"""

Metadata:

File: exceptions.py
Project: Django Foundry
Created Date: 13 Dec 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Sat Dec 17 2022
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann
"""
from __future__ import annotations

from django.core import exceptions

from djangofoundry.exceptions import AppException


class DoesNotExist(exceptions.ObjectDoesNotExist, AppException):
	"""
	Occurs when a model that should have exactly 1 result in the DB does not exist.
	"""

class NotUnique(exceptions.MultipleObjectsReturned, AppException):
	"""
	Occurs when a model that should have exactly 1 result in the DB has more than 1.
	"""
