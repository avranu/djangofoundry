"""
This module defines custom exceptions used by our hook classes.

Metadata:

File: exceptions.py
Project: Django Foundry
Created Date: 02 Sep 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Sat Dec 17 2022
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann
"""
# Generic imports
from __future__ import annotations

from djangofoundry.exceptions import AppException


class MaxExecutionsError(AppException):
	"""
	Indicates an action has already been executed the maximum number of times.
	"""
