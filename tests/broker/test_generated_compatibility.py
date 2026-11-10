import ast
import importlib
import re
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

import alpaca.broker
from alpaca._deprecating_enum import DeprecatingEnumMeta
from alpaca.broker import enums, models, requests
from alpaca.broker._generated import enums as generated_enums
from alpaca.broker._generated import models as generated_models
from alpaca.broker._generated import requests as generated_requests
from alpaca.common._deprecation import (
    build_from_response,
    compatibility_shape_message,
)
from alpaca.common.models import ModelWithID
from alpaca.trading import enums as trading_enums

# Same-name generated types that intentionally keep the handwritten public binding.
# Generated implementations stay available from alpaca.broker._generated.*.
SAME_NAME_LEGACY = {
    "enums": {
        "AgreementType",  # public keeps deprecated short aliases and CUSTODIAL_CUSTOMER
        "JournalEntryType",  # public keeps deprecated CASH/SECURITY aliases
        "TaxIdType",  # public keeps ARG_AR_CUIT; the spec spells it ARG_AG_CUIT
        "TransferStatus",  # public keeps deprecated SETTLED
    },
    "models": {
        "ACHRelationship",  # public keeps processor_token; generated adds requiredness drift
        "Account",  # public keeps custom __init__ and kyc_results / account_sub_type
        "AccountExtended",  # public keeps newly documented account response fields
        "AccountDocument",  # public uses content/mime_type; generated is TradeDocument-shaped
        "BankAdditionalFields",  # public keeps intermediary-bank instructions
        "Bank",  # generated adds extra_fields
        "BatchJournalResponse",  # public subclasses legacy Journal
        "Beneficiary",  # public keeps the documented IRA beneficiary shape
        "CIPDocument",  # public keeps compromised_document spelling
        "CIPPhoto",  # public keeps face_comparision spelling
        "Disclosures",  # generated adds employment_sector / context
        "Agreement",  # public keeps str signed_at and the short-name AgreementType
        "CIPIdentity",  # public keeps CIPResult/CIPStatus enums and datetime created_at
        "CIPInfo",  # public keeps required ids/timestamps and CIPProvider list
        "CIPWatchlist",  # public keeps CIPResult/CIPStatus enums and datetime created_at
        "Identity",  # generated adds investment-profile fields
        "Journal",  # generated adds created_at / transmitter_info
        "Order",  # public subclasses Trading Order and adds commission
        "Portfolio",  # public keeps rebalance_conditions field name
        "RebalancingConditions",  # public keeps float percent and enum type/sub_type
        "TradeAccount",  # public subclasses Trading TradeAccount with broker fields
        "Transfer",  # generated adds ira / hold_until / instant_amount
        "TransferIRADetails",  # public keeps documented IRA distribution fields
    },
    "requests": {
        "CreateACHRelationshipRequest",  # generated adds instant / processor_token
        "CreateBankRequest",  # generated adds extra_fields; public keeps ABA/BIC validator
        "CreateJournalRequest",  # public keeps float amount and entry-type validators
    },
}

# Members an enum shape keeps although its generated twin lacks them, so they are not
# deprecated.
KEPT_MEMBERS_MISSING_FROM_TWIN = {
    # Likely a spec typo; see docs/openapi-spec-discrepancies.md.
    "TaxIdType": {"ARG_AR_CUIT"},
}

PACKAGE = alpaca.broker

