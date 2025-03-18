"""


Metadata:

File: queryset_filter.py
Project: Django Foundry
Created Date: 05 Aug 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Sun Apr 16 2023
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann

"""
# Generic imports
from __future__ import annotations

from typing import Callable, Optional

from djangofoundry.models import QuerySet


class Queryset_Filter:
	"""
	A decorator for registering queryset filters
	"""

	# The Queryset method we're wrapping
	filter_fn : Callable
	# The Queryset object
	queryset : QuerySet

	def __init__(self, filter_fn : Callable, name : Optional[str] = None):
		"""
		Setup the decorator
		"""
		# Record the method we're wrapping for later
		self.filter_fn = filter_fn

		# Default the name to the name of the method
		if name is None:
			name = filter_fn.__name__

		# Store it for later
		self.name = name

	def __set_name__(self, owner : QuerySet, name : str):
		# Error handling for decorating the wrong objects
		try:
			# Add the filter name to the filters list
			# TODO: [AUTO-349] We have a bug here. Owner is (apparently) referring to the base QuerySet class and not the top-most child class... causing filters from one model to apply to another.
			owner.filters[self.name] = self.filter_fn
		except Exception as err:
			# If we get any exceptions adding the filter, then the object is not an instance of our custom QuerySet
			raise AttributeError('Queryset_Filter called on object with no filters property') from err

		# Make sure to do the job of __set_name__
		#super().__set_name__(owner, name)
		setattr(owner, name, self.filter_fn)

		self.queryset = owner

	def __get__(self, instance, owner):
		# Record the queryset obj for later use
		self.queryset = instance
		return self.__call__

	def __call__(self, *args, **kwargs):
		"""
		Call the filter we're wrapping
		"""
		# Store the result and pass whatever params we receive
		result = self.filter_fn(*args, **kwargs)
		# Return the result from the filter
		return result
