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
