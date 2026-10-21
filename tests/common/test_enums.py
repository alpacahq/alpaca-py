import subprocess
import sys
import warnings

import pytest
from pydantic import TypeAdapter

from alpaca.common.enums import BaseURL


@pytest.mark.parametrize("lookup", [getattr, lambda cls, name: cls[name]])
def test_option_data_stream_warns_and_preserves_alias(lookup):
    with pytest.deprecated_call(
        match="Use BaseURL.MARKET_DATA_STREAM instead"
    ) as caught:
        member = lookup(BaseURL, "OPTION_DATA_STREAM")

    assert len(caught) == 1
    assert caught[0].filename == __file__
    assert member is BaseURL.MARKET_DATA_STREAM
    assert member.value == "wss://stream.data.alpaca.markets"


def test_market_data_stream_value_remains_supported_without_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        canonical = BaseURL.MARKET_DATA_STREAM
        assert BaseURL["MARKET_DATA_STREAM"] is canonical
        assert BaseURL(canonical.value) is canonical
        adapter = TypeAdapter(BaseURL)
        member = adapter.validate_python(canonical.value)
        assert member is canonical
        assert adapter.dump_json(member) == b'"wss://stream.data.alpaca.markets"'


def test_base_url_import_does_not_warn():
    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::DeprecationWarning",
            "-c",
            "from alpaca.common.enums import BaseURL",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
