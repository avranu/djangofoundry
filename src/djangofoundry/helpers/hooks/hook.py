"""
The Hook class is responsible for storing data about hooks that we've registered.

Metadata:

File: hooks.py
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

from typing import Any, Callable, Tuple

from djangofoundry.helpers.hooks.meta import DEFAULT_NAMESPACE, DEFAULT_PRIORITY


class Hook:
	"""
	A container for data about a registered hook
	"""

	namespace : str
	name : str
	action : Callable
	priority : int
	max_executions : int
	_executions : int = 0

	@property
	def executions(self):
		"""
		Indicates the number of times this hook has been run.

		Represented as a property to discourage editing the executions variable.
		"""
		return self._executions

	def __init__(self,
			  name : str,
			  action : Callable,
			  namespace : str = DEFAULT_NAMESPACE,
			  priority : int = DEFAULT_PRIORITY,
			  max_executions : int = -1):
		"""
		Args:
			name (str):
				The name of the hook
			action (Callable):
				The action to perform when the hook is run.
			namespace (str):
				The namespace of the hook (defaults to the DEFAULT_NAMESPACE constant)
			priority (int):
				The priority of the hook (defaults to the DEFAULT_PRIORITY constant).
				Hooks execute in the order of their priority.
				Lower priorities will execute first.
			max_executions (int):
				The maximum number of times this hook can be run. Defaults to -1 (no maximum)

		"""
		self.namespace = namespace
		self.name = name
		self.action = action
		self.max_executions = max_executions
		self.priority = priority

		# Sanity checking
		if not max_executions:
			raise ValueError('Hook created with 0 maximum executions, so will never run.')

	def can_run(self) -> bool:
		"""
		Determines if this hook is allowed to run.

		This is determined by checking the number of executions against max_executions.

		Examples:
			>>> hook = Hook('test', lambda: 1, max_executions = 1)
			>>> hook.run()
			>>> hook.run()
			Traceback (most recent call last):
			...
			MaxExecutionsError: Hook application.test has already been run 1 times.

		"""
		return self.executions < self.max_executions > -1

	def run(self, *args, **kwargs) -> Tuple[bool, Any]:
		"""
		Request that the hook action be run if it is allowed to.

		Args:
			*args:
				Any positional arguments to pass to the action
			**kwargs:
				Any keyword arguments to pass to the action

		Returns:
			(bool, Any): Returns a boolean to indicate whether the action run, and the return value of the action (or None)

		"""
		# Check if we're allowed to run
		if self.can_run() is False:
			return (False, None)

		# Run the action and capture its return value
		result = self.action(*args, **kwargs)
		# Indicate we ran and pass the result back
		return (True, result)

	def force_run(self, *args, **kwargs) -> Any:
		"""
		Runs this hook action with the provided arguments, regardless of max_executions.

		This is not the standard way of running a hook. Most hooks are run with Hook.request_run().

		Args:
			*args:
				Any positional arguments to pass to the action
			**kwargs:
				Any keyword arguments to pass to the action

		Returns:
			Any: Hooks may define their own return values

		"""
		# Increase the executions (perhaps beyond the max)
		self._executions += 1

		# Return whatever the hook action says to return
		return self.action(*args, **kwargs)


if __name__ == "__main__":
	"""
	This code is only called if this module is executed directly (i.e. outside of django)

	Its purpose is to run basic unit tests to ensure the module operates the way we intend it to.
	"""
	# Import the doctest module, which runs tests based on Examples in our comments.
	import doctest

	# Run every test we can find in our comments.
	# No output means success.
	doctest.testmod()
