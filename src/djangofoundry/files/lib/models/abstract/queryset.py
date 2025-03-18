
from __future__ import annotations

from abc import ABC
from decimal import Decimal
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Any, Generic, Iterator, Self

# Django Imports
import django.db.models
from django.db.models import Field, Sum
from djangofoundry import models as foundry
from djangofoundry.helpers import queue
from typing_extensions import TypeVar

# App imports
from lib.models.faker import fake

if TYPE_CHECKING:
    from lib.models.abstract.model import LibModel

_LibModel = TypeVar("_LibModel", bound="LibModel", default="LibModel")
_LibQuerySet = TypeVar("_LibQuerySet", bound='foundry.QuerySet', default='foundry.QuerySet')

class LibQueue(queue.Queue, Generic[_LibModel], ABC):
    pass

class LibQuerySet(foundry.QuerySet, Generic[_LibModel]):
    pass

class LibManager(foundry.Manager, Generic[_LibModel, _LibQuerySet]):

    @singledispatchmethod
    def resolve(self, instance_or_id: Any) -> _LibModel:
        raise TypeError(f"Cannot resolve {instance_or_id=} to an instance of the model. Pass in an integer ID or an instance of the model.")

    @resolve.register
    def _(self, pk: int) -> _LibModel:
        return self.get(pk=pk)

    @resolve.register
    def _(self, instance: django.db.models.Model) -> _LibModel:
        return instance # type: ignore
