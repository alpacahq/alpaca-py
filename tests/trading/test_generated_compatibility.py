import ast
import re
import subprocess
import sys
import warnings
from datetime import datetime
from pathlib import Path

import pytest

import alpaca.trading
from alpaca._deprecating_enum import DeprecatingEnumMeta
from alpaca.common._deprecation import (
    build_from_response,
    compatibility_shape_message,
)
from alpaca.trading import enums, models, requests
from alpaca.trading._generated import enums as generated_enums
from alpaca.trading._generated import models as generated_models
from alpaca.trading._generated import requests as generated_requests

# Same-name generated types that intentionally keep the handwritten public binding.
# Generated implementations stay available from alpaca.trading._generated.*.
SAME_NAME_LEGACY = {
    "enums": {
        "AccountStatus",  # generated omits legacy Broker onboarding values
        "ActivityType",  # public keeps deprecated CIL/DIVWH/... members and helpers
        "OrderSide",  # generated lists only buy and sell; public enum keeps older FIX sides
        "OrderStatus",  # public keeps deprecated PENDING_REVIEW member
    },
    "models": {
        "Clock",  # generated Clock is the v3 multi-market shape
        "OptionContract",  # generated changes enum and numeric field types
        "OptionDeliverable",  # generated amount is required; delayed settlement omits it
        "OptionContractsResponse",  # wraps the legacy OptionContract shape
        "Order",  # generated changes requiredness, numeric types, and legs
        "PortfolioHistory",  # generated changes cashflow and numeric types
        "Position",  # generated changes enums and field requiredness
        "USDPositionValues",  # generated changes strings to strict strings
        "Watchlist",  # generated changes the nested Asset type
    },
    "requests": {
        "CreateWatchlistRequest",  # generated symbols field is optional
        "UpdateWatchlistRequest",  # generated lacks the non-empty validator
    },
}

# Members an enum shape keeps although its generated twin lacks them, so they are not
# deprecated.
KEPT_MEMBERS_MISSING_FROM_TWIN = {
    "OrderSide": {
        "BUY_MINUS",
        "CROSS",
        "CROSS_SHORT",
        "SELL_PLUS",
        "SELL_SHORT",
        "SELL_SHORT_EXEMPT",
        "UNDISCLOSED",
    },
}

# Same-name enum shapes that are not deprecated: they are not going to switch to the
# generated twin.
NOT_SWITCHING = {
    "OrderSide",  # keeps FIX sides so responses that use them still parse
}

PACKAGE = alpaca.trading

# Same-name legacy types that already have a differently named public replacement.
RENAMED_COMPATIBILITY = {
    "Clock",  # use LegacyClock instead
}

PUBLIC_MODULES = {
    "enums": (enums, generated_enums),
    "models": (models, generated_models),
    "requests": (requests, generated_requests),
}


def _generated_class_names(generated_module) -> set[str]:
    tree = ast.parse(Path(generated_module.__file__).read_text())
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )
    return names


def _replacements_from_deprecated(message: str) -> list[str]:
    # "Please use `New` instead." (enums) or "use New instead." (models, requests).
    # A message may name more than one replacement, each in backticks.
    match = re.search(r"\buse (.+?) instead", message)
    if not match:
        return []
    return re.findall(r"`(\w+)`", match.group(1)) or [match.group(1)]


@pytest.mark.parametrize(
    ("module_name", "public_module", "generated_module"),
    [(name, public, generated) for name, (public, generated) in PUBLIC_MODULES.items()],
)
def test_every_generated_type_is_available_from_its_public_module(
    module_name, public_module, generated_module
):
    generated_names = _generated_class_names(generated_module)
    assert generated_names <= set(vars(public_module))

    mismatches = {
        name
        for name in generated_names
        if getattr(public_module, name) is not getattr(generated_module, name)
    }
    assert mismatches == SAME_NAME_LEGACY[module_name]


@pytest.mark.parametrize(
    ("public_module", "generated_module", "canonical_name"),
    [
        (enums, generated_enums, "OptionContractType"),
        (models, generated_models, "Account"),
        (models, generated_models, "Assets"),
        (models, generated_models, "CalendarDay"),
        (models, generated_models, "LegacyClock"),
        (models, generated_models, "PositionClosedResponse"),
        (requests, generated_requests, "PatchOrderRequest"),
        (requests, generated_requests, "CreateOrderRequest"),
        (requests, generated_requests, "PostOrderRequest"),
    ],
)
def test_canonical_public_types_are_generated(
    public_module, generated_module, canonical_name
):
    generated_name = {
        "PostOrderRequest": "CreateOrderRequest",
    }.get(canonical_name, canonical_name)

    assert getattr(public_module, canonical_name) is getattr(
        generated_module, generated_name
    )


