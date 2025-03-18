"""

Metadata:

File: manager.py
Project: Django Foundry
Created Date: 18 Aug 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Sat Dec 03 2022
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann
"""
# Generic imports
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

# Django extensions
import auto_prefetch

# App Imports

if TYPE_CHECKING:
	from django.db.models import QuerySet

class Manager(auto_prefetch.Manager):
	"""
	A custom query manager. This creates QuerySets and is used in all models interacting with the db.
	"""

	@classmethod
	def from_queryset(cls, queryset_class : type[QuerySet], class_name : Optional[str] = None) -> Manager:
		"""
		Override the default from_queryset method to use our custom QuerySet class.
		"""
		return super().from_queryset(queryset_class)
