import pytest

from tools.scripts.openapi import fetch_specs

NORMALIZED_SPEC = '{\n  "openapi": "3.0.1"\n}\n'


def test_fetch_spec_replaces_destination_only_when_content_changes(
    tmp_path, monkeypatch
):
    destination = tmp_path / "trading-api.json"
    destination.write_text('{\n  "openapi": "3.0.0"\n}\n')
    monkeypatch.setattr(fetch_specs, "_download", lambda _: b'{"openapi":"3.0.1"}')

    assert fetch_specs.fetch_spec("https://example.test/spec.json", destination)
    assert destination.read_text() == NORMALIZED_SPEC
    assert not list(tmp_path.glob("*.tmp"))


def test_fetch_spec_keeps_identical_destination(tmp_path, monkeypatch):
    destination = tmp_path / "trading-api.json"
    destination.write_text(NORMALIZED_SPEC)
    before = destination.stat().st_mtime_ns
    monkeypatch.setattr(fetch_specs, "_download", lambda _: destination.read_bytes())

    assert not fetch_specs.fetch_spec("https://example.test/spec.json", destination)
    assert destination.stat().st_mtime_ns == before


def test_fetch_spec_normalizes_minified_upstream_payload(tmp_path, monkeypatch):
    """Upstream publishes minified JSON; the pinned copy must stay diff-friendly."""
    destination = tmp_path / "trading-api.json"
    monkeypatch.setattr(
        fetch_specs,
        "_download",
        lambda _: b'{"openapi":"3.1.2","info":{"title":"Trading API"}}',
    )

    assert fetch_specs.fetch_spec("https://example.test/spec.json", destination)
    assert destination.read_text() == (
        "{\n"
        '  "openapi": "3.1.2",\n'
        '  "info": {\n'
        '    "title": "Trading API"\n'
        "  }\n"
        "}\n"
    )


@pytest.mark.parametrize(
    "payload",
    [b"[]", b'{"openapi":"2.0"}', b"{}"],
)
def test_fetch_spec_rejects_unusable_documents(tmp_path, monkeypatch, payload):
    destination = tmp_path / "trading-api.json"
    monkeypatch.setattr(fetch_specs, "_download", lambda _: payload)

    with pytest.raises(ValueError):
        fetch_specs.fetch_spec("https://example.test/spec.json", destination)

    assert not destination.exists()
