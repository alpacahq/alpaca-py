import sys
import warnings
from enum import EnumMeta
from pathlib import Path

# Frames inside the installed package are the SDK, not the caller we want to warn.
_PACKAGE_DIR = Path(__file__).resolve().parent.as_posix()


def _deprecated_member_message(enum_cls, member_name):
    if DeprecatingEnumMeta._building or not member_name:
        return None
    return DeprecatingEnumMeta._deprecations.get(enum_cls, {}).get(member_name)


def _warn_deprecated_member(value):
    """Warn when Pydantic has already built a removed enum member.

    Pydantic validates enums in pydantic-core and does not call ``Enum.__call__``,
    so model parsing would otherwise stay silent. Direct construction still warns
    from the metaclass and does not go through this hook.
    """
    message = _deprecated_member_message(
        value.__class__, getattr(value, "_name_", None)
    )
    if message is not None:
        _warn_at_user_code(message)
    return value


def _is_internal_frame(filename: str) -> bool:
    filename = filename.replace("\\", "/")
    return (
        filename.startswith(_PACKAGE_DIR + "/")
        or "/pydantic" in filename
        or filename.endswith("/enum.py")
    )


def _warn_at_user_code(message: str) -> None:
    """Warn at the first frame outside the SDK and Pydantic."""
    level = 1
    frame = sys._getframe()
    while frame is not None:
        if not _is_internal_frame(frame.f_code.co_filename):
            warnings.warn(message, DeprecationWarning, stacklevel=level)
            return
        level += 1
        frame = frame.f_back
    warnings.warn(message, DeprecationWarning, stacklevel=2)


def _pydantic_core_schema(cls, source_type, handler):
    from pydantic_core import core_schema

    schema = handler(source_type)
    return core_schema.no_info_after_validator_function(_warn_deprecated_member, schema)


class DeprecatingEnumMeta(EnumMeta):
    """Warn when selected enum members are looked up.

    Pass the messages as the ``deprecations`` class argument. That map has to
    live at module level: a dict assigned in the enum class body becomes a
    member on Python 3.10.
    """

    # True while EnumMeta is still building the class. Member lookup during
    # construction must not warn, or importing the enum warns.
    _building = False
    _deprecations: dict = {}

    def __new__(mcs, name, bases, namespace, deprecations=None, **kwargs):
        if deprecations:
            # A function in the class body stays a method. A dict there would
            # become a member on Python 3.10.
            namespace["__get_pydantic_core_schema__"] = classmethod(
                _pydantic_core_schema
            )
        mcs._building = True
        try:
            cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        except BaseException:
            mcs._building = False
            raise
        if deprecations:
            mcs._deprecations[cls] = deprecations
        return cls

    def __init__(cls, name, bases, namespace, deprecations=None, **kwargs):
        try:
            super().__init__(name, bases, namespace, **kwargs)
        finally:
            type(cls)._building = False

    def __getattribute__(cls, name):
        if DeprecatingEnumMeta._building:
            return super().__getattribute__(name)
        message = DeprecatingEnumMeta._deprecations.get(cls, {}).get(name)
        if message is not None:
            warnings.warn(message, DeprecationWarning, stacklevel=2)
        return super().__getattribute__(name)

    def __getitem__(cls, name):
        if not DeprecatingEnumMeta._building:
            message = DeprecatingEnumMeta._deprecations.get(cls, {}).get(name)
            if message is not None:
                warnings.warn(message, DeprecationWarning, stacklevel=2)
        return super().__getitem__(name)

    def __call__(cls, value, *args, **kwargs):
        result = super().__call__(value, *args, **kwargs)
        if DeprecatingEnumMeta._building or not isinstance(result, cls):
            return result
        message = DeprecatingEnumMeta._deprecations.get(cls, {}).get(result._name_)
        if message is not None:
            warnings.warn(message, DeprecationWarning, stacklevel=2)
        return result
