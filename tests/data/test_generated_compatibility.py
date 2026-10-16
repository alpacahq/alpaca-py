import ast
import re
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

import alpaca.data
from alpaca._deprecating_enum import DeprecatingEnumMeta
from alpaca.common._deprecation import compatibility_shape_message
from alpaca.data import enums, models, requests
from alpaca.data._generated import enums as generated_enums
from alpaca.data._generated import models as generated_models
from alpaca.data._generated import requests as generated_requests
from alpaca.data.timeframe import TimeFrame

# Same-name generated types that intentionally keep the handwritten public binding.
# Generated implementations stay available from alpaca.data._generated.*.
SAME_NAME_LEGACY = {
    "enums": set(),
    "models": {
        "CashDividend",  # public adds corporate_action_type and omits currency/isin
        "CashMerger",
        "ForwardSplit",
        "Mover",  # public uses float fields; generated uses strict numeric unions
        "NameChange",
        "News",  # public keeps custom raw_data __init__ and optional images
        "Redemption",
        "ReverseSplit",
        "RightsDistribution",
        "SpinOff",
        "StockAndCashMerger",
        "StockDividend",
        "StockMerger",
        "UnitSplit",
        "WorthlessRemoval",
    },
    "requests": set(),
}

# Members an enum shape keeps although its generated twin lacks them, so they are not
# deprecated.
KEPT_MEMBERS_MISSING_FROM_TWIN: dict[str, set[str]] = {}

PACKAGE = alpaca.data

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
        (enums, generated_enums, "MarketType"),
        (enums, generated_enums, "NewsImageSize"),
        (enums, generated_enums, "OptionFeed"),
        (enums, generated_enums, "MostActivesByParameter"),
        (enums, generated_enums, "StockLatestFeed"),
        (models, generated_models, "StockBar"),
        (models, generated_models, "CryptoTrade"),
        (models, generated_models, "OptionGreeks"),
        (models, generated_models, "NewsImage"),
        (models, generated_models, "MostActive"),
    ],
)
def test_canonical_public_types_are_generated(
    public_module, generated_module, canonical_name
):
    assert getattr(public_module, canonical_name) is getattr(
        generated_module, canonical_name
    )


@pytest.mark.parametrize(
    ("module_name", "public_module"),
    [
        (name, public)
        for name, (public, _) in PUBLIC_MODULES.items()
        # Enum shapes are not deprecated as a whole; see the test below.
        if name != "enums"
    ],
)
def test_same_name_legacy_types_are_deprecated(module_name, public_module):
    for name in SAME_NAME_LEGACY[module_name]:
        obj = getattr(public_module, name)
        assert hasattr(obj, "__deprecated__"), f"{name} should be deprecated"
        assert obj.__deprecated__ == compatibility_shape_message(name)


def test_same_name_legacy_enums_deprecate_only_the_members_their_twin_lacks():
    for name in SAME_NAME_LEGACY["enums"]:
        shape = getattr(enums, name)
        twin = getattr(generated_enums, name)
        # Users have no other name to migrate to, so the enum is not deprecated.
        assert "__deprecated__" not in vars(shape), f"{name} should not be deprecated"
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
    [(enums,), (models,)],
)
def test_deprecated_public_types_point_at_existing_replacements(public_module):
    deprecated_types = [
        (name, obj)
        for name, obj in vars(public_module).items()
        if isinstance(obj, type)
        and hasattr(obj, "__deprecated__")
        and obj.__module__.startswith(public_module.__name__)
    ]
    assert deprecated_types

    module_legacy = next(
        SAME_NAME_LEGACY[name]
        for name, (public, _) in PUBLIC_MODULES.items()
        if public is public_module
    )

    for name, obj in deprecated_types:
        message = obj.__deprecated__
        if name in module_legacy:
            assert message == compatibility_shape_message(name)
            continue
        replacements = _replacements_from_deprecated(message)
        assert replacements, f"{name} has no 'use <Replacement> instead' message"
        for replacement in replacements:
            assert hasattr(
                public_module, replacement
            ), f"{name} points at missing replacement {replacement}"


def test_compatibility_shape_warns_when_instantiated():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        models.Mover(
            symbol="AAPL",
            percent_change=1.0,
            change=2.0,
            price=100.0,
        )

    assert any(
        warning.category is DeprecationWarning
        and "OpenAPI-generated Mover" in str(warning.message)
        for warning in caught
    )


def test_deprecated_enum_warns_when_constructed():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        enums.DataFeed("sip")
        enums.OptionsFeed("opra")
        enums.MostActivesBy("volume")
        enums.CryptoFeed("us")

    messages = [
        str(warning.message)
        for warning in caught
        if warning.category is DeprecationWarning
    ]
    assert any(
        "StockHistoricalFeed" in message and "StockLatestFeed" in message
        for message in messages
    )
    assert any("OptionFeed" in message for message in messages)
    assert any("MostActivesByParameter" in message for message in messages)
    assert any(
        "CryptoHistoricalLoc" in message and "CryptoLatestLoc" in message
        for message in messages
    )


def test_requests_accept_the_replacement_enums():
    bars = requests.StockBarsRequest(
        symbol_or_symbols="AAPL",
        timeframe=TimeFrame.Day,
        feed=enums.StockHistoricalFeed.SIP,
    )
    assert type(bars.feed) is enums.StockHistoricalFeed
    assert bars.to_request_fields()["feed"] == "sip"

    latest = requests.StockLatestQuoteRequest(
        symbol_or_symbols="AAPL", feed=enums.StockLatestFeed.DELAYED_SIP
    )
    assert latest.to_request_fields()["feed"] == "delayed_sip"

    # Strings keep parsing into the legacy enum.
    assert (
        type(
            requests.StockLatestQuoteRequest(symbol_or_symbols="AAPL", feed="iex").feed
        )
        is enums.DataFeed
    )

    chain = requests.OptionChainRequest(
        underlying_symbol="AAPL", feed=enums.OptionFeed.INDICATIVE
    )
    assert chain.to_request_fields()["feed"] == "indicative"

    movers = requests.MostActivesRequest(by=enums.MostActivesByParameter.TRADES)
    assert movers.to_request_fields()["by"] == "trades"


def test_deprecated_compatibility_types_do_not_warn_during_import():
    subprocess.run(
        [
            sys.executable,
            "-W",
            "error::DeprecationWarning",
            "-c",
            "import alpaca.data.enums; import alpaca.data.models; import alpaca.data.requests",
        ],
        check=True,
    )
