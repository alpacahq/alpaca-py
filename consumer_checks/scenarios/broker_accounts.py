"""One sandbox account: read it, change it, and close it.

``delete_account`` is the deprecated name for close. It gets its own account so
the supported ``close_account`` path stays on the lifecycle scenario.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Callable, Dict
from uuid import UUID

from requests import HTTPError

from alpaca.broker.enums import (
    AccountEntities,
    DocumentType,
    TradeDocumentType,
    UploadDocumentMimeType,
    UploadDocumentSubType,
)
from alpaca.broker.models import Account
from alpaca.broker.requests import (
    GetAccountActivitiesRequest,
    GetTradeDocumentsRequest,
    ListAccountsRequest,
    UpdateAccountRequest,
    UpdatableContact,
    UploadDocumentRequest,
)
from alpaca.common.enums import PaginationType, Sort
from alpaca.common.exceptions import APIError
from alpaca.trading.enums import AccountStatus, TradeConfirmationEmail
from alpaca.trading.models import AccountConfiguration, TradeAccount

from . import Context, scenario
from ._broker import TINY_PNG, expect_client_error, opened_account

BROKER = "broker"
CLOSED = (AccountStatus.ACCOUNT_CLOSED, AccountStatus.ACCOUNT_CLOSED_PENDING)
MISSING_DOCUMENT = UUID("11111111-1111-1111-1111-111111111111")


def _missing_download(call: Callable[[], Any]) -> Dict[str, Any]:
    """What downloading a document that does not exist raises.

    ``download_trade_document_for_account_by_id`` raises ``APIError`` when the
    body has a ``code``, and the raw ``requests.HTTPError`` otherwise. Callers
    have to handle both, so the recording keeps which one came back.
    """
    try:
        call()
    except APIError as error:
        status = error.status_code
        error_type = type(error).__name__
    except HTTPError as error:
        assert error.response is not None
        status = error.response.status_code
        error_type = type(error).__name__
    else:
        raise AssertionError("a missing document should raise")
    assert isinstance(status, int) and 400 <= status < 500
    return {"error_type": error_type, "status_code": status}


@scenario(
    covers=[
        "BrokerClient.create_account",
        "BrokerClient.get_account_by_id",
        "BrokerClient.list_accounts",
        "BrokerClient.update_account",
        "BrokerClient.get_trade_account_by_id",
        "BrokerClient.get_trade_configuration_for_account",
        "BrokerClient.update_trade_configuration_for_account",
        "BrokerClient.upload_documents_to_account",
        "BrokerClient.get_trade_documents_for_account",
        "BrokerClient.get_trade_document_for_account_by_id",
        "BrokerClient.download_trade_document_for_account_by_id",
        "BrokerClient.get_account_activities",
        "BrokerClient.get_cip_data_for_account_by_id",
        "BrokerClient.upload_cip_data_for_account_by_id",
        "BrokerClient.close_account",
    ],
    credentials=BROKER,
)
def account_lifecycle(ctx: Context) -> Dict[str, Any]:
    with opened_account(ctx) as session:
        created = session.account
        assert created.currency == "USD"
        session.wait_until_ready()

        fetched = ctx.broker.get_account_by_id(created.id)
        assert isinstance(fetched, Account)
        assert fetched.id == created.id

        # Filtered to the email we just created. An unfiltered list would record
        # every other account on the sandbox.
        listed = ctx.broker.list_accounts(
            ListAccountsRequest(
                query=session.email,
                sort=Sort.DESC,
                entities=[AccountEntities.CONTACT, AccountEntities.IDENTITY],
                created_after=datetime(2020, 1, 1, tzinfo=timezone.utc),
            )
        )
        assert isinstance(listed, list)
        # Every row must be ours: if the API ever ignored the filter, the
        # recording would hold every other account on the sandbox.
        assert listed and all(account.id == created.id for account in listed)
        ours = listed

        updated = ctx.broker.update_account(
            created.id,
            UpdateAccountRequest(contact=UpdatableContact(city="Example Town")),
        )
        assert isinstance(updated, Account)
        assert updated.id == created.id
        assert updated.contact is not None
        assert updated.contact.city == "Example Town"
        updated_city = updated.contact.city

        trade_account = ctx.broker.get_trade_account_by_id(created.id)
        assert isinstance(trade_account, TradeAccount)
        assert trade_account.id == created.id

        config = ctx.broker.get_trade_configuration_for_account(created.id)
        assert isinstance(config, AccountConfiguration)
        original = config.trade_confirm_email
        target = (
            TradeConfirmationEmail.NONE
            if original == TradeConfirmationEmail.ALL
            else TradeConfirmationEmail.ALL
        )
        config.trade_confirm_email = target
        try:
            changed = ctx.broker.update_trade_configuration_for_account(
                created.id, config
            )
            assert isinstance(changed, AccountConfiguration)
            assert changed.trade_confirm_email == target
        finally:
            config.trade_confirm_email = original
            restored = ctx.broker.update_trade_configuration_for_account(
                created.id, config
            )
            assert isinstance(restored, AccountConfiguration)
        assert restored.trade_confirm_email == original

        ctx.broker.upload_documents_to_account(
            created.id,
            [
                UploadDocumentRequest(
                    document_type=DocumentType.IDENTITY_VERIFICATION,
                    document_sub_type=UploadDocumentSubType.PASSPORT,
                    content=TINY_PNG,
                    mime_type=UploadDocumentMimeType.PNG,
                )
            ],
        )

        documents = ctx.broker.get_trade_documents_for_account(
            created.id,
            GetTradeDocumentsRequest(
                start=date(2020, 1, 1),
                end=date(2020, 1, 31),
                type=TradeDocumentType.ACCOUNT_STATEMENT,
            ),
        )
        assert isinstance(documents, list)
        missing_document = expect_client_error(
            lambda: ctx.broker.get_trade_document_for_account_by_id(
                created.id, MISSING_DOCUMENT
            )
        )
        missing_download = _missing_download(
            lambda: ctx.broker.download_trade_document_for_account_by_id(
                created.id,
                MISSING_DOCUMENT,
                "/tmp/consumer-check-not-a-document.pdf",
            )
        )

        activities = ctx.broker.get_account_activities(
            GetAccountActivitiesRequest(
                account_id=created.id,
                page_size=1,
                direction=Sort.DESC,
            ),
            max_items_limit=1,
            handle_pagination=PaginationType.FULL,
        )
        assert isinstance(activities, list)
        # GET /accounts/activities is correspondent-wide, filtered by a query
        # parameter, and account_id is scrubbed in recordings. The account is
        # not funded yet, so any row would belong to another account.
        assert activities == []

        # Both CIP methods are still unimplemented and return without a request.
        # A later implementation that starts calling the API fails this recording.
        ctx.broker.get_cip_data_for_account_by_id(created.id)
        ctx.broker.upload_cip_data_for_account_by_id(created.id)

    assert session.closed
    return {
        "created_status": created.status,
        "listed": ours[0],
        "updated_city": updated_city,
        "trade_account": trade_account,
        "config": restored,
        "documents_are_a_list": isinstance(documents, list),
        "missing_document": missing_document,
        "missing_download": missing_download,
        "activity_count": len(activities),
    }


@scenario(covers=["BrokerClient.delete_account"], credentials=BROKER)
def close_via_delete_account(ctx: Context) -> Dict[str, Any]:
    # delete_account is deprecated and calls close_account. Users still import it.
    with opened_account(ctx, "delete") as session:
        # Ready first: a new account is not ACTIVE yet, so checking the status
        # afterwards would pass even if delete_account did nothing.
        session.wait_until_ready()
        ctx.broker.delete_account(session.account.id)
        session.closed = True
        status = None
        for _ in range(5):
            closed = ctx.broker.get_account_by_id(session.account.id)
            assert isinstance(closed, Account)
            status = closed.status
            if status in CLOSED:
                break
            ctx.sleep(1)
        assert status in CLOSED
    return {"status": status}