@pytest.mark.parametrize(
    ("module_name", "public_module"),
    [(name, public) for name, (public, _) in PUBLIC_MODULES.items()],
)
def test_same_name_legacy_types_are_deprecated(module_name, public_module):
    for name in SAME_NAME_LEGACY[module_name]:
        if name in RENAMED_COMPATIBILITY:
            continue
        obj = getattr(public_module, name)
        if name in NOT_SWITCHING:
            assert "__deprecated__" not in vars(obj), f"{name} should not be deprecated"
            continue
        assert hasattr(obj, "__deprecated__"), f"{name} should be deprecated"
        # Enum shapes add a sentence naming what their twin lacks.
        assert obj.__deprecated__.startswith(compatibility_shape_message(name)), name


def test_same_name_legacy_enums_deprecate_only_the_members_their_twin_lacks():
    for name in SAME_NAME_LEGACY["enums"]:
        shape = getattr(enums, name)
        twin = getattr(generated_enums, name)
        # The enum's own deprecation is static only, so looking up a member the twin
        # also has stays silent at runtime.
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            shape(next(iter(twin)).value)
        missing_from_twin = set(shape.__members__) - set(twin.__members__)
        deprecated_members = set(DeprecatingEnumMeta._deprecations.get(shape, {}))
        assert (
            missing_from_twin - KEPT_MEMBERS_MISSING_FROM_TWIN.get(name, set())
            == deprecated_members
        ), name


def test_package_does_not_reexport_deprecation_helpers():
    for helper in (
        "deprecated",
        "compatibility_shape_message",
        "deprecate_compatibility_shape",
        "warn_on_direct_instantiation",
        "build_from_response",
    ):
        assert not hasattr(PACKAGE, helper), helper


@pytest.mark.parametrize(
    ("public_module",),
    [(enums,), (models,), (requests,)],
)
def test_deprecated_public_types_point_at_existing_replacements(public_module):
    deprecated_types = [
        (name, obj)
        for name, obj in vars(public_module).items()
        if isinstance(obj, type)
        and hasattr(obj, "__deprecated__")
        and obj.__module__ == public_module.__name__
    ]
    assert deprecated_types

    module_legacy = next(
        SAME_NAME_LEGACY[name]
        for name, (public, _) in PUBLIC_MODULES.items()
        if public is public_module
    )

    for name, obj in deprecated_types:
        message = obj.__deprecated__
        if name in module_legacy and name not in RENAMED_COMPATIBILITY:
            assert message.startswith(compatibility_shape_message(name)), name
            continue
        replacements = _replacements_from_deprecated(message)
        assert replacements, f"{name} has no 'use <Replacement> instead' message"
        for replacement in replacements:
            assert hasattr(
                public_module, replacement
            ), f"{name} points at missing replacement {replacement}"


def test_deprecated_model_warns_when_instantiated():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        models.Calendar(date="2025-01-02", open="09:30", close="16:00")

    assert any(
        warning.category is DeprecationWarning and "CalendarDay" in str(warning.message)
        for warning in caught
    )


def test_compatibility_shape_warns_when_instantiated():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        models.OptionContract(
            id="id",
            symbol="AAPL250620C00100000",
            name="AAPL call",
            status=enums.AssetStatus.ACTIVE,
            tradable=True,
            expiration_date="2025-06-20",
            root_symbol="AAPL",
            underlying_symbol="AAPL",
            underlying_asset_id="b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
            type=enums.ContractType.CALL,
            style=enums.ExerciseStyle.AMERICAN,
            strike_price=100.0,
            size="100",
        )

    assert any(
        warning.category is DeprecationWarning
        and "OpenAPI-generated OptionContract" in str(warning.message)
        for warning in caught
    )


