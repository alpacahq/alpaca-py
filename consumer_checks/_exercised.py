"""What the scenarios exercise of the public surface, observed while they run.

While active, every public client method is wrapped. When a scenario calls one
(not when a public method calls another internally), the collector records:

* ``method:`` and ``param:`` items for the method and the arguments passed;
* ``request:`` items for the fields set (``model_fields_set``) on the request
  models among them, nested ones included;
* ``response:`` items for the fields holding a value other than ``None`` in
  the models returned, nested ones included, also when they come page by page
  from an iterator.

A field counts for every public class in the model's MRO that declares it, so
setting ``page_token`` on ``StockBarsRequest`` also exercises
``BaseTimeseriesDataRequest.page_token``.
"""

from __future__ import annotations

import functools
import inspect
import warnings
from collections.abc import Iterator as IteratorABC
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Set, Tuple

from pydantic import BaseModel

from _surface import Surface


class Collector:
    def __init__(self, surface: Surface) -> None:
        self.surface = surface
        self.exercised: Set[str] = set()
        self._depth = 0

    @contextmanager
    def active(self) -> Iterator[None]:
        patched: List[Tuple[type, str, bool, Any]] = []
        for client, cls in self.surface.clients.items():
            for name in self.surface.methods.get(client, []):
                own = name in cls.__dict__
                original = getattr(cls, name)
                setattr(cls, name, self._wrap(client, name, original))
                patched.append((cls, name, own, original))
        try:
            yield
        finally:
            for cls, name, own, original in reversed(patched):
                if own:
                    setattr(cls, name, original)
                else:
                    delattr(cls, name)

    def _wrap(self, client: str, name: str, original: Any) -> Any:
        signature = inspect.signature(original)
        collector = self

        @functools.wraps(original)
        def wrapper(instance, *args, **kwargs):
            if collector._depth:
                return original(instance, *args, **kwargs)
            collector._depth += 1
            try:
                collector._record_call(client, name, signature, instance, args, kwargs)
                result = original(instance, *args, **kwargs)
            finally:
                collector._depth -= 1
            return collector._observe(result)

        return wrapper

    def _record_call(self, client, name, signature, instance, args, kwargs) -> None:
        self.exercised.add(f"client:{client}")
        self.exercised.add(f"method:{client}.{name}")
        try:
            bound = signature.bind(instance, *args, **kwargs)
        except TypeError:
            return  # the SDK reports the bad call itself
        for parameter, value in bound.arguments.items():
            if parameter == "self":
                continue
            self.exercised.add(f"param:{client}.{name}({parameter})")
            self._walk_request(value, set())

    def _walk_request(self, value: Any, seen: Set[int]) -> None:
        if id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, BaseModel):
            names = value.model_fields_set
            for cls in type(value).__mro__:
                path = self.surface.requests.get(cls)
                declared = getattr(cls, "model_fields", None) or {}
                if path:
                    for field_name in names & set(declared):
                        self.exercised.add(f"request:{path}.{field_name}")
            for field_name in names:
                self._walk_request(getattr(value, field_name, None), seen)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                self._walk_request(item, seen)
        elif isinstance(value, dict):
            for item in value.values():
                self._walk_request(item, seen)

    def _observe(self, result: Any) -> Any:
        # A lazy iterator of pages: observe each page as the scenario takes it.
        if isinstance(result, IteratorABC) and not isinstance(
            result, (BaseModel, dict, list, str, bytes)
        ):
            return self._observe_pages(result)
        self._walk_response(result, set())
        return result

    def _observe_pages(self, pages: Iterator[Any]) -> Iterator[Any]:
        for page in pages:
            self._walk_response(page, set())
            yield page

    def _walk_response(self, value: Any, seen: Set[int]) -> None:
        if value is None or id(value) in seen:
            return
        seen.add(id(value))
        if isinstance(value, BaseModel):
            with warnings.catch_warnings():
                # Deprecated fields are read too; their warnings are noise here.
                warnings.simplefilter("ignore", DeprecationWarning)
                values: Dict[str, Any] = {}
                for cls in type(value).__mro__:
                    path = self.surface.responses.get(cls)
                    if not path:
                        continue
                    names = list(getattr(cls, "model_fields", None) or {})
                    names += list(getattr(cls, "model_computed_fields", None) or {})
                    for field_name in names:
                        if field_name not in values:
                            values[field_name] = getattr(value, field_name, None)
                        if values[field_name] is not None:
                            self.exercised.add(f"response:{path}.{field_name}")
            for item in values.values():
                self._walk_response(item, seen)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                self._walk_response(item, seen)
        elif isinstance(value, dict):
            for item in value.values():
                self._walk_response(item, seen)
