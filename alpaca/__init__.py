# placeholder for poetry-dynamic-versioning
__version__ = "0.0.0"

from alpaca._version_resolve import resolve_version as _resolve_version

__version__ = _resolve_version(__version__)
del _resolve_version
globals().pop("_version_resolve", None)

__all__ = ["__version__"]
