"""
Metadata:

File: char.py
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

# Django Imports
from django.db import models

# Lib Imports
# App Imports

class CharField(models.CharField):
	"""
	Override the default django field
	"""

class TextField(models.TextField):
	"""
	Override the default django field
	"""

class OneCharField(CharField):
	"""
	A single character string field.
	"""

	def __init__(self, *, max_length: int = 1, **kwargs):
		if max_length > 1:
			raise ValueError(f'Trying to initialize a single character field with a length of {max_length}')

		super().__init__(max_length=max_length, **kwargs)


class RowIdField(CharField):
	"""
	A charfield that is used for storing row ids (from databases like Oracle)
	"""

	def __init__(self, *,
				 max_length : int = 18,
				 unique	 : bool = True,
				 null	   : bool = False,
				 blank	  : bool = False,
				 editable   : bool = False,
				 **kwargs):
		# Call the parent init function first
		super().__init__(max_length 	 = max_length,
								unique	 = unique,
								null	 = null,
								blank 	 = blank,
								editable = editable,
								**kwargs)

class GuidField(CharField):
	"""
	A charfield that is used for storing GUIDs (UUID v4)
	"""

	def __init__(self, *,
				 max_length : int 	= 38,
				 unique	 : bool 	= True,
				 null : bool 		= False,
				 blank : bool 		= False,
				 editable : bool 	= False,
				 **kwargs):
		"""
		Redefine init to only accept named args
		"""
		# Call the parent init function first
		super().__init__(max_length		 = max_length,
								unique	 = unique,
								null	 = null,
								blank	 = blank,
								editable = editable,
								**kwargs)
