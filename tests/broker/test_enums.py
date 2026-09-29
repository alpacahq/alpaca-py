import re
import subprocess
import sys
import warnings

import pytest

from alpaca.broker.enums import (
    ACHRelationshipStatus,
    AccountType,
    AgreementType,
    BankAccountType,
    BankStatus,
    JournalStatus,
    TransferStatus,
)
from alpaca.trading.enums import (
    AccountStatus,
    ActivityType,
    AssetClass,
    AssetExchange,
    OrderClass,
    OrderSide,
    OrderStatus,
)


def test_activity_type_is_trade_activity():
    """This seems like an overly simple test right now but will probably be more useful in the future"""

    assert ActivityType.FILL.is_trade_activity()
    assert not ActivityType.ACATC.is_trade_activity()


def _deprecation_message(enum_name: str, member_name: str, kind: str) -> str:
    return (
        f"{enum_name}.{member_name} is deprecated and will be removed in the next release. "
        f"It is no longer a valid {kind}."
    )


@pytest.mark.parametrize(
    ("enum_cls", "member_name", "wire_value", "kind", "stable_member"),
    [
        (ActivityType, "CIL", "CIL", "activity type", "FILL"),
        (ActivityType, "DIVWH", "DIVWH", "activity type", "FILL"),
        (ActivityType, "EXTRD", "EXTRD", "activity type", "FILL"),
        (ActivityType, "FXTRD", "FXTRD", "activity type", "FILL"),
        (ActivityType, "INTPNL", "INTPNL", "activity type", "FILL"),
        (ActivityType, "MEM", "MEM", "activity type", "FILL"),
        (ActivityType, "SWP", "SWP", "activity type", "FILL"),
        (ActivityType, "VOF", "VOF", "activity type", "FILL"),
        (ActivityType, "WH", "WH", "activity type", "FILL"),
        (OrderStatus, "PENDING_REVIEW", "pending_review", "order status", "NEW"),
        (
            AgreementType,
            "CUSTODIAL_CUSTOMER",
            "custodial_customer_agreement",
            "agreement type",
            "ACCOUNT_AGREEMENT",
        ),
        (AccountStatus, "AML_REVIEW", "AML_REVIEW", "account status", "ACTIVE"),
        (AccountStatus, "DISABLED", "DISABLED", "account status", "ACTIVE"),
        (
            AccountStatus,
            "DISABLE_PENDING",
            "DISABLE_PENDING",
            "account status",
            "ACTIVE",
        ),
        (AccountStatus, "EDITED", "EDITED", "account status", "ACTIVE"),
        (
            AccountStatus,
            "KYC_SUBMITTED",
            "KYC_SUBMITTED",
            "account status",
            "ACTIVE",
        ),
        (
            AccountStatus,
            "REAPPROVAL_PENDING",
            "REAPPROVAL_PENDING",
            "account status",
            "ACTIVE",
        ),
        (AccountStatus, "RESUBMITTED", "RESUBMITTED", "account status", "ACTIVE"),
        (AccountStatus, "SIGNED_UP", "SIGNED_UP", "account status", "ACTIVE"),
        (TransferStatus, "SETTLED", "SETTLED", "transfer status", "QUEUED"),
        (BankAccountType, "NONE", "", "bank account type", "CHECKING"),
        (AssetExchange, "ASCX", "ASCX", "asset exchange", "NYSE"),
        (AssetExchange, "FTXU", "FTXU", "asset exchange", "NYSE"),
        (AssetExchange, "CBSE", "CBSE", "asset exchange", "NYSE"),
        (AssetExchange, "GNSS", "GNSS", "asset exchange", "NYSE"),
        (AssetExchange, "ERSX", "ERSX", "asset exchange", "NYSE"),
    ],
)
def test_deprecated_enum_member_warns_on_lookup(
    enum_cls, member_name, wire_value, kind, stable_member
):
    message = _deprecation_message(enum_cls.__name__, member_name, kind)
    match = f"^{re.escape(message)}$"

    with pytest.warns(DeprecationWarning, match=match) as caught:
        by_attribute = getattr(enum_cls, member_name)
    assert len(caught) == 1
    assert by_attribute == wire_value
    assert by_attribute.value == wire_value

    with pytest.warns(DeprecationWarning, match=match) as caught:
        by_name = enum_cls[member_name]
    assert len(caught) == 1
    assert by_name == wire_value
    assert by_name.value == wire_value

    with pytest.warns(DeprecationWarning, match=match) as caught:
        by_value = enum_cls(wire_value)
    assert len(caught) == 1
    assert by_value == wire_value
    assert by_value.value == wire_value

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        assert (
            getattr(enum_cls, stable_member) == getattr(enum_cls, stable_member).value
        )
        assert member_name in enum_cls.__members__
        assert list(enum_cls)


