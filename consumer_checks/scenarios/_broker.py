"""Shared by the broker scenarios. Part of every using scenario's hash.

Safety rules for the Broker sandbox these scenarios share:

* Every account is created here, with a synthetic identity, and closed before
  the scenario returns. Sandbox accounts can be closed, not deleted.
* Nothing lists or journals another account. List calls are filtered to an
  email this scenario just created, or the path contains an id it created.
* ``get_all_accounts_positions`` is not called here. It returns every account
  and is covered by a stubbed scenario instead.
"""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from decimal import ROUND_DOWN, Decimal
from typing import Any, Callable, Iterator, Optional, Tuple
from uuid import UUID

from alpaca.broker.enums import (
    AgreementType,
    BankAccountType,
    FundingSource,
    TaxIdType,
    TransferDirection,
)
from alpaca.broker.models import (
    Account,
    ACHRelationship,
    Agreement,
    Contact,
    Disclosures,
    Identity,
    Transfer,
)
from alpaca.broker.models import TradeAccount as BrokerTradeAccount
from alpaca.broker.requests import (
    CreateAccountRequest,
    CreateACHRelationshipRequest,
    CreateACHTransferRequest,
)
from alpaca.common.exceptions import APIError
from alpaca.trading.enums import AccountStatus
from alpaca.trading.models import TradeAccount

from . import Context

# 1x1 PNG. Document uploads need a real base64 body; this is not a person's id.
TINY_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
UNFILLABLE_LIMIT_PRICE = 1.00
READY = (AccountStatus.ACTIVE, AccountStatus.APPROVED)


def tax_id(unique: str) -> str:
    """A synthetic SSN. 666 is not an issued area number."""
    digits = "".join(str(int(char, 16) % 10) for char in unique[:9].ljust(9, "0"))
    return f"666-{digits[:2]}-{digits[2:6]}"


def create_account_request(ctx: Context, label: str) -> CreateAccountRequest:
    unique = ctx.unique_id(label)
    return CreateAccountRequest(
        contact=Contact(
            email_address=f"consumer-check-{unique[:12]}@example.com",
            phone_number="+15555550100",
            street_address=["1 Consumer Check Way"],
            city="Example City",
            state="CA",
            postal_code="94000",
            country="USA",
        ),
        identity=Identity(
            given_name="Consumer",
            family_name="Check",
            date_of_birth="1990-01-01",
            tax_id=tax_id(unique),
            tax_id_type=TaxIdType.USA_SSN,
            country_of_citizenship="USA",
            country_of_birth="USA",
            country_of_tax_residence="USA",
            funding_source=[FundingSource.EMPLOYMENT_INCOME],
        ),
        disclosures=Disclosures(
            is_control_person=False,
            is_affiliated_exchange_or_finra=False,
            is_politically_exposed=False,
            immediate_family_exposed=False,
        ),
        agreements=[
            Agreement(
                agreement=AgreementType.CUSTOMER_AGREEMENT,
                signed_at="2024-01-01T00:00:00Z",
                ip_address="192.0.2.1",
            ),
            Agreement(
                agreement=AgreementType.ACCOUNT_AGREEMENT,
                signed_at="2024-01-01T00:00:00Z",
                ip_address="192.0.2.1",
            ),
        ],
    )


class AccountSession:
    """An account this scenario created. Closed on the way out."""

    def __init__(self, ctx: Context, label: str) -> None:
        self.ctx = ctx
        self.request = create_account_request(ctx, label)
        # The address we sent. Response contact fields are scrubbed, so later
        # requests must use this and not the value the API echoed.
        self.email = self.request.contact.email_address
        created = ctx.broker.create_account(self.request)
        assert isinstance(created, Account)
        self.account = created
        self.closed = False

    def close(self) -> None:
        if self.closed:
            return
        self.ctx.broker.close_account(self.account.id)
        self.closed = True

    def wait_until_ready(self, attempts: int = 12) -> Account:
        last = self.account
        for _ in range(attempts):
            fetched = self.ctx.broker.get_account_by_id(self.account.id)
            assert isinstance(fetched, Account)
            last = fetched
            if fetched.status in READY:
                self.account = fetched
                return fetched
            self.ctx.sleep(1)
        raise AssertionError(f"account stayed {last.status}")

    def __enter__(self) -> "AccountSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.closed:
            return
        if exc_type is not None:
            _close_quietly(self.ctx, self.account.id)
            self.closed = True
            return
        self.close()