# Same-name public types that subclass the generated type to attach SDK-only behavior
# (not temporary compatibility shapes, so they are not deprecated).
SAME_NAME_SDK_EXTENSIONS = {
    "enums": set(),
    "models": {
        "Contact",  # keeps the published usa_state_has_value validator
        "TrustedContact",  # accepts a deprecated string street_address and stores a list
    },
    "requests": set(),
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
    assert mismatches == (
        SAME_NAME_LEGACY[module_name] | SAME_NAME_SDK_EXTENSIONS[module_name]
    )


@pytest.mark.parametrize(
    ("public_module", "generated_module", "canonical_name"),
    [
        (enums, generated_enums, "AccountSubType"),
        (enums, generated_enums, "AccountType"),
        (enums, generated_enums, "ACHRelationshipStatus"),
        (enums, generated_enums, "BankStatus"),
        (enums, generated_enums, "JournalStatus"),
        (enums, generated_enums, "PortfolioStatus"),
        (enums, generated_enums, "TransferDirection"),
        (enums, generated_enums, "TransferType"),
        (enums, generated_enums, "DisclosuresEmploymentStatus"),
        (enums, generated_enums, "PortfolioRunStatus"),
        (models, generated_models, "SkippedOrder"),
        (requests, generated_requests, "CreateTransferRequest"),
        (requests, generated_requests, "CreateOrderRequest"),
        (requests, generated_requests, "AccountCreationRequest"),
    ],
)
def test_canonical_public_types_are_generated(
    public_module, generated_module, canonical_name
):
    assert getattr(public_module, canonical_name) is getattr(
        generated_module, canonical_name
    )


@pytest.mark.parametrize(
    ("module_path", "name", "canonical"),
    [
        ("alpaca.broker.models.accounts", "AgreementType", enums.AgreementType),
        ("alpaca.broker.models", "CIPProvider", enums.CIPProvider),
        ("alpaca.broker.models.cip", "CIPProvider", enums.CIPProvider),
        ("alpaca.broker.requests", "CalendarSubType", enums.CalendarSubType),
        ("alpaca.broker.requests", "DriftBandSubType", enums.DriftBandSubType),
        (
            "alpaca.broker.requests",
            "RebalancingConditionsType",
            enums.RebalancingConditionsType,
        ),
        ("alpaca.broker.models.cip", "ModelWithID", ModelWithID),
    ],
)
def test_legacy_import_paths_stay_bound(module_path, name, canonical):
    module = importlib.import_module(module_path)
    assert getattr(module, name) is canonical


def test_models_agreement_type_uses_compatibility_shape():
    # alpaca.broker.models re-exports the enums-module compatibility shape (which keeps
    # the deprecated short member names), not the generated enum, so every public
    # AgreementType path resolves to the same shape and stays backwards compatible.
    assert models.AgreementType is enums.AgreementType
    assert models.AgreementType is not generated_enums.AgreementType


def test_trusted_contact_requires_a_contact_method():
    with pytest.raises(ValueError, match="At least one method of contact"):
        models.TrustedContact(given_name="Jane", family_name="Doe")

    contact = models.TrustedContact(
        given_name="Jane", family_name="Doe", email_address="jane@example.com"
    )
    assert contact.email_address == "jane@example.com"


def test_contact_leaves_the_usa_state_rule_to_the_api():
    # The Broker API requires contact.state on create only for US tax residents and
    # never checks presence on partial updates, so the SDK rejects nothing here
    # (as in earlier releases) and keeps usa_state_has_value for compatibility.
    assert issubclass(models.Contact, generated_models.Contact)
    assert hasattr(models.Contact, "usa_state_has_value")
    assert hasattr(requests.UpdatableContact, "usa_state_has_value")

    without_state = models.Contact(
        email_address="a@b.com",
        street_address=["1 Main"],
        city="San Mateo",
        country="USA",
    )
    assert without_state.state is None
    assert requests.UpdatableContact(country="USA").state is None

    contact = models.Contact(
        email_address="a@b.com",
        street_address=["1 Main"],
        city="San Mateo",
        state="CA",
        country="USA",
    )
    assert contact.state == "CA"


@pytest.mark.parametrize(
    ("module_name", "public_module"),
    [(name, public) for name, (public, _) in PUBLIC_MODULES.items()],
)
def test_same_name_legacy_types_are_deprecated(module_name, public_module):
    for name in SAME_NAME_LEGACY[module_name]:
        obj = getattr(public_module, name)
        assert hasattr(obj, "__deprecated__"), f"{name} should be deprecated"
        # Enum shapes add a sentence naming the members their twin lacks.
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
        and "__deprecated__" in obj.__dict__
        and obj.__module__.startswith(public_module.__name__)
    ]
    assert deprecated_types

    # A compatibility shape can live in a different public module than its generated
    # twin (RebalancingConditions is defined in requests; the generated one is a model).
    all_legacy = set().union(*SAME_NAME_LEGACY.values())

    for name, obj in deprecated_types:
        message = obj.__deprecated__
        if name in all_legacy:
            assert message.startswith(compatibility_shape_message(name)), name
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
        models.Identity(
            given_name="John",
            family_name="Doe",
            country_of_tax_residence="USA",
        )

    assert any(
        warning.category is DeprecationWarning
        and "OpenAPI-generated Identity" in str(warning.message)
        for warning in caught
    )


