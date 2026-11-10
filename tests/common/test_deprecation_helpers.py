import warnings

import pytest

from alpaca.common._deprecation import (
    build_from_response,
    compatibility_shape_message,
    deprecate_compatibility_shape,
    warn_on_direct_instantiation,
)


@warn_on_direct_instantiation("Legacy is deprecated; use Replacement instead.")
class Legacy:
    def __init__(self, value: int = 0) -> None:
        self.value = value * 2


class LegacySubclass(Legacy):
    pass


@deprecate_compatibility_shape
class Shape:
    def __init__(self, value: int = 0) -> None:
        self.value = value


def test_direct_instantiation_warns():
    with pytest.warns(DeprecationWarning, match="Legacy is deprecated"):
        Legacy(1)


def test_subclass_instantiation_is_silent():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        assert LegacySubclass(1).value == 2


def test_build_from_response_is_silent_and_runs_init():
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        assert build_from_response(Legacy, {"value": 3}).value == 6


def test_build_from_response_resets_after_init_fails():
    with pytest.raises(TypeError):
        build_from_response(Legacy, {"unknown": 1})

    with pytest.warns(DeprecationWarning, match="Legacy is deprecated"):
        Legacy()


def test_compatibility_shape_warns_with_shape_message():
    with pytest.warns(DeprecationWarning) as record:
        Shape(1)

    assert [str(warning.message) for warning in record] == [
        compatibility_shape_message("Shape")
    ]


def test_compatibility_shape_is_flagged_for_type_checkers():
    assert Shape.__deprecated__ == compatibility_shape_message("Shape")
