"""Helpers for compatibility types that are deprecated by a generated replacement."""

from contextvars import ContextVar
from functools import wraps
from typing import Any, Mapping, TypeVar
import warnings

_T = TypeVar("_T", bound=type)
_M = TypeVar("_M")

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


def warn_on_direct_instantiation(message: str):
    """Warn when the decorated compatibility class itself is instantiated.

    Unlike ``typing_extensions.deprecated``, this does not warn when a subclass is
    declared. That distinction matters for compatibility bases such as OrderRequest,
    which still have public subclasses during the deprecation window.

    This only provides the runtime warning. Type checkers (PEP 702) do not execute
    decorator helpers, so apply a literal ``@deprecated(message, category=None)``
    directly on each public class as well, with the same message::

        @deprecated(MESSAGE, category=None)
        @warn_on_direct_instantiation(MESSAGE)
        class CreateWatchlistRequest: ...

    Not for enums: enum lookup never calls ``__init__``, so nothing would warn, and an
    enum shape deprecates only the members its generated twin lacks.
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
