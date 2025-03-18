"""


Metadata:

File: date.py
Project: Django Foundry
Created Date: 18 Aug 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Wed Apr 26 2023
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

class DateField(models.DateField):
	"""
	Override the default django field
	"""

class DateGroupField(models.JSONField):
	"""
	Accepts a single date, or a list of dates, or a range of dates, stored in a json field.
	"""

class DateTimeField(models.DateTimeField):
	"""
	Override the default django field
	"""

class InsertedNowField(DateTimeField):
	"""
	Override the default django field to customize typical init options
	"""

	def __init__(self, *_args, **kwargs):
		# Set auto_now_add, null, and blank within kwargs
		kwargs['auto_now_add'] = True
		kwargs['null'] = False
		kwargs['blank'] = False

		super().__init__(**kwargs)


class UpdatedNowField(DateTimeField):
	"""
	Override the default django field to customize typical init options
	"""

	def __init__(self, *_args, **kwargs):
		# Set auto_now_add, null, and blank within kwargs
		kwargs['auto_now'] = True
		kwargs['null'] = False
		kwargs['blank'] = False

		super().__init__(**kwargs)
