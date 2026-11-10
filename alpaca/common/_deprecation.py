"""Helpers for compatibility types that are deprecated by a generated replacement."""

from contextvars import ContextVar
from functools import wraps
from typing import Annotated, Any, Mapping, TypeVar, Union
import warnings

from pydantic import Field
from typing_extensions import deprecated

_T = TypeVar("_T", bound=type)
_M = TypeVar("_M")
_Legacy = TypeVar("_Legacy")
_Generated = TypeVar("_Generated")

# The type of a field that nests a deprecated class: ``LegacyFirst[Old, Replacement]``
# also accepts the generated replacement. Validation tries the deprecated class
# first, so API payloads keep parsing into it even if a regenerated replacement gains
# fields; instances of either class are kept as they are, and payloads only the
# replacement accepts fall back to it.
LegacyFirst = Annotated[Union[_Legacy, _Generated], Field(union_mode="left_to_right")]

# Set while an SDK client builds a model from an API response. The caller cannot
# choose the returned type, so the direct-instantiation warning is not actionable.
_BUILDING_FROM_RESPONSE: ContextVar[bool] = ContextVar(
    "alpaca_building_from_response", default=False
)


def build_from_response(cls: "type[_M]", data: Mapping[str, Any]) -> _M:
    """Build ``cls`` from an API response through its normal ``__init__``.

    Compatibility shapes warn when users instantiate them directly. Clients use this
    helper so returning a shape stays silent, while custom ``__init__`` logic (such
    as Calendar's time parsing) still runs.
    """
    token = _BUILDING_FROM_RESPONSE.set(True)
    try:
        return cls(**data)
    finally:
        _BUILDING_FROM_RESPONSE.reset(token)


def compatibility_shape_message(name: str) -> str:
    """Deprecation text for a same-name legacy type awaiting its generated twin."""
    return (
        f"{name} is a temporary compatibility shape and will be replaced "
        f"by the OpenAPI-generated {name} in a future release."
    )


def deprecate_compatibility_shape(cls: _T) -> _T:
    """Mark a hand-written public type that shares a name with a generated replacement.

    These keep the pre-codegen field/types for one release window, then flip to the
    generated class under the same public name.

    Not for enums: enum lookup never calls ``__init__``, so nothing would warn, and an
    enum shape deprecates only the members its generated twin lacks.
    """
    message = compatibility_shape_message(cls.__name__)
    return warn_on_direct_instantiation(message)(
        deprecated(message, category=None)(cls)
    )


def warn_on_direct_instantiation(message: str):
    """Warn when the decorated compatibility class itself is instantiated.

    Unlike ``typing_extensions.deprecated``, this does not warn when a subclass is
    declared. That distinction matters for compatibility bases such as OrderRequest,
    which still have public subclasses during the deprecation window.
    """

    def decorate(cls: _T) -> _T:
        original_init = cls.__init__

        @wraps(original_init)
        def warned_init(self, *args, **kwargs):
            if type(self) is cls and not _BUILDING_FROM_RESPONSE.get():
                warnings.warn(message, DeprecationWarning, stacklevel=2)
            original_init(self, *args, **kwargs)

        cls.__init__ = warned_init
        return cls

    return decorate
