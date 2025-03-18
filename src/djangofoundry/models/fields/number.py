"""


Metadata:

File: number.py
Project: Django Foundry
Created Date: 18 Aug 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Thu Apr 27 2023
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


class IntegerField(models.IntegerField):
	"""
	Override the default django field
	"""

class PositiveIntegerField(models.PositiveIntegerField):
	"""
	Override the default django field
	"""

class BigIntegerField(models.BigIntegerField):
	"""
	Override the default django field
	"""

class DecimalField(models.DecimalField):
	"""
	Override the default django field
	"""

class CurrencyField(DecimalField):
	"""
	Represents currency
	"""

class FloatField(models.FloatField):
	"""
	Override the default django field
	"""