@pytest.mark.parametrize(
    ("enum_cls", "member_name", "wire_value"),
    [
        (ActivityType, "TRANS", "TRANS"),
        (ActivityType, "MISC", "MISC"),
        (ActivityType, "CGD", "CGD"),
        (ActivityType, "DIVFEE", "DIVFEE"),
        (ActivityType, "DIVFT", "DIVFT"),
        (ActivityType, "DIVTW", "DIVTW"),
        (ActivityType, "INTNRA", "INTNRA"),
        (ActivityType, "INTTW", "INTTW"),
        (ActivityType, "JNL", "JNL"),
        (ActivityType, "OPCA", "OPCA"),
        (ActivityType, "PTR", "PTR"),
        (ActivityType, "REO", "REO"),
        (ActivityType, "FOPT", "FOPT"),
        (AccountType, "TRUST", "trust"),
        (AccountType, "OMNIBUS_NON_DISCLOSED", "omnibus_non_disclosed"),
        (AccountType, "OMNIBUS_SUB", "omnibus_sub"),
        (AccountType, "JOINT", "joint"),
        (AssetClass, "TREASURY", "treasury"),
        (AssetClass, "CORPORATE", "corporate"),
        (AssetClass, "GLOBAL_EQUITY", "global_equity"),
        (AssetClass, "US_INDEX", "us_index"),
        (AssetClass, "US_EQUITY_CHAIN", "us_equity_chain"),
        (AssetClass, "IPO", "ipo"),
        (AccountStatus, "ACCOUNT_CLOSED_PENDING", "ACCOUNT_CLOSED_PENDING"),
        (JournalStatus, "ACTIVITY_CREATED", "activity_created"),
        (OrderClass, "EMPTY", ""),
        (OrderSide, "BUY_MINUS", "buy_minus"),
        (OrderSide, "SELL_PLUS", "sell_plus"),
        (OrderSide, "SELL_SHORT", "sell_short"),
        (OrderSide, "SELL_SHORT_EXEMPT", "sell_short_exempt"),
        (OrderSide, "UNDISCLOSED", "undisclosed"),
        (OrderSide, "CROSS", "cross"),
        (OrderSide, "CROSS_SHORT", "cross_short"),
        (ACHRelationshipStatus, "REJECTED", "REJECTED"),
        (ACHRelationshipStatus, "CANCEL_REQUESTED", "CANCEL_REQUESTED"),
        (BankStatus, "REJECTED", "REJECTED"),
    ],
)
def test_openapi_enum_value_is_accepted(enum_cls, member_name, wire_value):
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        member = getattr(enum_cls, member_name)
        assert member == wire_value
        assert member.value == wire_value
        assert enum_cls(wire_value) is member


def _agreement_rename_message(old_name: str, new_name: str) -> str:
    return (
        f"AgreementType.{old_name} is deprecated and will be removed in the next release. "
        f"Use AgreementType.{new_name}."
    )


