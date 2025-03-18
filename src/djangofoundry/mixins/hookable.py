"""


Metadata:

File: hookable.py
Project: Django Foundry
Created Date: 10 Aug 2022
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

from typing import Any


class Hookable:
	"""
	An abstract class that allows subclasses to hook into methods of this class without overriding them.
	"""

	@classmethod
	def hook(cls, name: str, **kwargs) -> None:
		"""
		Implemented by subclasses to hook into methods of this class without overriding them.
		TODO: Signals
		"""
		# By default, do nothing
		return

	@classmethod
	def hook_filter(cls, name: str, value: Any, **kwargs) -> Any:
		"""
		Implemented by subclasses to filter a variable (much like a hook) without overriding this class' methods
		"""
		# By default, return the unfiltered value
		return value
