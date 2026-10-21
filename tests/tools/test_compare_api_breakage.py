"""Unit tests for tools/scripts/compare_api_breakage.py pure helpers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPOSITORY_ROOT / "tools" / "scripts" / "compare_api_breakage.py"


@pytest.fixture(scope="module")
def cab():
    spec = importlib.util.spec_from_file_location("compare_api_breakage", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestNormalizeVersion:
    def test_metadata_local_version_unchanged(self, cab):
        assert cab._normalize_version("0.43.5.post30.dev0+g382857f") == (
            "0.43.5.post30.dev0+g382857f"
        )

    def test_wheel_filename_local_version_decoded(self, cab):
        assert cab._normalize_version("0.43.5.post30.dev0_g382857f") == (
            "0.43.5.post30.dev0+g382857f"
        )

    def test_wheel_filename_local_dots_become_underscores(self, cab):
        assert cab._normalize_version("1.0.0_abc_def") == "1.0.0+abc.def"

    def test_release_version_unchanged(self, cab):
        assert cab._normalize_version("0.43.5") == "0.43.5"

    def test_versions_equal_across_encodings(self, cab):
        assert cab._versions_equal(
            "0.43.5.post30.dev0_g382857f",
            "0.43.5.post30.dev0+g382857f",
        )


class TestDownloadReleaseWheelSelection:
    def test_post_release_wheel_is_accepted(self, cab, tmp_path, monkeypatch):
        version = "0.43.5.post1"
        wheel = tmp_path / f"alpaca_py-{version}-py3-none-any.whl"
        wheel.write_bytes(b"")

        def fake_pip(python, *args, verbose=True):
            return None

        monkeypatch.setattr(cab, "_pip", fake_pip)
        selected = cab._download_release_wheel(
            tmp_path / "python", version, tmp_path, verbose=False
        )
        assert selected == wheel

    def test_release_wheel_is_accepted(self, cab, tmp_path, monkeypatch):
        version = "0.43.5"
        wheel = tmp_path / f"alpaca_py-{version}-py3-none-any.whl"
        wheel.write_bytes(b"")

        monkeypatch.setattr(cab, "_pip", lambda *args, **kwargs: None)
        selected = cab._download_release_wheel(
            tmp_path / "python", version, tmp_path, verbose=False
        )
        assert selected == wheel


class TestBuildRefWheel:
    def test_reuses_cached_wheel_without_building(self, cab, tmp_path, monkeypatch):
        sha = "a" * 40
        cache_root = tmp_path / "baseline"
        wheel_dir = cache_root / sha
        wheel_dir.mkdir(parents=True)
        wheel = wheel_dir / "alpaca_py-0.0.0-py3-none-any.whl"
        wheel.write_bytes(b"")

        monkeypatch.setattr(cab.shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(cab, "_resolve_ref", lambda git, ref, verbose=True: sha)

        def fail_run(cmd, **kwargs):
            raise AssertionError(f"should not run commands: {cmd}")

        monkeypatch.setattr(cab, "_run", fail_run)
        selected = cab._build_ref_wheel("master", cache_root, verbose=False)
        assert selected == wheel

    def test_builds_wheel_in_detached_worktree(self, cab, tmp_path, monkeypatch):
        sha = "b" * 40
        cache_root = tmp_path / "baseline"
        calls: list[list[str]] = []

        monkeypatch.setattr(cab.shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(cab, "_resolve_ref", lambda git, ref, verbose=True: sha)

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            if len(cmd) > 1 and cmd[1] == "build":
                out_dir = Path(cmd[cmd.index("-o") + 1])
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "alpaca_py-0.0.0-py3-none-any.whl").write_bytes(b"")
            return None

        monkeypatch.setattr(cab, "_run", fake_run)
        selected = cab._build_ref_wheel("master", cache_root, verbose=False)

        assert selected == cache_root / sha / "alpaca_py-0.0.0-py3-none-any.whl"
        # worktree is added detached, used to build, then removed -- in that order.
        add_idx = next(
            i for i, c in enumerate(calls) if c[1] == "worktree" and c[2] == "add"
        )
        build_idx = next(i for i, c in enumerate(calls) if c[1] == "build")
        remove_idx = next(
            i for i, c in enumerate(calls) if c[1] == "worktree" and c[2] == "remove"
        )
        assert add_idx < build_idx < remove_idx
        assert calls[add_idx][3:5] == ["--force", "--detach"]
        assert calls[add_idx][-1] == sha
        assert "--force" in calls[remove_idx]
        assert not any(c[1:3] == ["worktree", "prune"] for c in calls)

    def test_removes_worktree_and_skips_cache_when_build_fails(
        self, cab, tmp_path, monkeypatch
    ):
        sha = "c" * 40
        cache_root = tmp_path / "baseline"
        calls: list[list[str]] = []

        monkeypatch.setattr(cab.shutil, "which", lambda name: f"/usr/bin/{name}")
        monkeypatch.setattr(cab, "_resolve_ref", lambda git, ref, verbose=True: sha)

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            if len(cmd) > 1 and cmd[1] == "build":
                raise cab.ToolError("build failed")

        monkeypatch.setattr(cab, "_run", fake_run)
        with pytest.raises(cab.ToolError, match="build failed"):
            cab._build_ref_wheel("master", cache_root, verbose=False)

        build_idx = next(i for i, c in enumerate(calls) if c[1] == "build")
        remove_idx = next(
            i for i, c in enumerate(calls) if c[1:3] == ["worktree", "remove"]
        )
        assert build_idx < remove_idx
        assert not list((cache_root / sha).glob("*.whl"))

    def test_raises_without_git(self, cab, tmp_path, monkeypatch):
        monkeypatch.setattr(
            cab.shutil, "which", lambda name: None if name == "git" else "/x"
        )
        with pytest.raises(cab.ToolError, match="git is required"):
            cab._build_ref_wheel("master", tmp_path, verbose=False)


class TestCompareEnums:
    def test_removed_member_is_breaking(self, cab):
        old = {
            "enums": {
                "alpaca.trading.OrderSide": {
                    "target": "alpaca.trading.enums.OrderSide",
                    "members": {"BUY": "'buy'", "SELL": "'sell'"},
                }
            }
        }
        new = {
            "enums": {
                "alpaca.trading.OrderSide": {
                    "target": "alpaca.trading.enums.OrderSide",
                    "members": {"BUY": "'buy'"},
                }
            }
        }
        breaking, additive = cab._compare_enums(old, new)
        assert any("SELL removed" in msg for msg, _ in breaking)
        assert additive == []

    def test_value_change_is_breaking(self, cab):
        old = {
            "enums": {
                "alpaca.trading.OrderSide": {
                    "target": "alpaca.trading.enums.OrderSide",
                    "members": {"BUY": "'buy'"},
                }
            }
        }
        new = {
            "enums": {
                "alpaca.trading.OrderSide": {
                    "target": "alpaca.trading.enums.OrderSide",
                    "members": {"BUY": "'BUY'"},
                }
            }
        }
        breaking, _ = cab._compare_enums(old, new)
        assert any("value changed" in msg for msg, _ in breaking)

    def test_added_member_is_additive(self, cab):
        old = {
            "enums": {
                "alpaca.trading.OrderSide": {
                    "target": "alpaca.trading.enums.OrderSide",
                    "members": {"BUY": "'buy'"},
                }
            }
        }
        new = {
            "enums": {
                "alpaca.trading.OrderSide": {
                    "target": "alpaca.trading.enums.OrderSide",
                    "members": {"BUY": "'buy'", "SELL": "'sell'"},
                }
            }
        }
        breaking, additive = cab._compare_enums(old, new)
        assert breaking == []
        assert any("SELL added" in msg for msg, _ in additive)

    def test_target_identity_swap_is_breaking_even_with_same_members(self, cab):
        old = {
            "enums": {
                "alpaca.trading.AccountStatus": {
                    "target": "alpaca.trading.enums.AccountStatus",
                    "members": {"ACTIVE": "'ACTIVE'"},
                }
            }
        }
        new = {
            "enums": {
                "alpaca.trading.AccountStatus": {
                    "target": "alpaca.trading._generated.enums.AccountStatus",
                    "members": {"ACTIVE": "'ACTIVE'"},
                }
            }
        }
        breaking, additive = cab._compare_enums(old, new)
        assert any("target changed" in msg for msg, _ in breaking)
        assert additive == []

    def test_removed_export_is_breaking(self, cab):
        old = {
            "enums": {
                "alpaca.trading.OrderSide": {
                    "target": "alpaca.trading.enums.OrderSide",
                    "members": {"BUY": "'buy'"},
                }
            }
        }
        new = {"enums": {}}
        breaking, _ = cab._compare_enums(old, new)
        assert any("no longer exported" in msg for msg, _ in breaking)


class TestCompareModels:
    def _model(self, target: str, fields: dict) -> dict:
        return {"target": target, "fields": fields}

    def test_removed_field_is_breaking(self, cab):
        old = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "id": {
                            "type": "UUID",
                            "required": True,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                        "symbol": {
                            "type": "str",
                            "required": True,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        new = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "id": {
                            "type": "UUID",
                            "required": True,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        breaking, additive = cab._compare_models(old, new)
        assert any("symbol removed" in msg for msg, _ in breaking)
        assert additive == []

    def test_optional_field_added_is_additive(self, cab):
        old = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "id": {
                            "type": "UUID",
                            "required": True,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        new = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "id": {
                            "type": "UUID",
                            "required": True,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                        "note": {
                            "type": "str | None",
                            "required": False,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        breaking, additive = cab._compare_models(old, new)
        assert breaking == []
        assert any("note added" in msg for msg, _ in additive)

    def test_required_field_added_is_breaking(self, cab):
        old = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "id": {
                            "type": "UUID",
                            "required": True,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        new = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "id": {
                            "type": "UUID",
                            "required": True,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                        "symbol": {
                            "type": "str",
                            "required": True,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        breaking, _ = cab._compare_models(old, new)
        assert any("required field symbol added" in msg for msg, _ in breaking)

    def test_requiredness_tightening_is_breaking(self, cab):
        old = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "symbol": {
                            "type": "str | None",
                            "required": False,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        new = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "symbol": {
                            "type": "str",
                            "required": True,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        breaking, _ = cab._compare_models(old, new)
        assert any("became required" in msg for msg, _ in breaking)

    def test_type_change_is_breaking(self, cab):
        old = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "qty": {
                            "type": "str | None",
                            "required": False,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        new = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order",
                    {
                        "qty": {
                            "type": "StrictStr | None",
                            "required": False,
                            "validation_aliases": [],
                            "serialization_alias": None,
                        },
                    },
                )
            }
        }
        breaking, _ = cab._compare_models(old, new)
        assert any("type changed" in msg for msg, _ in breaking)

    def test_validation_alias_change_is_breaking(self, cab):
        old = {
            "models": {
                "alpaca.trading.Asset": self._model(
                    "alpaca.trading.models.Asset",
                    {
                        "asset_class": {
                            "type": "AssetClass",
                            "required": True,
                            "validation_aliases": ["class"],
                            "serialization_alias": "class",
                        },
                    },
                )
            }
        }
        new = {
            "models": {
                "alpaca.trading.Asset": self._model(
                    "alpaca.trading.models.Asset",
                    {
                        "asset_class": {
                            "type": "AssetClass",
                            "required": True,
                            "validation_aliases": ["class", "asset_class"],
                            "serialization_alias": "class",
                        },
                    },
                )
            }
        }
        breaking, _ = cab._compare_models(old, new)
        assert any("validation_aliases changed" in msg for msg, _ in breaking)

    def test_target_identity_swap_is_breaking(self, cab):
        field = {
            "id": {
                "type": "UUID",
                "required": True,
                "validation_aliases": [],
                "serialization_alias": None,
            }
        }
        old = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading.models.Order", field
                )
            }
        }
        new = {
            "models": {
                "alpaca.trading.Order": self._model(
                    "alpaca.trading._generated.models.Order", field
                )
            }
        }
        breaking, _ = cab._compare_models(old, new)
        assert any("target changed" in msg for msg, _ in breaking)


class TestSummarizeAndTopBreaking:
    def test_summarize_counts_ranks(self, cab, tmp_path):
        changes = tmp_path / "changes.json"
        changes.write_text(
            '{"entries": {'
            '"a": {"rank": 60},'
            '"b": {"rank": 0},'
            '"c": {"rank": -1},'
            '"d": {"rank": {"rank": 80}}'
            "}}"
        )
        assert cab._summarize_changes(changes) == (2, 1, 1)

    def test_top_breaking_entries_sorted_by_rank(self, cab, tmp_path):
        changes = tmp_path / "changes.json"
        changes.write_text(
            '{"entries": {'
            '"low": {"rank": 20, "message": "low"},'
            '"high": {"rank": 80, "message": "high"},'
            '"compat": {"rank": 0, "message": "ok"},'
            '"unknown": {"rank": -1, "message": "unk"}'
            "}}"
        )
        top = cab._top_breaking_entries(changes, limit=5)
        assert [e["message"] for e in top] == ["high", "low"]

    def test_top_breaking_entries_limit_none_returns_all(self, cab, tmp_path):
        changes = tmp_path / "changes.json"
        # 3 breakings so a default cap of 20 is irrelevant; assert no slicing when limit=None
        entries = {f"e{i}": {"rank": 10 + i, "message": f"m{i}"} for i in range(3)}
        changes.write_text(json.dumps({"entries": entries}))
        all_breaking = cab._top_breaking_entries(changes, limit=None)
        assert [e["message"] for e in all_breaking] == ["m2", "m1", "m0"]

    def test_top_breaking_entries_default_limit_still_caps(self, cab, tmp_path):
        changes = tmp_path / "changes.json"
        entries = {f"e{i}": {"rank": i + 1, "message": f"m{i:02d}"} for i in range(25)}
        changes.write_text(json.dumps({"entries": entries}))
        top = cab._top_breaking_entries(changes)
        assert len(top) == cab.TOP_BREAKING_LIMIT
        assert top[0]["message"] == "m24"

    def test_optional_parameter_on_method_is_compatible(self, cab, tmp_path):
        changes = tmp_path / "changes.json"
        changes.write_text(
            json.dumps(
                {
                    "entries": {
                        "opt": {
                            "kind": "AddOptionalParameter",
                            "rank": 60,
                            "message": "Add PositionalOrKeyword parameter: page.",
                        },
                        "req": {
                            "kind": "AddRequiredParameter",
                            "rank": 100,
                            "message": "Add required parameter: id.",
                        },
                    }
                }
            )
        )

        assert cab._summarize_changes(changes) == (1, 1, 0)
        assert [e["message"] for e in cab._top_breaking_entries(changes)] == [
            "Add required parameter: id."
        ]
        assert cab._caller_compatible_entries(changes) == [
            {"rank": 60, "message": "Add PositionalOrKeyword parameter: page."}
        ]

    def test_unknown_entries_lists_negative_ranks(self, cab, tmp_path):
        changes = tmp_path / "changes.json"
        changes.write_text(
            '{"entries": {'
            '"a": {"rank": 60, "message": "break"},'
            '"b": {"rank": 0, "message": "ok"},'
            '"c": {"rank": -1, "message": "unk-b"},'
            '"d": {"rank": -2, "message": "unk-a"}'
            "}}"
        )
        unknown = cab._unknown_entries(changes)
        assert [e["message"] for e in unknown] == ["unk-a", "unk-b"]


class TestDumpErrors:
    def test_require_no_dump_errors_raises(self, cab):
        with pytest.raises(cab.ToolError, match="dump import errors"):
            cab._require_no_dump_errors(
                {"errors": {"alpaca.trading.enums": "ImportError: boom"}}
            )

    def test_require_no_dump_errors_ok_when_empty(self, cab):
        cab._require_no_dump_errors({"errors": {}})


class TestSnapshotImportGuards:
    def test_require_snapshot_location_accepts_site_packages_path(self, cab, tmp_path):
        site_packages = tmp_path / "site-packages"
        location = site_packages / "alpaca" / "__init__.py"
        location.parent.mkdir(parents=True)
        location.touch()
        cab._require_snapshot_location(str(location), site_packages)

    def test_require_snapshot_location_rejects_checkout_path(self, cab, tmp_path):
        site_packages = tmp_path / "venv" / "lib" / "site-packages"
        checkout = tmp_path / "src" / "alpaca" / "__init__.py"
        checkout.parent.mkdir(parents=True)
        checkout.touch()
        with pytest.raises(cab.ToolError, match="expected installed package"):
            cab._require_snapshot_location(str(checkout), site_packages)

    def test_require_snapshot_location_rejects_missing_location(self, cab, tmp_path):
        with pytest.raises(cab.ToolError, match="missing import location"):
            cab._require_snapshot_location(None, tmp_path)

    def test_dump_public_api_uses_isolated_mode_and_empty_run_dir(
        self, cab, tmp_path, monkeypatch
    ):
        calls: list[tuple[list[str], dict]] = []

        def fake_run(cmd, **kwargs):
            calls.append((cmd, kwargs))

            class Result:
                stdout = json.dumps(
                    {
                        "version": "1.0.0",
                        "location": str(
                            tmp_path / "site-packages" / "alpaca" / "__init__.py"
                        ),
                        "enums": {},
                        "models": {},
                        "errors": {},
                    }
                )
                stderr = ""
                returncode = 0

            return Result()

        site_packages = tmp_path / "site-packages"
        (site_packages / "alpaca").mkdir(parents=True)
        (site_packages / "alpaca" / "__init__.py").touch()

        monkeypatch.setattr(cab, "_run", fake_run)
        monkeypatch.setattr(
            cab,
            "_venv_site_packages",
            lambda python, verbose=True: site_packages,
        )

        python = tmp_path / "bin" / "python"
        python.parent.mkdir(parents=True)
        workdir = tmp_path / "work"
        workdir.mkdir()
        (workdir / "alpaca").mkdir()

        cab._dump_public_api(
            python,
            tmp_path / "public.json",
            workdir,
            "1.0.0",
            verbose=False,
        )

        assert len(calls) == 1
        cmd, kwargs = calls[0]
        assert cmd[:3] == [str(python), "-I", "-c"]
        assert kwargs["cwd"] == workdir / ".snapshot_run"
        assert "PYTHONPATH" not in kwargs["env"]
        assert "PYTHONSAFEPATH" not in kwargs["env"]


def _callable(annotation):
    return {"returnAnnotation": annotation, "private": False}


def _change_return(function_id, rank=None):
    """One AexPy ``ChangeReturnType`` entry. Omit ``rank`` to leave it unset."""
    entry = {
        "kind": "ChangeReturnType",
        "message": f"Change return type ({function_id}): old => new",
        "old": {"id": function_id},
        "new": {"id": function_id},
    }
    if rank is not None:
        entry["rank"] = rank
    return entry


_ACCOUNT_EXTENDED_MRO = [
    "alpaca.broker.models.accounts.AccountExtended",
    "alpaca.broker.models.accounts.Account",
    "pydantic.main.BaseModel",
    "builtins.object",
]


def _classes(mro):
    """AexPy ``classes`` entry for ``mro[0]``, shaped like ``api.json``."""
    return {mro[0]: {"id": mro[0], "mros": mro}}


class TestNormalizeTypeAnnotation:
    def test_typing_list_matches_builtin_list(self, cab):
        assert cab._normalize_type_annotation(
            "typing.List[int]"
        ) == cab._normalize_type_annotation("list[int]")

    def test_optional_matches_union_with_none(self, cab):
        assert cab._normalize_type_annotation("typing.Optional[str]") == "None | str"
        assert cab._normalize_type_annotation("Optional[str]") == "None | str"
        assert cab._normalize_type_annotation("str | None") == "None | str"
        assert cab._normalize_type_annotation("typing.Union[str, None]") == "None | str"

    def test_union_order_is_ignored(self, cab):
        assert cab._normalize_type_annotation(
            "B | A"
        ) == cab._normalize_type_annotation("A | B")

    def test_dict_any_alias(self, cab):
        assert cab._normalize_type_annotation(
            "typing.Dict[str, typing.Any]"
        ) == cab._normalize_type_annotation("dict[str, Any]")

    def test_nested_union_inside_tuple(self, cab):
        assert (
            cab._normalize_type_annotation("typing.Tuple[str | None, int]")
            == "tuple[None | str, int]"
        )

    def test_unparseable_text_falls_back_to_collapsed_whitespace(self, cab):
        assert cab._normalize_type_annotation("Literal[1]  extra") == "Literal[1] extra"

    def test_object_address_is_ignored(self, cab):
        assert cab._normalize_type_annotation(
            "<function BaseDataSet.dict at 0x10abf8250>"
        ) == cab._normalize_type_annotation(
            "<function BaseDataSet.dict at 0x10b02eda0>"
        )

    def test_class_repr_unwraps_to_qualified_name(self, cab):
        assert (
            cab._normalize_type_annotation("<class 'alpaca.trading.models.Clock'>")
            == "alpaca.trading.models.Clock"
        )
        assert cab._normalize_type_annotation("<class 'int'>") == "int"
        assert cab._normalize_type_annotation("<class 'NoneType'>") == "None"

    def test_class_repr_matches_union_member(self, cab):
        assert cab._normalize_type_annotation(
            "<class 'alpaca.broker.models.accounts.Account'> | None"
        ) == cab._normalize_type_annotation(
            "alpaca.broker.models.accounts.Account | None"
        )


class TestCompareReturnAnnotations:
    def test_rebalancing_page_returns_are_breaking(self, cab):
        old = {
            "functions": {
                "alpaca.broker.client.BrokerClient.get_all_subscriptions": _callable(
                    "typing.List[alpaca.broker.models.rebalancing.Subscription]"
                    " | typing.List[typing.Dict[str, typing.Any]]"
                ),
                "alpaca.broker.client.BrokerClient.get_all_runs": _callable(
                    "typing.List[alpaca.broker.models.rebalancing.RebalancingRun]"
                    " | typing.List[typing.Dict[str, typing.Any]]"
                ),
            }
        }
        new = {
            "functions": {
                "alpaca.broker.client.BrokerClient.get_all_subscriptions": _callable(
                    "typing.List[alpaca.broker.models.rebalancing.Subscription]"
                    " | alpaca.broker.models.rebalancing.SubscriptionPage"
                    " | typing.Dict[str, typing.Any]"
                ),
                "alpaca.broker.client.BrokerClient.get_all_runs": _callable(
                    "typing.List[alpaca.broker.models.rebalancing.RebalancingRun]"
                    " | alpaca.broker.models.rebalancing.RebalancingRunPage"
                    " | typing.Dict[str, typing.Any]"
                ),
            }
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        messages = [message for message, _ in breaking]
        assert narrowed == []
        assert any(
            "get_all_subscriptions return type changed" in message
            for message in messages
        )
        assert any(
            "get_all_runs return type changed" in message for message in messages
        )
        assert any("SubscriptionPage" in message for message in messages)
        assert any("RebalancingRunPage" in message for message in messages)

    def test_equivalent_spellings_are_not_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_clock"
        old = {"functions": {function_id: _callable("typing.Optional[str]")}}
        new = {"functions": {function_id: _callable("str | None")}}
        assert cab._compare_return_annotations(old, new) == ([], [])

    def test_private_and_newly_annotated_callables_are_ignored(self, cab):
        old = {
            "functions": {
                "alpaca.broker.client.BrokerClient._iterate_over_pages": _callable(
                    "typing.Iterator[int]"
                ),
                "alpaca.broker.client.BrokerClient.create_account": _callable(""),
            }
        }
        new = {
            "functions": {
                "alpaca.broker.client.BrokerClient._iterate_over_pages": _callable(
                    "typing.Iterator[str]"
                ),
                "alpaca.broker.client.BrokerClient.create_account": _callable(
                    "alpaca.broker.models.accounts.Account"
                ),
            }
        }
        assert cab._compare_return_annotations(old, new) == ([], [])

    def test_removed_annotation_is_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_clock"
        old = {"functions": {function_id: _callable("Clock")}}
        new = {"functions": {function_id: _callable("")}}
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert narrowed == []
        assert breaking == [
            (
                "get_clock return type changed: Clock -> <unannotated>",
                [function_id],
            )
        ]

    def test_dropping_none_is_narrowed_not_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_account"
        old = {
            "functions": {
                function_id: _callable(
                    "alpaca.broker.models.accounts.Account"
                    " | typing.Dict[str, typing.Any] | None"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable(
                    "alpaca.broker.models.accounts.Account | typing.Dict[str, typing.Any]"
                )
            }
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert breaking == []
        assert narrowed == [
            (
                "get_account return type narrowed: "
                "None | alpaca.broker.models.accounts.Account | dict[str, Any] "
                "-> alpaca.broker.models.accounts.Account | dict[str, Any]",
                [function_id],
            )
        ]

    def test_dropping_none_from_class_repr_is_narrowed(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_clock"
        old = {
            "functions": {function_id: _callable("alpaca.broker.models.Clock | None")}
        }
        new = {
            "functions": {
                function_id: _callable("<class 'alpaca.broker.models.Clock'>")
            }
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert breaking == []
        assert narrowed == [
            (
                "get_clock return type narrowed: "
                "None | alpaca.broker.models.Clock -> alpaca.broker.models.Clock",
                [function_id],
            )
        ]

    def test_dropping_list_raw_data_is_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_all_subscriptions"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.List[alpaca.broker.models.rebalancing.Subscription]"
                    " | typing.List[typing.Dict[str, typing.Any]]"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable(
                    "typing.List[alpaca.broker.models.rebalancing.Subscription]"
                )
            }
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert narrowed == []
        assert breaking == [
            (
                "get_all_subscriptions return type changed: "
                "list[alpaca.broker.models.rebalancing.Subscription]"
                " | list[dict[str, Any]]"
                " -> list[alpaca.broker.models.rebalancing.Subscription]",
                [function_id],
            )
        ]

    def test_dropping_none_keeps_list_raw_data_narrowed(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_all_subscriptions"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.List[alpaca.broker.models.rebalancing.Subscription]"
                    " | typing.List[typing.Dict[str, typing.Any]] | None"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable(
                    "typing.List[alpaca.broker.models.rebalancing.Subscription]"
                    " | typing.List[typing.Dict[str, typing.Any]]"
                )
            }
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert breaking == []
        assert narrowed == [
            (
                "get_all_subscriptions return type narrowed: "
                "None | list[alpaca.broker.models.rebalancing.Subscription]"
                " | list[dict[str, Any]]"
                " -> list[alpaca.broker.models.rebalancing.Subscription]"
                " | list[dict[str, Any]]",
                [function_id],
            )
        ]

    def test_dropping_raw_data_is_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_account"
        old = {
            "functions": {
                function_id: _callable(
                    "alpaca.broker.models.accounts.Account"
                    " | typing.Dict[str, typing.Any] | None"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable("alpaca.broker.models.accounts.Account | None")
            }
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert narrowed == []
        assert breaking == [
            (
                "get_account return type changed: "
                "None | alpaca.broker.models.accounts.Account | dict[str, Any] "
                "-> None | alpaca.broker.models.accounts.Account",
                [function_id],
            )
        ]

    def test_subclass_return_is_narrowed(self, cab):
        get_id = "alpaca.broker.client.BrokerClient.get_account_by_id"
        list_id = "alpaca.broker.client.BrokerClient.list_accounts"
        old = {
            "functions": {
                get_id: _callable(
                    "alpaca.broker.models.accounts.Account"
                    " | typing.Dict[str, typing.Any]"
                ),
                list_id: _callable(
                    "typing.List[alpaca.broker.models.accounts.Account]"
                    " | typing.Dict[str, typing.Any]"
                ),
            }
        }
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {
                get_id: _callable(
                    "alpaca.broker.models.accounts.AccountExtended"
                    " | typing.Dict[str, typing.Any]"
                ),
                list_id: _callable(
                    "typing.List[alpaca.broker.models.accounts.AccountExtended]"
                    " | typing.Dict[str, typing.Any]"
                ),
            },
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert breaking == []
        assert narrowed == [
            (
                "get_account_by_id return type narrowed: "
                "alpaca.broker.models.accounts.Account | dict[str, Any] "
                "-> alpaca.broker.models.accounts.AccountExtended | dict[str, Any]",
                [get_id],
            ),
            (
                "list_accounts return type narrowed: "
                "dict[str, Any] | list[alpaca.broker.models.accounts.Account] "
                "-> dict[str, Any] | list[alpaca.broker.models.accounts.AccountExtended]",
                [list_id],
            ),
        ]

    def test_superclass_return_is_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_account_by_id"
        old = {
            "functions": {
                function_id: _callable("alpaca.broker.models.accounts.AccountExtended")
            }
        }
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {
                function_id: _callable("alpaca.broker.models.accounts.Account")
            },
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert narrowed == []
        assert [message for message, _ in breaking] == [
            "get_account_by_id return type changed: "
            "alpaca.broker.models.accounts.AccountExtended "
            "-> alpaca.broker.models.accounts.Account"
        ]

    def test_unrelated_class_return_is_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.list_accounts"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.List[alpaca.broker.models.accounts.Account]"
                )
            }
        }
        new = {
            "classes": _classes(["alpaca.broker.models.accounts.TradeAccount"]),
            "functions": {
                function_id: _callable(
                    "typing.List[alpaca.broker.models.accounts.TradeAccount]"
                )
            },
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert narrowed == []
        assert len(breaking) == 1

    def test_subclass_does_not_hide_dropped_raw_data(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_account_by_id"
        old = {
            "functions": {
                function_id: _callable(
                    "alpaca.broker.models.accounts.Account"
                    " | typing.Dict[str, typing.Any]"
                )
            }
        }
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {
                function_id: _callable("alpaca.broker.models.accounts.AccountExtended")
            },
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert narrowed == []
        assert len(breaking) == 1

    def test_mapping_key_narrowing_is_breaking(self, cab):
        mapping_id = "alpaca.broker.client.BrokerClient.get_by_account"
        dict_id = "alpaca.broker.client.BrokerClient.get_dict_by_account"
        old = {
            "functions": {
                mapping_id: _callable(
                    "typing.Mapping[alpaca.broker.models.accounts.Account, str]"
                ),
                dict_id: _callable(
                    "typing.Dict[alpaca.broker.models.accounts.Account, str]"
                ),
            }
        }
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {
                mapping_id: _callable(
                    "typing.Mapping["
                    "alpaca.broker.models.accounts.AccountExtended, str]"
                ),
                dict_id: _callable(
                    "typing.Dict[alpaca.broker.models.accounts.AccountExtended, str]"
                ),
            },
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert narrowed == []
        assert breaking == [
            (
                "get_by_account return type changed: "
                "collections.abc.Mapping[alpaca.broker.models.accounts.Account, str] "
                "-> collections.abc.Mapping["
                "alpaca.broker.models.accounts.AccountExtended, str]",
                [mapping_id],
            ),
            (
                "get_dict_by_account return type changed: "
                "dict[alpaca.broker.models.accounts.Account, str] "
                "-> dict[alpaca.broker.models.accounts.AccountExtended, str]",
                [dict_id],
            ),
        ]

    def test_mapping_value_narrowing_is_compatible(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_by_account"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.Mapping[str, alpaca.broker.models.accounts.Account]"
                )
            }
        }
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {
                function_id: _callable(
                    "typing.Mapping[str, alpaca.broker.models.accounts.AccountExtended]"
                )
            },
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert breaking == []
        assert narrowed == [
            (
                "get_by_account return type narrowed: "
                "collections.abc.Mapping[str, alpaca.broker.models.accounts.Account] "
                "-> collections.abc.Mapping["
                "str, alpaca.broker.models.accounts.AccountExtended]",
                [function_id],
            )
        ]

    def test_callable_parameters_are_not_covariant(self, cab):
        function_id = "alpaca.data.live.stock.StockDataStream.get_handler"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.Callable[[alpaca.broker.models.accounts.Account], None]"
                )
            }
        }
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {
                function_id: _callable(
                    "typing.Callable"
                    "[[alpaca.broker.models.accounts.AccountExtended], None]"
                )
            },
        }
        breaking, narrowed = cab._compare_return_annotations(old, new)
        assert narrowed == []
        assert len(breaking) == 1

    def test_generator_send_type_is_not_covariant(self, cab):
        function_id = "alpaca.data.live.stock.StockDataStream.stream"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.Generator[int, alpaca.broker.models.accounts.Account, None]"
                )
            }
        }
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {
                function_id: _callable(
                    "typing.Generator"
                    "[int, alpaca.broker.models.accounts.AccountExtended, None]"
                )
            },
        }
        breaking, compatible = cab._compare_return_annotations(old, new)
        assert compatible == []
        assert len(breaking) == 1

    def test_any_return_becoming_concrete_is_narrowed(self, cab):
        function_id = "alpaca.trading.client.TradingClient.get_clock"
        old = {"functions": {function_id: _callable("typing.Any")}}
        new = {"functions": {function_id: _callable("alpaca.trading.models.Clock")}}
        breaking, compatible = cab._compare_return_annotations(old, new)
        assert breaking == []
        assert compatible == [
            (
                "get_clock return type narrowed: Any -> alpaca.trading.models.Clock",
                [function_id],
            )
        ]

    def test_dropping_raw_data_list_inside_iterator_is_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_runs"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.Iterator[typing.List[typing.Dict[str, typing.Any]]"
                    " | typing.List[alpaca.broker.models.rebalancing.RebalancingRun]]"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable(
                    "typing.Iterator"
                    "[typing.List[alpaca.broker.models.rebalancing.RebalancingRun]]"
                )
            }
        }
        breaking, compatible = cab._compare_return_annotations(old, new)
        assert compatible == []
        assert breaking == [
            (
                "get_runs return type changed: collections.abc.Iterator["
                "list[alpaca.broker.models.rebalancing.RebalancingRun]"
                " | list[dict[str, Any]]] -> collections.abc.Iterator["
                "list[alpaca.broker.models.rebalancing.RebalancingRun]]",
                [function_id],
            )
        ]

    def test_dropping_raw_data_inside_list_argument_is_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_runs"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.List[typing.Dict[str, typing.Any]"
                    " | alpaca.broker.models.rebalancing.RebalancingRun]"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable(
                    "typing.List[alpaca.broker.models.rebalancing.RebalancingRun]"
                )
            }
        }
        breaking, compatible = cab._compare_return_annotations(old, new)
        assert compatible == []
        assert len(breaking) == 1

    def test_dropping_none_inside_iterator_keeps_raw_data_narrowed(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_runs"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.Iterator[typing.List[typing.Dict[str, typing.Any]]"
                    " | typing.List[alpaca.broker.models.rebalancing.RebalancingRun]"
                    " | None]"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable(
                    "typing.Iterator[typing.List[typing.Dict[str, typing.Any]]"
                    " | typing.List[alpaca.broker.models.rebalancing.RebalancingRun]]"
                )
            }
        }
        breaking, compatible = cab._compare_return_annotations(old, new)
        assert breaking == []
        assert len(compatible) == 1

    def test_raw_data_value_type_change_is_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_account_by_id"
        old = {
            "functions": {
                function_id: _callable(
                    "alpaca.broker.models.accounts.Account"
                    " | typing.Dict[str, typing.Any]"
                )
            }
        }
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {
                function_id: _callable(
                    "alpaca.broker.models.accounts.Account"
                    " | typing.Dict[str, alpaca.broker.models.accounts.Account]"
                )
            },
        }
        breaking, compatible = cab._compare_return_annotations(old, new)
        assert compatible == []
        assert len(breaking) == 1

    def test_none_return_gaining_a_value_is_compatible(self, cab):
        function_id = (
            "alpaca.broker.client.BrokerClient"
            ".exercise_options_position_for_account_by_id"
        )
        old = {"functions": {function_id: _callable("None")}}
        new = {
            "functions": {
                function_id: _callable(
                    "alpaca.broker.models.trading.OptionExerciseResponse"
                    " | typing.Dict[str, typing.Any] | None"
                )
            }
        }
        breaking, compatible = cab._compare_return_annotations(old, new)
        assert breaking == []
        assert compatible == [
            (
                "exercise_options_position_for_account_by_id return type gained "
                "a value: None -> None"
                " | alpaca.broker.models.trading.OptionExerciseResponse"
                " | dict[str, Any]",
                [function_id],
            )
        ]

    def test_none_return_becoming_unannotated_is_breaking(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.cancel_run_by_id"
        old = {"functions": {function_id: _callable("None")}}
        new = {"functions": {function_id: _callable("")}}
        breaking, compatible = cab._compare_return_annotations(old, new)
        assert compatible == []
        assert breaking == [
            (
                "cancel_run_by_id return type changed: None -> <unannotated>",
                [function_id],
            )
        ]

    def test_already_reported_return_type_is_not_duplicated(self, cab):
        function_id = "alpaca.trading.client.TradingClient.get_clock"
        old = {"functions": {function_id: _callable("Clock")}}
        new = {"functions": {function_id: _callable("ExtendedClock")}}
        reported = cab._reported_return_type_ids(
            [
                {
                    "kind": "ChangeReturnType",
                    "message": f"Change return type ({function_id}): Clock => ExtendedClock",
                    "old": {"id": function_id},
                    "new": {"id": function_id},
                }
            ]
        )
        assert function_id in reported
        assert cab._compare_return_annotations(old, new, already_reported=reported) == (
            [],
            [],
        )

    def test_aexpy_compatible_subclass_is_not_duplicated(self, cab):
        """A rank-0 subclass return stays AexPy's finding, not a second one."""
        function_id = "alpaca.broker.client.BrokerClient.get_account_by_id"
        list_id = "alpaca.broker.client.BrokerClient.list_accounts"
        old = {
            "functions": {
                function_id: _callable("alpaca.broker.models.accounts.Account"),
                list_id: _callable(
                    "typing.List[alpaca.broker.models.accounts.Account]"
                ),
            }
        }
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {
                function_id: _callable("alpaca.broker.models.accounts.AccountExtended"),
                list_id: _callable(
                    "typing.List[alpaca.broker.models.accounts.AccountExtended]"
                ),
            },
        }
        entries = [
            _change_return(function_id, rank=0),
            _change_return(list_id, rank=0),
        ]
        reported = cab._reported_return_type_ids(entries)
        assert cab._compare_return_annotations(
            old,
            new,
            already_reported=reported,
            aexpy_compatible=cab._aexpy_compatible_return_ids(entries),
        ) == ([], [])

    def test_aexpy_compatible_dropped_raw_data_is_breaking(self, cab):
        """A rank-0 return that drops RawData still fails the build.

        AexPy ranks ``Model | RawData`` -> ``Model`` compatible because the new
        return is assignable to the old one. ``raw_data=True`` is a client
        constructor argument, so that ranking is not enough.
        """
        account_id = "alpaca.broker.client.BrokerClient.get_account"
        runs_id = "alpaca.broker.client.BrokerClient.get_runs"
        old = {
            "functions": {
                account_id: _callable(
                    "alpaca.broker.models.accounts.Account"
                    " | typing.Dict[str, typing.Any]"
                ),
                runs_id: _callable(
                    "typing.Iterator[typing.List[typing.Dict[str, typing.Any]]"
                    " | typing.List[alpaca.broker.models.rebalancing.RebalancingRun]]"
                ),
            }
        }
        new = {
            "functions": {
                account_id: _callable("alpaca.broker.models.accounts.Account"),
                runs_id: _callable(
                    "typing.Iterator"
                    "[typing.List[alpaca.broker.models.rebalancing.RebalancingRun]]"
                ),
            }
        }
        entries = [
            _change_return(account_id, rank=0),
            _change_return(runs_id, rank=0),
        ]
        breaking, compatible = cab._compare_return_annotations(
            old,
            new,
            already_reported=cab._reported_return_type_ids(entries),
            aexpy_compatible=cab._aexpy_compatible_return_ids(entries),
        )
        assert compatible == []
        assert breaking == [
            (
                "get_account return type dropped RawData: "
                "alpaca.broker.models.accounts.Account | dict[str, Any] "
                "-> alpaca.broker.models.accounts.Account",
                [account_id],
            ),
            (
                "get_runs return type dropped RawData: collections.abc.Iterator["
                "list[alpaca.broker.models.rebalancing.RebalancingRun]"
                " | list[dict[str, Any]]] -> collections.abc.Iterator["
                "list[alpaca.broker.models.rebalancing.RebalancingRun]]",
                [runs_id],
            ),
        ]

    def test_aexpy_compatible_mapping_key_narrowing_is_breaking(self, cab):
        mapping_id = "alpaca.broker.client.BrokerClient.get_by_account"
        nested_id = "alpaca.broker.client.BrokerClient.list_by_account"
        mutable_id = "alpaca.broker.client.BrokerClient.get_mutable_by_account"
        old = {
            "functions": {
                mapping_id: _callable(
                    "typing.Mapping[alpaca.broker.models.accounts.Account, str]"
                ),
                nested_id: _callable(
                    "typing.List[typing.Dict["
                    "alpaca.broker.models.accounts.Account, str]]"
                ),
                mutable_id: _callable(
                    "typing.MutableMapping["
                    "alpaca.broker.models.accounts.Account, str]"
                ),
            }
        }
        new = {
            "functions": {
                mapping_id: _callable(
                    "typing.Mapping["
                    "alpaca.broker.models.accounts.AccountExtended, str]"
                ),
                nested_id: _callable(
                    "typing.List[typing.Dict["
                    "alpaca.broker.models.accounts.AccountExtended, str]]"
                ),
                mutable_id: _callable(
                    "typing.MutableMapping["
                    "alpaca.broker.models.accounts.AccountExtended, str]"
                ),
            }
        }
        entries = [
            _change_return(mapping_id, rank=0),
            _change_return(nested_id, rank=0),
            _change_return(mutable_id, rank=0),
        ]
        breaking, compatible = cab._compare_return_annotations(
            old,
            new,
            already_reported=cab._reported_return_type_ids(entries),
            aexpy_compatible=cab._aexpy_compatible_return_ids(entries),
        )
        assert compatible == []
        assert breaking == [
            (
                "get_by_account return type changed a mapping key: "
                "collections.abc.Mapping[alpaca.broker.models.accounts.Account, str] "
                "-> collections.abc.Mapping["
                "alpaca.broker.models.accounts.AccountExtended, str]",
                [mapping_id],
            ),
            (
                "get_mutable_by_account return type changed a mapping key: "
                "collections.abc.MutableMapping["
                "alpaca.broker.models.accounts.Account, str] "
                "-> collections.abc.MutableMapping["
                "alpaca.broker.models.accounts.AccountExtended, str]",
                [mutable_id],
            ),
            (
                "list_by_account return type changed a mapping key: "
                "list[dict[alpaca.broker.models.accounts.Account, str]] "
                "-> list[dict[alpaca.broker.models.accounts.AccountExtended, str]]",
                [nested_id],
            ),
        ]

    @pytest.mark.parametrize(
        "wrapper",
        ["list[{}]", "dict[str, {}]", "typing.Callable[[{}], None]"],
    )
    @pytest.mark.parametrize("keep_compatible_arm", [False, True])
    def test_aexpy_mapping_key_change_with_unrelated_union_arm(
        self, cab, wrapper, keep_compatible_arm
    ):
        function_id = "alpaca.broker.client.BrokerClient.get_by_account"
        old_mapping = wrapper.format("typing.Mapping[Base, str]")
        new_mapping = wrapper.format("typing.Mapping[Sub, str]")
        old_annotation = f"{old_mapping} | {wrapper.format('int')}"
        if keep_compatible_arm:
            old_annotation += f" | {new_mapping}"
        old = {"functions": {function_id: _callable(old_annotation)}}
        new = {"functions": {function_id: _callable(new_mapping)}}
        entries = [_change_return(function_id, rank=0)]

        breaking, compatible = cab._compare_return_annotations(
            old,
            new,
            already_reported=cab._reported_return_type_ids(entries),
            aexpy_compatible=cab._aexpy_compatible_return_ids(entries),
        )

        assert compatible == []
        if keep_compatible_arm:
            assert breaking == []
        else:
            assert breaking == [
                (
                    "get_by_account return type changed a mapping key: "
                    f"{cab._normalize_type_annotation(old_annotation)} "
                    f"-> {cab._normalize_type_annotation(new_mapping)}",
                    [function_id],
                )
            ]

    @pytest.mark.parametrize("wrapper", ["{}", "list[{}]"])
    @pytest.mark.parametrize("keep_compatible_arm", [False, True])
    def test_aexpy_mapping_union_with_subclass_value(
        self, cab, wrapper, keep_compatible_arm
    ):
        function_id = "alpaca.broker.client.BrokerClient.get_by_account"
        base, sub = _ACCOUNT_EXTENDED_MRO[1], _ACCOUNT_EXTENDED_MRO[0]
        old_annotation = f"typing.Mapping[{base}, {base}]"
        if keep_compatible_arm:
            old_annotation += f" | typing.Mapping[{sub}, {base}]"
        new_annotation = f"typing.Mapping[{sub}, {sub}]"
        old = {"functions": {function_id: _callable(wrapper.format(old_annotation))}}
        new = {
            "classes": _classes(_ACCOUNT_EXTENDED_MRO),
            "functions": {function_id: _callable(wrapper.format(new_annotation))},
        }
        entries = [_change_return(function_id, rank=0)]

        breaking, compatible = cab._compare_return_annotations(
            old,
            new,
            already_reported=cab._reported_return_type_ids(entries),
            aexpy_compatible=cab._aexpy_compatible_return_ids(entries),
        )

        assert compatible == []
        if keep_compatible_arm:
            assert breaking == []
        else:
            assert len(breaking) == 1
            assert breaking[0][1] == [function_id]

    def test_aexpy_compatible_mapping_value_is_not_duplicated(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_by_account"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.Mapping[str, alpaca.broker.models.accounts.Account]"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable(
                    "typing.Mapping[str, alpaca.broker.models.accounts.AccountExtended]"
                )
            }
        }
        entries = [_change_return(function_id, rank=0)]
        assert cab._compare_return_annotations(
            old,
            new,
            already_reported=cab._reported_return_type_ids(entries),
            aexpy_compatible=cab._aexpy_compatible_return_ids(entries),
        ) == ([], [])

    def test_aexpy_compatible_callable_widening_is_not_overridden(self, cab):
        """Parameter widening is compatible. The key veto must not reject it."""
        function_id = "alpaca.data.live.stock.StockDataStream.get_handler"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.Callable"
                    "[[alpaca.broker.models.accounts.AccountExtended], None]"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable(
                    "typing.Callable[[alpaca.broker.models.accounts.Account], None]"
                )
            }
        }
        entries = [_change_return(function_id, rank=0)]
        assert cab._compare_return_annotations(
            old,
            new,
            already_reported=cab._reported_return_type_ids(entries),
            aexpy_compatible=cab._aexpy_compatible_return_ids(entries),
        ) == ([], [])

    def test_aexpy_breaking_mapping_key_is_not_duplicated(self, cab):
        function_id = "alpaca.broker.client.BrokerClient.get_by_account"
        old = {
            "functions": {
                function_id: _callable(
                    "typing.Mapping[alpaca.broker.models.accounts.Account, str]"
                )
            }
        }
        new = {
            "functions": {
                function_id: _callable(
                    "typing.Mapping["
                    "alpaca.broker.models.accounts.AccountExtended, str]"
                )
            }
        }
        entries = [_change_return(function_id, rank=60)]
        assert cab._aexpy_compatible_return_ids(entries) == set()
        assert cab._compare_return_annotations(
            old,
            new,
            already_reported=cab._reported_return_type_ids(entries),
            aexpy_compatible=cab._aexpy_compatible_return_ids(entries),
        ) == ([], [])