@pytest.mark.parametrize(
    ("old_name", "new_name", "wire_value"),
    [
        ("MARGIN", "MARGIN_AGREEMENT", "margin_agreement"),
        ("ACCOUNT", "ACCOUNT_AGREEMENT", "account_agreement"),
        ("CUSTOMER", "CUSTOMER_AGREEMENT", "customer_agreement"),
        ("CRYPTO", "CRYPTO_AGREEMENT", "crypto_agreement"),
        ("OPTIONS", "OPTIONS_AGREEMENT", "options_agreement"),
    ],
)
def test_deprecated_agreement_type_name_warns(old_name, new_name, wire_value):
    message = _agreement_rename_message(old_name, new_name)
    match = f"^{re.escape(message)}$"

    with pytest.warns(DeprecationWarning, match=match) as caught:
        by_attribute = getattr(AgreementType, old_name)
    assert len(caught) == 1
    assert by_attribute == wire_value
    assert by_attribute.value == wire_value
    assert by_attribute.name == new_name

    with pytest.warns(DeprecationWarning, match=match) as caught:
        by_name = AgreementType[old_name]
    assert len(caught) == 1
    assert by_name == wire_value
    assert by_name.name == new_name

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        by_value = AgreementType(wire_value)
        canonical = getattr(AgreementType, new_name)
        assert by_value == wire_value
        assert by_value.value == wire_value
        assert canonical == wire_value
        assert by_attribute is canonical
        assert by_name is canonical
        assert by_value is canonical


def test_model_validation_warns_for_removed_enum_value():
    from alpaca.trading.models import NonTradeActivity

    raw = {
        "id": "20260525000000000::c524b737-b67b-416a-b451-321e42d3a609",
        "account_id": "c524b737-b67b-416a-b451-321e42d3a609",
        "activity_type": "WH",
        "date": "2026-05-25",
        "net_amount": "0.18",
        "description": "",
        "symbol": "AIA",
        "status": "executed",
    }
    message = _deprecation_message("ActivityType", "WH", "activity type")

    with pytest.warns(DeprecationWarning, match=f"^{re.escape(message)}$") as caught:
        activity = NonTradeActivity.model_validate(raw)

    assert len(caught) == 1
    assert caught[0].filename == __file__
    assert activity.activity_type.name == "WH"
    assert activity.activity_type == "WH"


def test_model_validation_accepts_added_and_renamed_wire_values_quietly():
    from pydantic import TypeAdapter

    from alpaca.trading.models import NonTradeActivity

    raw = {
        "id": "20260525000000000::c524b737-b67b-416a-b451-321e42d3a609",
        "account_id": "c524b737-b67b-416a-b451-321e42d3a609",
        "activity_type": "CGD",
        "date": "2026-05-25",
        "net_amount": "0.18",
        "description": "",
        "symbol": "AIA",
        "status": "executed",
    }

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        activity = NonTradeActivity.model_validate(raw)
        agreement = TypeAdapter(AgreementType).validate_python("margin_agreement")
        bank_account_type = TypeAdapter(BankAccountType).validate_python("CHECKING")
        status_schema = TypeAdapter(OrderStatus).json_schema()

    assert activity.activity_type is ActivityType.CGD
    assert agreement is AgreementType.MARGIN_AGREEMENT
    assert bank_account_type is BankAccountType.CHECKING
    assert "pending_review" in status_schema["enum"]
    assert "new" in status_schema["enum"]


def test_deprecating_enum_meta_is_not_a_public_enum_attribute():
    import alpaca.broker.enums as broker_enums
    import alpaca.trading.enums as trading_enums

    assert not hasattr(broker_enums, "DeprecatingEnumMeta")
    assert not hasattr(trading_enums, "DeprecatingEnumMeta")


def test_importing_enum_modules_does_not_warn():
    completed = subprocess.run(
        [
            sys.executable,
            "-W",
            "always",
            "-c",
            "import alpaca.trading.enums, alpaca.broker.enums",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    combined = completed.stderr + completed.stdout
    assert "will be removed in the next release" not in combined
