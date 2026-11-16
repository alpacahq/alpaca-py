"""Deprecations must be visible to type checkers and warn at runtime.

PEP 702 type checkers only recognise ``@deprecated(...)`` written on the class with a
string literal message. A deprecation applied inside a helper, or with a computed
message, still works at runtime but is invisible to them.

Deprecated models also need ``@_warn_on_direct_instantiation`` for the runtime
warning: ``@deprecated`` on a model is declared with ``category=None`` so it does not
warn when a subclass is declared, and the wrapper stays silent while a client builds
the model from an API response.

Messages follow CONTRIBUTING: a renamed class says "X is deprecated and will be
removed in a future version. Please use `Y` instead.", a compatibility shape starts
with the shape sentence, and the docstring carries a ``.. deprecated::`` line.
"""

import ast
import importlib
import re
from pathlib import Path

import pytest
from pydantic import BaseModel

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

# Modules whose deprecations are declared with literal decorators. Add a module once
# its classes follow the rule.
MODULES = [
    "alpaca/trading/enums.py",
    "alpaca/trading/models.py",
    "alpaca/data/enums.py",
    "alpaca/broker/enums.py",
]

DEPRECATED_NAMES = {"deprecated", "_deprecated"}
WARN_NAMES = {"warn_on_direct_instantiation", "_warn_on_direct_instantiation"}

RENAMED_MESSAGE = re.compile(
    r"^(?P<name>\w+) is deprecated and will be removed in a future version\. "
    r"Please use `\w+`"
)
SHAPE_MESSAGE = re.compile(
    r"^(?P<name>\w+) is a temporary compatibility shape and will be replaced by the "
    r"OpenAPI-generated (?P=name) in a future release\."
)


def _decorator_name(decorator: ast.expr) -> str:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(target, ast.Attribute):
        return target.attr
    return getattr(target, "id", "")


def _literal_argument(node: ast.ClassDef, names: set):
    for decorator in node.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and _decorator_name(decorator) in names
            and decorator.args
            and isinstance(decorator.args[0], ast.Constant)
            and isinstance(decorator.args[0].value, str)
        ):
            return decorator.args[0].value
    return None


def _deprecated_classes(path):
    module = importlib.import_module(path[: -len(".py")].replace("/", "."))
    tree = ast.parse((REPOSITORY_ROOT / path).read_text())
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        cls = getattr(module, node.name)
        message = cls.__dict__.get("__deprecated__")
        if message is not None:
            yield node, cls, message


@pytest.mark.parametrize("path", MODULES)
def test_deprecated_classes_use_a_literal_deprecated_decorator(path):
    for node, _, message in _deprecated_classes(path):
        assert _literal_argument(node, DEPRECATED_NAMES) == message, (
            f"{path}: {node.name} must be decorated with @_deprecated and a string "
            "literal message so type checkers see the deprecation"
        )


@pytest.mark.parametrize("path", MODULES)
def test_deprecated_models_warn_on_direct_instantiation(path):
    for node, cls, message in _deprecated_classes(path):
        if not issubclass(cls, BaseModel):
            continue
        assert _literal_argument(node, WARN_NAMES) == message, (
            f"{path}: {node.name} must also be decorated with "
            "@_warn_on_direct_instantiation and the same message so it warns at runtime"
        )


@pytest.mark.parametrize("path", MODULES)
def test_deprecation_messages_follow_the_template(path):
    for node, _, message in _deprecated_classes(path):
        match = RENAMED_MESSAGE.match(message) or SHAPE_MESSAGE.match(message)
        assert match and match.group("name") == node.name, (
            f"{path}: {node.name} has a deprecation message that does not follow the "
            f"CONTRIBUTING template: {message!r}"
        )


@pytest.mark.parametrize("path", MODULES)
def test_deprecated_classes_document_the_deprecation(path):
    for node, _, _ in _deprecated_classes(path):
        assert ".. deprecated::" in (
            ast.get_docstring(node) or ""
        ), f"{path}: {node.name} needs a `.. deprecated::` line in its docstring"
