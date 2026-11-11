#!/usr/bin/env python3
"""The public SDK surface, as item ids users can reach.

Items (one id each):

* ``client:<Client>``: a public ``RESTClient`` subclass
* ``method:<Client>.<method>``: a public method of it
* ``param:<Client>.<method>(<name>)``: a parameter of that method
* ``request:<public path>.<field>``: a field of a request model
* ``response:<public path>.<field>``: a field of any other model (responses)

Classes are named by a public import path (such as
``alpaca.data.StockBarsRequest``), not by the module that defines them, so
moving a definition does not change the surface as long as users' imports keep
working. The path comes from the class's own package first (a trading model is
named under ``alpaca.trading`` even though ``alpaca.broker`` re-exports it),
then the shortest one wins.

Run with the SDK to describe on the import path:

  .consumer-venv/bin/python consumer_checks/_surface.py   # the BASELINE release
"""

from __future__ import annotations

import importlib
import importlib.metadata
import inspect
import json
import pkgutil
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Type

ROOT = "alpaca"


@dataclass
class Surface:
    items: Set[str] = field(default_factory=set)
    clients: Dict[str, type] = field(default_factory=dict)
    # Client name -> public method names (not inherited from RESTClient).
    methods: Dict[str, List[str]] = field(default_factory=dict)
    # Model class -> public path, for requests and responses.
    requests: Dict[type, str] = field(default_factory=dict)
    responses: Dict[type, str] = field(default_factory=dict)


def _public_modules() -> List[Any]:
    import alpaca

    modules = [alpaca]
    for info in pkgutil.walk_packages(
        alpaca.__path__, f"{ROOT}.", onerror=lambda _: None
    ):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        modules.append(importlib.import_module(info.name))
    return sorted(modules, key=lambda module: module.__name__)


def _public_classes() -> Dict[type, str]:
    """Every class reachable from a public module, with its public path."""
    paths: Dict[type, str] = {}
    for module in _public_modules():
        for name, value in vars(module).items():
            if name.startswith("_") or not inspect.isclass(value):
                continue
            if not (getattr(value, "__module__", "") or "").startswith(ROOT):
                continue
            path = f"{module.__name__}.{name}"
            current = paths.get(value)
            if current is None or _rank(value, path) < _rank(value, current):
                paths[value] = path
    return paths


def _rank(cls: type, path: str) -> tuple:
    """Paths in the class's own package first, then the shortest."""
    home = ".".join(
        cls.__module__.split(".")[:2]
    )  # alpaca.trading._generated -> alpaca.trading
    return (not path.startswith(home + "."), path.count("."), path)


def _is_request(cls: type) -> bool:
    from alpaca.common.requests import NonEmptyRequest

    if issubclass(cls, NonEmptyRequest):
        return True
    # Models nested inside requests (Weight, UpdatableContact, ...).
    return cls.__module__.endswith(".requests") and not cls.__name__.endswith(
        "Response"
    )


def _model_fields(cls: Type[Any]) -> List[str]:
    names = list(getattr(cls, "model_fields", {}) or {})
    names += list(getattr(cls, "model_computed_fields", {}) or {})
    return names


def collect() -> Surface:
    from pydantic import BaseModel

    from alpaca.common.rest import RESTClient

    surface = Surface()
    inherited = set(dir(RESTClient))
    for cls, path in sorted(_public_classes().items(), key=lambda item: item[1]):
        if issubclass(cls, RESTClient) and cls is not RESTClient:
            client = cls.__name__
            surface.clients[client] = cls
            surface.items.add(f"client:{client}")
            names = sorted(
                name
                for name, member in inspect.getmembers(cls, inspect.isfunction)
                if not name.startswith("_") and name not in inherited
            )
            surface.methods[client] = names
            for name in names:
                surface.items.add(f"method:{client}.{name}")
                for parameter in inspect.signature(
                    getattr(cls, name)
                ).parameters.values():
                    if parameter.name == "self" or parameter.kind in (
                        parameter.VAR_POSITIONAL,
                        parameter.VAR_KEYWORD,
                    ):
                        continue
                    surface.items.add(f"param:{client}.{name}({parameter.name})")
        elif issubclass(cls, BaseModel):
            kind = "request" if _is_request(cls) else "response"
            (surface.requests if kind == "request" else surface.responses)[cls] = path
            for name in _model_fields(cls):
                surface.items.add(f"{kind}:{path}.{name}")
    return surface


def snapshot() -> Dict[str, Any]:
    return {
        "sdk": importlib.metadata.version("alpaca-py"),
        "items": sorted(collect().items),
    }


if __name__ == "__main__":
    json.dump(snapshot(), sys.stdout, indent=1)
    sys.stdout.write("\n")