@contextmanager
def opened_account(ctx: Context, label: str = "account") -> Iterator[AccountSession]:
    session = AccountSession(ctx, label)
    with session:
        yield session


def expect_client_error(call: Callable[[], Any]) -> APIError:
    try:
        call()
    except APIError as error:
        assert isinstance(error.status_code, int)
        assert 400 <= error.status_code < 500
        return error
    raise AssertionError("expected APIError")


def fund_with_ach(
    ctx: Context, account_id: UUID, amount: str = "1000"
) -> Tuple[ACHRelationship, Transfer]:
    """Incoming sandbox ACH. The caller deletes the relationship."""
    relationship = ctx.broker.create_ach_relationship_for_account(
        account_id,
        CreateACHRelationshipRequest(
            account_owner_name="Consumer Check",
            bank_account_type=BankAccountType.CHECKING,
            bank_account_number="123456789",
            bank_routing_number="121000248",
            nickname="consumer-check",
        ),
    )
    assert isinstance(relationship, ACHRelationship)
    transfer = ctx.broker.create_transfer_for_account(
        account_id,
        CreateACHTransferRequest(
            amount=amount,
            direction=TransferDirection.INCOMING,
            relationship_id=relationship.id,
        ),
    )
    assert isinstance(transfer, Transfer)
    return relationship, transfer


def wait_for_buying_power(
    ctx: Context, account_id: UUID, minimum: str = "1", attempts: int = 20
) -> TradeAccount:
    last: Optional[TradeAccount] = None
    needed = Decimal(minimum)
    for _ in range(attempts):
        account = ctx.broker.get_trade_account_by_id(account_id)
        assert isinstance(account, TradeAccount)
        last = account
        buying_power = Decimal(account.buying_power or "0")
        if buying_power >= needed:
            return account
        ctx.sleep(1)
    cash = getattr(last, "cash", None)
    raise AssertionError(f"account was not funded: cash={cash}")


def _whole_cents(value: Optional[str]) -> Decimal:
    """A cash string rounded down to cents, so a request never overdraws."""
    return Decimal(value or "0").quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def withdraw_remaining_cash(
    ctx: Context, account_id: UUID, relationship_id: UUID, attempts: int = 20
) -> Optional[Transfer]:
    """Send the account's cash back over ACH, so ``close_account`` is allowed.

    ``BrokerClient.close_account`` is refused while the account holds money.
    Call this before the ACH relationship is deleted. A deposit that is still
    pending is waited for first, and no transfer is made when there is no cash.
    """
    account: Optional[BrokerTradeAccount] = None
    for _ in range(attempts):
        fetched = ctx.broker.get_trade_account_by_id(account_id)
        assert isinstance(fetched, BrokerTradeAccount)
        account = fetched
        if _whole_cents(account.pending_transfer_in) <= 0:
            break
        ctx.sleep(1)
    assert account is not None
    amount = _whole_cents(account.cash_withdrawable)
    if amount <= 0:
        return None
    transfer = ctx.broker.create_transfer_for_account(
        account_id,
        CreateACHTransferRequest(
            amount=str(amount),
            direction=TransferDirection.OUTGOING,
            relationship_id=relationship_id,
        ),
    )
    assert isinstance(transfer, Transfer)
    return transfer


def withdraw_quietly(ctx: Context, account_id: UUID, relationship_id: UUID) -> None:
    """``withdraw_remaining_cash`` for ``finally`` blocks.

    It must not replace the error a failed scenario is already raising. If the
    cash stays, ``close_account`` fails next, so the problem is still reported.
    """
    try:
        withdraw_remaining_cash(ctx, account_id, relationship_id)
    except APIError as error:
        warnings.warn(
            f"could not withdraw cash from sandbox account {account_id}: "
            f"{error.status_code}. Withdraw it by hand before closing.",
            stacklevel=2,
        )


def _close_quietly(ctx: Context, account_id: UUID) -> None:
    """Best-effort cleanup after a failure, without hiding the original error.

    A failed step is reported as a warning, so an account left open in the
    sandbox shows up in the run log instead of piling up unnoticed.
    """
    for step, call in (
        ("cancel orders", ctx.broker.cancel_orders_for_account),
        ("close", ctx.broker.close_account),
    ):
        try:
            call(account_id)
        except APIError as error:
            warnings.warn(
                f"could not {step} for sandbox account {account_id}: "
                f"{error.status_code}. Close it by hand if it is still open.",
                stacklevel=2,
            )
