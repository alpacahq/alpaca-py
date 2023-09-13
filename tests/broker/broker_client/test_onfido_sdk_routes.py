from alpaca.broker.client import BrokerClient

from alpaca.common.enums import BaseURL

from alpaca.broker.models.accounts import OnfidoToken

from alpaca.broker.requests import UpdateOnfidoOutcomeRequest


def test_get_onfido_sdk_token(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"

    reqmock.get(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/onfido/sdk/tokens",
        text="""
            {
            "token": "header.payload.signature"
            }
            """,
    )
    token = client.get_onfido_sdk_token(account_id)

    assert reqmock.called_once
    assert isinstance(token, OnfidoToken)
    assert isinstance(token.token, str)


def test_patch_onfido_sdk_outcome(reqmock, client: BrokerClient):
    account_id = "2a87c088-ffb6-472b-a4a3-cd9305c8605c"
    outcome = UpdateOnfidoOutcomeRequest(
        **{
            "outcome": "USER_EXITED",
            "reason": "User denied consent",
            "token": "header.payload.signature",
        }
    )
    reqmock.patch(
        f"{BaseURL.BROKER_SANDBOX.value}/v1/accounts/{account_id}/onfido/sdk/",
        text=outcome.model_dump_json(),
    )
    client.update_onfido_sdk_outcome(account_id, onfido_outcome=outcome)

    assert reqmock.called_once