def test_option_deliverable_warns_only_when_instantiated_directly():
    deliverable = {
        "type": "equity",
        "symbol": "AAPL",
        "allocation_percentage": "100",
        "settlement_type": "T+1",
        "settlement_method": "CCC",
        "delayed_settlement": False,
    }
    with pytest.warns(DeprecationWarning, match="OpenAPI-generated OptionDeliverable"):
        models.OptionDeliverable(**deliverable)

    # Parsed as part of a contract the client builds, it stays silent.
    contract = {
        "id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
        "symbol": "AAPL250620C00100000",
        "name": "AAPL call",
        "status": "active",
        "tradable": True,
        "expiration_date": "2025-06-20",
        "root_symbol": "AAPL",
        "underlying_symbol": "AAPL",
        "underlying_asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
        "type": "call",
        "style": "american",
        "strike_price": "100",
        "size": "100",
        "deliverables": [deliverable],
    }
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        built = build_from_response(models.OptionContract, contract)
    assert type(built.deliverables[0]) is models.OptionDeliverable


def test_deprecated_enum_warns_when_constructed():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        enums.ContractType("call")
        enums.AssetStatus("active")

    messages = [
        str(warning.message)
        for warning in caught
        if warning.category is DeprecationWarning
    ]
    assert any("OptionContractType" in message for message in messages)
    assert any("AssetsStatus" in message for message in messages)


def test_deprecated_enum_warning_points_at_the_caller():
    # Python's default filters only show a DeprecationWarning attributed to
    # __main__, so it must not be attributed to enum.py.
    with pytest.warns(DeprecationWarning, match="AssetsStatus") as caught:
        enums.AssetStatus("active")
    assert [warning.filename for warning in caught] == [__file__]


def test_requests_accept_the_replacement_enums():
    assets = requests.GetAssetsRequest(
        status=enums.AssetsStatus.ACTIVE, exchange=enums.Exchange.NYSE
    )
    assert type(assets.status) is enums.AssetsStatus
    assert assets.to_request_fields() == {"status": "active", "exchange": "NYSE"}

    # Strings and legacy members keep parsing into the legacy enum.
    assert type(requests.GetAssetsRequest(status="active").status) is enums.AssetStatus
    assert (
        type(requests.GetAssetsRequest(status=enums.AssetStatus.ACTIVE).status)
        is enums.AssetStatus
    )

    orders = requests.GetOrdersRequest(status=enums.GetAllOrdersStatusParameter.OPEN)
    assert orders.to_request_fields()["status"] == "open"

    contracts = requests.GetOptionContractsRequest(
        type=enums.OptionContractType.CALL, style=enums.OptionContractStyle.AMERICAN
    )
    assert contracts.to_request_fields()["type"] == "call"
    assert contracts.to_request_fields()["style"] == "american"


@pytest.mark.parametrize(
    ("model", "data"),
    [
        (
            models.Asset,
            {
                "id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
                "class": "us_index",
                "symbol": "SPX",
                "name": "S&P 500",
                "status": "active",
                "tradable": False,
                "marginable": False,
                "shortable": False,
                "easy_to_borrow": False,
                "fractionable": False,
            },
        ),
        (
            models.Position,
            {
                "asset_id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
                "symbol": "SPX",
                "asset_class": "us_equity",
                "avg_entry_price": "1",
                "qty": "1",
                "side": "long",
                "cost_basis": "1",
            },
        ),
    ],
)
def test_asset_exchange_falls_back_to_the_generated_exchange(model, data):
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        index = build_from_response(model, {**data, "exchange": "INDEX"})
        crxl = build_from_response(model, {**data, "exchange": "CRXL"})
        nyse = build_from_response(model, {**data, "exchange": "NYSE"})

    assert index.exchange is enums.Exchange.INDEX
    assert crxl.exchange is enums.Exchange.CRXL
    # Exchanges the legacy enum has keep parsing into it.
    assert nyse.exchange is enums.AssetExchange.NYSE


def test_deprecated_compatibility_types_do_not_warn_during_import():
    subprocess.run(
        [
            sys.executable,
            "-W",
            "error::DeprecationWarning:alpaca",
            "-c",
            "import alpaca.trading.requests; import alpaca.broker.models",
        ],
        check=True,
    )


def test_clients_build_compatibility_shapes_without_warning():
    data = {"date": "2022-05-16", "open": "09:30", "close": "16:00"}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        built = build_from_response(models.Calendar, data)

    assert not [w for w in caught if w.category is DeprecationWarning]
    # The shape's own __init__ still runs (Calendar combines date and time).
    assert built.open == datetime(2022, 5, 16, 9, 30)

    with pytest.warns(DeprecationWarning, match="Calendar is deprecated"):
        models.Calendar(**data)
