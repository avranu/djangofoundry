
from __future__ import annotations

from abc import ABC
from decimal import Decimal
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Any, Generic, Iterator, Self

from typing_extensions import TypeVar

# App imports
from lib import models

if TYPE_CHECKING:
    from dashboard.models.abstract.model import DashboardModel

_DashboardModel = TypeVar("_DashboardModel", bound="DashboardModel", default="DashboardModel")
_DashboardQuerySet = TypeVar("_DashboardQuerySet", bound='DashboardQuerySet', default='DashboardQuerySet')

class DashboardQueue(models.LibQueue, Generic[_DashboardModel], ABC):
    pass

class DashboardQuerySet(models.LibQuerySet, Generic[_DashboardModel]):
    pass

class DashboardManager(models.LibManager, Generic[_DashboardModel, _DashboardQuerySet]):
    pass
