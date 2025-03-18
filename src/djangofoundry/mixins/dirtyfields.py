"""


Metadata:

File: dirtyfields.py
Project: Django Foundry
Created Date: 23 Aug 2022
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

from typing import Optional

from dirtyfields import DirtyFieldsMixin


class DirtyFields(DirtyFieldsMixin):
	"""
	Tracks changes to a model in order to implement the following methods:
		is_dirty()
		dirty_fields()
		save_dirty_fields()
	"""

	def is_dirty(self, check_relationship: bool = True, check_m2m: Optional[bool] = None) -> bool:
		"""
		Checks if a model is dirty (i.e. if it has been modified since being loaded from the DB)

		Overrides the default implementation to change check_relationship default value to True.

		Args:
			check_relationship (bool):
				Whether to check foreign key relationships (default: True)
			check_m2m (bool, optional):
				Whether to check m2m relationships (default: None)

		Returns:
			bool: True if the model state differs from when it was loaded from the DB. False if it is the same.

		"""
		# Outsource the work to our parent implementation. We only wanted to change the defaults.
		return super().is_dirty(check_relationship=check_relationship, check_m2m=check_m2m)
