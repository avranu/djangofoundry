"""
Represents a hook waypoint, which is a place in our code where a hook can be registered and run.

Metadata:

File: waypoint.py
Project: Django Foundry
Created Date: 02 Sep 2022
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

from typing import TYPE_CHECKING, Any, Iterable

from djangofoundry.helpers.hooks.meta.constants import DEFAULT_NAMESPACE

if TYPE_CHECKING:
	from djangofoundry.helpers.hooks.hook import Hook

class Waypoint:
	"""
	A waypoint is a place in our code where a hook can be registered and run.

	Attributes:
		name (str):
			The name of the hook waypoint (i.e. "person.save.after")
		namespace (str):
			The namespace this waypoint resides in (i.e. "dashboard")
		positional_arguments (int):
			The number of positional arguments hooks must accept at this waypoint
		named_arguments (list[str]):
			A list of named arguments that hooks must accept at this waypoint.
		return_type (Type):
			The type that all hooks at this waypoint return when they are run.
		hooks (list[Hook]):
			The list of hooks registered at this waypoint.

	"""

	name : str
	namespace : str
	positional_arguments : int
	named_arguments : list[str]
	return_type : Any
	hooks : list[Hook]

	def __init__(self,
			name : str,
			namespace : str = DEFAULT_NAMESPACE,
			positional_arguments : int = 0,
			named_arguments : list[str] = list,
			return_type : Any = Any,
			hooks : list[Hook] = list):
		self.name = name
		self.namespace = namespace
		self.positional_arguments = positional_arguments
		self.named_arguments = named_arguments
		self.return_type = return_type
		self.hooks = hooks

		# Sanity checks
		if positional_arguments < 0:
			raise ValueError(f'Invalid number of position_arguments: {positional_arguments}')

	def run(self, *args, **kwargs) -> Iterable[Any]:
		"""
		Run any hooks registered to this waypoint.

		Args:
			*args:
				Position arguments to pass on to the hook
			**kwargs:
				Named arguments to pass on to the hook

		Returns:
			Iterable[Any]:
				Returns a list of all return values for the hooks run.
				This will actually be an iterable of self.return_type, but we can't typehint based on variables passed in during init.

		"""
		# Sort the hooks by priority
		self.hooks.sort(key = lambda x: x.priority, reverse=True)

		# Initialize a list of all return values from each hook run
		results = []

		# Run each one in order
		hook: Hook
		for hook in self.hooks:
			# Request that it run, if it's able to.
			(did_run, result) = hook.request_run(*args, **kwargs)

			# Record the return value
			if did_run is True:
				results.append(result)

		# Return a list of all return values
		return results
