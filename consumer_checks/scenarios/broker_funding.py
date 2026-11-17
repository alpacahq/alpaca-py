"""ACH, a recipient bank, and one incoming transfer, on an account we close.

The transfer is canceled when the sandbox still allows it. Sandbox deposits
often settle immediately, and then cancel fails: both outcomes are a finished
call, and the recorded one is what replay repeats.
"""

from __future__ import annotations

from typing import Any, Dict

from alpaca.broker.enums import (
    BankAccountType,
    IdentifierType,
    RecipientBankStatus,
    TransferDirection,
)
from alpaca.broker.models import ACHRelationship, Bank, Transfer
from alpaca.broker.requests import CreateBankRequest, GetTransfersRequest
from alpaca.common.enums import PaginationType
from alpaca.common.exceptions import APIError

from . import Context, scenario
from ._broker import fund_with_ach, opened_account, withdraw_remaining_cash

BROKER = "broker"


@scenario(
    covers=[
        "BrokerClient.create_ach_relationship_for_account",
        "BrokerClient.get_ach_relationships_for_account",
        "BrokerClient.delete_ach_relationship_for_account",
        "BrokerClient.create_bank_for_account",
        "BrokerClient.get_banks_for_account",
        "BrokerClient.delete_bank_for_account",
        "BrokerClient.create_transfer_for_account",
        "BrokerClient.get_transfers_for_account",
        "BrokerClient.cancel_transfer_for_account",
    ],
    credentials=BROKER,
)
def ach_bank_and_transfer(ctx: Context) -> Dict[str, Any]:
    with opened_account(ctx, "funding") as session:
        session.wait_until_ready()
        account_id = session.account.id
        relationship, transfer = fund_with_ach(ctx, account_id, amount="25")
        assert isinstance(relationship, ACHRelationship)
        assert isinstance(transfer, Transfer)
        assert relationship.nickname == "consumer-check"

        listed = ctx.broker.get_ach_relationships_for_account(
            account_id, statuses=[relationship.status]
        )
        assert isinstance(listed, list)
        assert any(item.id == relationship.id for item in listed)

        page = ctx.broker.get_transfers_for_account(
            account_id,
            GetTransfersRequest(
                direction=TransferDirection.INCOMING, limit=10, offset=0
            ),
            handle_pagination=PaginationType.NONE,
        )
        assert isinstance(page, list)
        assert any(
            isinstance(item, Transfer) and item.id == transfer.id for item in page
        )
        capped = ctx.broker.get_transfers_for_account(
            account_id,
            GetTransfersRequest(direction=TransferDirection.INCOMING, limit=10),
            max_items_limit=10,
            handle_pagination=PaginationType.FULL,
        )
        assert isinstance(capped, list)

        try:
            ctx.broker.cancel_transfer_for_account(account_id, transfer.id)
            cancel_status = None
        except APIError as error:
            assert isinstance(error.status_code, int)
            assert 400 <= error.status_code < 500
            cancel_status = error.status_code

        bank = ctx.broker.create_bank_for_account(
            account_id,
            CreateBankRequest(
                name="Consumer Check Bank",
                bank_code_type=IdentifierType.ABA,
                bank_code="026009593",
                account_number="123456789",
            ),
        )
        assert isinstance(bank, Bank)
        banks = ctx.broker.get_banks_for_account(
            account_id,
            status=RecipientBankStatus.ACTIVE,
            bank_name="Consumer Check Bank",
        )
        assert isinstance(banks, list)
        assert any(item.id == bank.id for item in banks)
        ctx.broker.delete_bank_for_account(account_id, bank.id)

        # A deposit that settled (cancel refused) is still cash, and
        # close_account is refused while the account holds any.
        withdraw_remaining_cash(ctx, account_id, relationship.id)
        ctx.broker.delete_ach_relationship_for_account(account_id, relationship.id)
        # BankAccountType is part of the ACH request built in fund_with_ach.
        assert relationship.bank_account_type == BankAccountType.CHECKING

    return {
        "relationship_status": relationship.status,
        "transfer_status": transfer.status,
        "cancel_status": cancel_status,
        "bank_status": bank.status,
    }