def test_deprecated_enum_warns_when_constructed():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        enums.EmploymentStatus("EMPLOYED")
        enums.RunType("full_rebalance")
        enums.RunStatus("QUEUED")
        enums.RunInitiatedFrom("api")
        enums.AccountEntities("contact")
        enums.CIPApprovalStatus("approved")
        enums.FundingSource("savings")
        enums.IdentifierType("ABA")
        enums.RecipientBankStatus("ACTIVE")
        enums.WeightType("cash")

    messages = [
        str(warning.message)
        for warning in caught
        if warning.category is DeprecationWarning
    ]
    assert any("DisclosuresEmploymentStatus" in message for message in messages)
    assert any("PortfolioRunType" in message for message in messages)
    assert any("PortfolioRunStatus" in message for message in messages)
    assert any("PortfolioRunInitiatedFrom" in message for message in messages)
    assert any("GetAllAccountsEntitiesParameter" in message for message in messages)
    for replacement in (
        "CIPKYCApprovalStatus",
        "IdentityFundingSourceInner",
        "BankBankCodeType",
        "GetRecipientBanksStatusParameter",
        "PortfolioWeightRequestType",
    ):
        assert any(replacement in message for message in messages), replacement
    assert {member.value for member in enums.AccountEntities} == {
        member.value for member in enums.GetAllAccountsEntitiesParameter
    }


def test_journal_entry_type_short_names_are_deprecated_aliases():
    with pytest.warns(DeprecationWarning, match="JournalEntryType.JNLC") as caught:
        cash = enums.JournalEntryType.CASH
    assert [warning.filename for warning in caught] == [__file__]
    assert cash is enums.JournalEntryType.JNLC
    with pytest.warns(DeprecationWarning, match="JournalEntryType.JNLS"):
        assert enums.JournalEntryType.SECURITY is enums.JournalEntryType.JNLS

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        assert enums.JournalEntryType("JNLC") is enums.JournalEntryType.JNLC
        assert enums.JournalEntryType("JNLS") is enums.JournalEntryType.JNLS


def test_requests_accept_the_replacement_enums():
    runs = requests.GetRunsRequest(type=enums.PortfolioRunType.INVEST_CASH)
    assert type(runs.type) is enums.PortfolioRunType
    assert runs.to_request_fields()["type"] == "invest_cash"
    # Strings keep parsing into the legacy enum.
    assert type(requests.GetRunsRequest(type="invest_cash").type) is enums.RunType

    weight = requests.Weight(type=enums.PortfolioWeightRequestType.CASH, percent=10.0)
    assert weight.type == "cash"

    accounts = requests.ListAccountsRequest(
        entities=[enums.GetAllAccountsEntitiesParameter.CONTACT]
    )
    assert accounts.to_request_fields()["entities"] == ["contact"]

    documents = requests.GetTradeDocumentsRequest(
        type=enums.GetDocsForAccountTypeParameter.CRYPTO_ACCOUNT_STATEMENT
    )
    assert documents.to_request_fields()["type"] == "crypto_account_statement"

    with warnings.catch_warnings():
        # CreateACHRelationshipRequest is itself a compatibility shape.
        warnings.simplefilter("ignore", DeprecationWarning)
        relationship = requests.CreateACHRelationshipRequest(
            account_owner_name="Jane Doe",
            bank_account_type=enums.CreateACHRelationshipRequestBankAccountType.SAVINGS,
            bank_account_number="123456789",
            bank_routing_number="121000358",
        )
    assert relationship.to_request_fields()["bank_account_type"] == "SAVINGS"


