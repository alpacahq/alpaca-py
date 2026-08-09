"""Tests for runtime version resolution."""

import platform

import alpaca
from alpaca import __version__
from alpaca._version_resolve import resolve_version
from alpaca.common.utils import get_default_user_agent


def test_resolve_version_keeps_substituted_build_version():
    assert resolve_version("0.43.5") == "0.43.5"
    assert resolve_version("0.43.5.post9.dev0+0ab791a") == "0.43.5.post9.dev0+0ab791a"


def test_resolve_version_strips_leading_v():
    assert resolve_version("v0.43.5") == "0.43.5"


def test_resolve_version_uses_git_for_placeholder(monkeypatch):
    import alpaca._version_resolve as version_mod

    monkeypatch.setattr(version_mod, "version_from_git", lambda: "0.43.5-dev+g0bc1e2d")
    assert version_mod.resolve_version("0.0.0") == "0.43.5-dev+g0bc1e2d"
    assert version_mod.resolve_version("0.0.0.dev0") == "0.43.5-dev+g0bc1e2d"


def test_resolve_version_falls_back_when_git_unavailable(monkeypatch):
    import alpaca._version_resolve as version_mod

    monkeypatch.setattr(version_mod, "version_from_git", lambda: None)
    assert version_mod.resolve_version("0.0.0") == "0.0.0-dev"


def test_version_from_git_parses_describe_long(monkeypatch):
    import alpaca._version_resolve as version_mod

    monkeypatch.setattr(
        version_mod.subprocess,
        "check_output",
        lambda *args, **kwargs: "v0.43.5-16-g0bc1e2d\n",
    )
    assert version_mod.version_from_git() == "0.43.5-dev+g0bc1e2d"


def test_version_from_git_parses_describe_long_on_tag(monkeypatch):
    import alpaca._version_resolve as version_mod

    monkeypatch.setattr(
        version_mod.subprocess,
        "check_output",
        lambda *args, **kwargs: "v0.43.5-0-gabcd123\n",
    )
    assert version_mod.version_from_git() == "0.43.5-dev+gabcd123"


def test_version_from_git_returns_none_on_subprocess_error(monkeypatch):
    import alpaca._version_resolve as version_mod

    def boom(*args, **kwargs):
        raise version_mod.subprocess.CalledProcessError(128, "git")

    monkeypatch.setattr(version_mod.subprocess, "check_output", boom)
    assert version_mod.version_from_git() is None


def test_version_from_git_returns_none_on_unparseable_output(monkeypatch):
    import alpaca._version_resolve as version_mod

    monkeypatch.setattr(
        version_mod.subprocess,
        "check_output",
        lambda *args, **kwargs: "not-a-describe\n",
    )
    assert version_mod.version_from_git() is None


def test_version_from_git_uses_single_subprocess_call(monkeypatch):
    import alpaca._version_resolve as version_mod

    calls = []

    def fake_check_output(cmd, **kwargs):
        calls.append(cmd)
        return "v1.2.3-4-gabcdef0\n"

    monkeypatch.setattr(version_mod.subprocess, "check_output", fake_check_output)
    assert version_mod.version_from_git() == "1.2.3-dev+gabcdef0"
    assert len(calls) == 1
    assert calls[0][:4] == ["git", "describe", "--tags", "--long"]


def test_package_namespace_does_not_expose_resolver():
    public = [name for name in dir(alpaca) if not name.startswith("__")]
    assert "_version_resolve" not in public
    assert "resolve_version" not in public
    assert "version_from_git" not in public


def test_user_agent_uses_resolved_package_version():
    assert get_default_user_agent() == (
        f"APCA-PY/{__version__} Python/{platform.python_version()}"
    )
