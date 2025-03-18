"""

Metadata:

File: mixins.py
Project: Django Foundry
Created Date: 15 Sep 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Fri Dec 02 2022
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann
"""
from __future__ import annotations

import logging
import re

# Generic imports
from typing import Iterable, TypeVar

# Get a logger for logging messages
#
# Set up logging for this module. __name__ includes the namespace (e.g. dashboard.models.cases).
#
# We can adjust logging settings from the namespace down to the module level in project/settings
#
logger = logging.getLogger(__name__)

# A generic type we use in some of our sanitizing methods.
T = TypeVar('T')

class HasParams:
	"""
	A mixin for Controllers to handle parameters passed in via url.

	This is used on several extensions of base django controllers, as well as django rest api viewsets.

	Attributes:
		kwargs (Iterable[dict]):
			The (unsanitized) parameters passed to us via url.
			NOTE: This is defined by django controllers and overrides our definition. We include it here only for standalone type checking purposes.

	"""

	kwargs: Iterable[dict]

	def get_param(self, name : str, sanitize : bool = True, required : bool = False) -> str | None:
		"""
		Convenience method for accessing self.kwargs[] to rerieve data passed in the url.

		Attributes:
			name (str):
				The name of the parameter
			sanitize (bool):
				If False, return the user input unmodified. Otherwise, sanitize the user input (default).
			required (bool):
				If true, we will throw an exception if the parameter is missing. If false, we return null for missing parameters.

		Returns:
			str: The value of the parameter, or None if not found.

		Raises:
			ReferenceError: If the parameter is missing and required is True.

		"""
		# If it's found, then return it.
		if name in self.kwargs:
			if sanitize is False:
				# Return it unsanitized
				logger.warning(f'Returning user input {name} unsanitized.')
				return self.kwargs[name]
			
			# Unless explicitly False, return a sanitized string.
			return self.sanitize_str(self.kwargs[name])

		# Not found, determine what to do...
		if required is True:
			raise ReferenceError(f"Required param {name} is missing.")

		return None

	def get_required_param(self, name : str, sanitize : bool = True) -> str:
		"""
		Retrieves data passed in the url.

		Convenience method for accessing get_param(name,True) and ensuring the return value is a str.

		Attributes:
			name (str):
				The name of the parameter
			sanitize (bool):
				If False, return the user input unmodified. Otherwise, sanitize the user input (default).

		Returns:
			str: The value of the parameter

		Raises:
			ReferenceError: If the parameter is missing
			TypeError: If the parameter is found but is None

		"""
		value = self.get_param(name, sanitize=sanitize, required=True)

		# This should never happen, because required=True should throw a ReferenceError if the value is null.
		# This check is here for future proofing.
		if value is None:
			raise TypeError(f"Internal error: required param {name} is None.")

		# Always a str
		return value

	def sanitize_str(self, value : str) -> str:
		"""
		Accepts a string passed by the user, and strips any special characters from it.

		This is handled by django in the url, but we do it here as well to future proof against unexpected changes.

		If no sanitizing is done at all (by django or by us), it could conceievably open us up to injection attacks.

		Args:
			value (str): The value of the string to sanitize.

		Returns:
			str: The sanitized value.

		"""
		# Remove any character besides letters, numbers, and an underscore/comma, then truncate to a max of 500 characters.
		return re.sub(r'[^a-zA-Z0-9_,-]+', '', value)[:500]

	def sanitize_int(self, value : str) -> int:
		"""
		Accepts a string passed by the user, and converts it safely to an integer.

		This is handled by django in the url, but we do it here as well to future proof against unexpected changes.

		If no sanitizing is done at all (by django or by us), it could conceievably open us up to injection attacks.

		Args:
			value (str): The value of the user input string to sanitize.

		Returns:
			int: The sanitized value as an int

		"""
		# Strip any non-numeric characters from the value
		result = re.sub(r'[^0-9]+', '', value)

		# Convert to an int and return
		return int(result)

	def sanitize(self, value : str, param_type : T = str) -> T:
		"""
		Accepts a string passed by the user, and converts it safely to a supported type.

		This is handled by django in the url, but we do it here as well to future proof against unexpected changes.

		If no sanitizing is done at all (by django or by us), it could conceievably open us up to injection attacks.

		Args:
			value (str):
				The value of the user input string to sanitize.
			param_type (str|int):
				A variable type. This function currently supports string and int.

		Returns:
			str | int: The sanitized value

		Raises:
			ValueError: If param_type is not a supported type.

		"""
		match param_type:
			case str():
				return self.sanitize_str(value)
			case int():
				return self.sanitize_int(value)

		raise ValueError(f"Unsupported type {T}")