@pytest.mark.parametrize(
    ("enum_cls", "value", "replacements"),
    [
        # A runtime warning would also fire for CHECKING and SAVINGS and double the
        # per-member warning on NONE.
        (
            enums.BankAccountType,
            "CHECKING",
            (
                "ACHRelationshipBankAccountType",
                "CreateACHRelationshipRequestBankAccountType",
            ),
        ),
        # A runtime warning would fire while parsing documents whose type this enum
        # lacks, since Pydantic calls the enum class to look them up.
        (
            enums.TradeDocumentType,
            "account_statement",
            ("AccountDocumentType", "GetDocsForAccountTypeParameter"),
        ),
        # Same for account documents whose type this enum lacks.
        (enums.DocumentType, "w8ben", ("OwnerDocumentType",)),
    ],
)
def test_statically_deprecated_enums_do_not_warn_at_runtime(
    enum_cls, value, replacements
):
    for replacement in replacements:
        assert replacement in enum_cls.__deprecated__

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        assert enum_cls(value).value == value


def test_trade_document_parses_types_missing_from_the_legacy_enum():
    def document(document_type: str):
        return models.TradeDocument(
            id="b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
            name="statement",
            type=document_type,
            date="2024-01-31",
        )

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        crypto = document("crypto_account_statement")
        options = document("options_application")
        legacy = document("tax_w8")

    assert crypto.type is enums.AccountDocumentType.CRYPTO_ACCOUNT_STATEMENT
    assert options.type is enums.AccountDocumentType.OPTIONS_APPLICATION
    # Values the legacy enum has keep parsing into it.
    assert legacy.type is enums.TradeDocumentType.TAX_W8


def test_account_document_parses_types_missing_from_the_legacy_enum():
    def document(document_type: str):
        # Built as the client builds responses: AccountDocument is itself a
        # compatibility shape that warns when instantiated directly.
        return build_from_response(
            models.AccountDocument,
            {
                "id": "b0b6dd9d-8b9b-48a9-ba46-b9d54906e415",
                "document_type": document_type,
            },
        )

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        w9 = document("w9")
        formation = document("company_formation")
        other = document("other")

    assert w9.document_type is enums.OwnerDocumentType.W9
    assert formation.document_type is enums.OwnerDocumentType.COMPANY_FORMATION
    # Values the legacy enum has keep parsing into it.
    assert other.document_type is enums.DocumentType.OTHER


def test_upload_document_request_accepts_the_generated_document_type():
    upload = requests.UploadDocumentRequest(
        document_type=enums.OwnerDocumentType.W9,
        content="ZGF0YQ==",
        mime_type=enums.UploadDocumentMimeType.PDF,
    )
    assert upload.to_request_fields()["document_type"] == "w9"

    # W8BEN still has to go through UploadW8BenDocumentRequest.
    with pytest.raises(ValueError, match="UploadW8BenDocument"):
        requests.UploadDocumentRequest(
            document_type=enums.OwnerDocumentType.W8BEN,
            content="ZGF0YQ==",
            mime_type=enums.UploadDocumentMimeType.PDF,
        )


def test_input_models_accept_the_replacement_enums():
    identity = build_from_response(
        models.Identity,
        {
            "given_name": "Jane",
            "family_name": "Doe",
            "country_of_tax_residence": "USA",
            "funding_source": [enums.IdentityFundingSourceInner.SAVINGS],
        },
    )
    assert identity.funding_source == ["savings"]

    configurations = models.AccountTradingConfigurations(
        trade_confirm_email=enums.AccountConfigurationsTradeConfirmEmail.NONE
    )
    assert configurations.trade_confirm_email == "none"


def test_account_activities_request_accepts_both_category_enums():
    # ActivityCategory's deprecation names the Trading enum, while the Broker spec
    # generates its own class with the same values.
    for category in (
        enums.GetAccountActivitiesCategoryParameter.TRADE_ACTIVITY,
        trading_enums.GetAccountActivitiesCategoryParameter.TRADE_ACTIVITY,
    ):
        request = requests.GetAccountActivitiesRequest(category=category)
        assert type(request.category) is type(category)
        assert request.to_request_fields()["category"] == "trade_activity"


def test_deprecated_compatibility_types_do_not_warn_during_import():
    subprocess.run(
        [
            sys.executable,
            "-W",
            "error::DeprecationWarning:alpaca",
            "-c",
            "import alpaca.broker.enums; import alpaca.broker.models; import alpaca.broker.requests",
        ],
        check=True,
    )
