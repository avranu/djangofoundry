"""
Assists with registering and calling hooks for arbitrary points in the code.

This allows our software to be modular:
addons can be included which modify core behavior of our software without subclassing or overriding anything.

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

from typing import Any, Callable, Iterable, Optional

from djangofoundry.helpers.hooks.hook import Hook
from djangofoundry.helpers.hooks.meta import DEFAULT_NAMESPACE, DEFAULT_PRIORITY, NamespaceMap
from djangofoundry.helpers.hooks.waypoint import Waypoint


class Hooks:
	"""
	The Hooks class allows registration of modular hooks throughout the application.
	"""

	# A map of hooks in the format: {namespace: {name: list(Callable())}}
	_hooks : NamespaceMap

	@classmethod
	def run(cls, name : str, namespace : str = DEFAULT_NAMESPACE, *args, **kwargs) -> Iterable[Any]:
		"""
		Run any hooks registered to this name and namespace.

		Args:
			name (str, optional):
				The name of the hook
			namespace (str, optional):
				The namespace to search for hooks. defaults to the DEFAULT_NAMESPACE constant.
			*args:
				Positional arguments to pass to the hook
			**kwargs:
				Named arguments to pass to the hook

		Returns:
			Iterable[Any]: Returns a list of all retur values for the hooks run.

		"""
		# Get all hooks that match this criteria
		hooks : list[Hook] = cls.get(name=name, namespace=namespace)

		# Sort the hooks by priority
		hooks.sort(key = lambda x: x.priority, reverse=True)

		# Initialize a list of all return values from each hook run
		results = []

		# Run each one in order
		hook: Hook
		for hook in hooks:
			# Request that it run, if it's able to.
			(did_run, result) = hook.request_run(*args, **kwargs)

			# Record the return value
			if did_run is True:
				results.append(result)

		# Return a list of all return values
		return results

	@classmethod
	def register(cls,
			  name: str,
			  action: Callable,
			  namespace: str = DEFAULT_NAMESPACE,
			  priority : int = DEFAULT_PRIORITY,
			  max_executions: int = -1) -> None:
		"""
		Register a new hook to this name and namespace.

		After being registered, the provided callable will be executed when Hook.run() is called.

		Args:
			name (str):
				The name of the hook
			action (Callable):
				The callable function to execute when this hook is run.
			namespace (str, optional):
				The namespace to search for hooks. defaults to the DEFAULT_NAMESPACE constant.
			priority (int, optional):
				The priority of the hook. Defaults to the DEFAULT_PRIORITY constant
			max_executions (int, optional):
				The maximum number of times this hook should be executed. Defaults to -1 (no maximum).

		Returns:
			None

		"""
		cls._initialize_waypoint(name=name, namespace=namespace)

		# Create a new hook object
		hook = Hook(name=name, namespace=namespace, priority=priority, max_executions=max_executions, action=action)

		# Now that it's guaranteed to be initialized, add it
		cls._hooks[namespace][name].append(hook)


	@classmethod
	def get(cls, name : Optional[str] = None, namespace : str = DEFAULT_NAMESPACE) -> list[Hook]:
		"""
		Get a list of hooks registered to this name and namespace.

		Args:
			name (str, optional):
				The name of the hook
			namespace (str, optional):
				The namespace to search for hooks. defaults to the DEFAULT_NAMESPACE constant.

		Raises:
			ValueError: If a name is specified, but namespace is None

		Note:
			If name is None, get all hooks registered to the entire namespace.
			If name AND namespace are both None, get all hooks registered anywhere.
			If namespace is None, but name is provided, raises a ValueError.

		Returns:
			int: The number of hooks registered to this name and namespace.

		"""
		# Grab all waypoints that match the criteria
		waypoints = cls.get_waypoints(name, namespace)

		# Return all hooks in every waypoint we found.
		return [waypoint.hooks for waypoint in waypoints]


	@classmethod
	def has_waypoint(cls, name: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
		"""
		Returns whether a waypoint exists at the given name and namespace.

		Args:
			name (str):
				The name of the hook
			namespace (str, optional):
				The namespace to search for hooks. defaults to the DEFAULT_NAMESPACE constant.

		Returns:
			bool: True if a waypoint exists here, False if no waypoint can be found with this name/namespace.

		"""
		# No waypoint registered because this name/namespace hasn't been defined.
		if namespace not in cls._hooks or name not in cls._hooks[namespace]:
			return False

		# This name/namespace was defined, but no waypoint is there.
		if cls._hooks[namespace][name] is None:
			return False

		# Passed all checks, so must have found a waypoint here!
		return True


	@classmethod
	def get_waypoint(cls, name: str, namespace: str = DEFAULT_NAMESPACE) -> Waypoint | None:
		"""
		Gets the waypoint at the specified name and namespace.

		Args:
			name (str):
				The name of the hook
			namespace (str, optional):
				The namespace to search for hooks. defaults to the DEFAULT_NAMESPACE constant.

		Returns:
			Waypoint | None: A waypoint, if one was registered. Otherwise None.

		"""
		# No waypoint registered because this name/namespace hasn't been defined.
		if namespace not in cls._hooks or name not in cls._hooks[namespace]:
			return None

		# Return whatever happens to be there (i.e. a Waypoint or None)
		return cls._hooks[namespace][name]


	@classmethod
	def get_waypoints(cls, name: Optional[str] = None, namespace: str = DEFAULT_NAMESPACE) -> Iterable[Waypoint]:
		"""
		Gets all waypoints matching the criteria passed in.

		Args:
			name (str, optional):
				The name of the waypoint. If None, returns all waypoints with any name.
			namespace (str, optional):
				The namespace to search for hooks. defaults to the DEFAULT_NAMESPACE constant.

		Returns:
			Waypoint | None: A waypoint, if one was registered. Otherwise None.

		Raises:
			ValueError: If a name is specified, but namespace is None

		"""
		if namespace is None:
			if name is None:
				# No name or namespace, return all waypoints
				return [names.values() for names in cls._hooks.values()]

			# Name but no namespace, raise an error
			raise ValueError(f'Requesting all waypoints with a name ({name}) but no namespace specified.')

		if name is None:
			# No name, but a namespace. Return all waypoints in that namespace.
			return list(cls._hooks[namespace].values())

		# Both a name and a namespace. Return the single waypoint as a list to match our return type.
		return list(cls._hooks[namespace][name])

	@classmethod
	def count(cls, name : Optional[str] = None, namespace : str = DEFAULT_NAMESPACE) -> int:
		"""
		Counts the number of hooks registered to this name and namespace.

		Args:
			name (str, optional):
				The name of the hook
			namespace (str, optional):
				The namespace to search for hooks.
				To search for hooks with the default namespace, set this to the DEFAULT_NAMESPACE constant.

		Note:
			If name is None, counts all hooks registered to the entire namespace.
			If namespace is None, counts all hooks with the given name in any namespace.
			If name AND namespace are both None, counts all hooks registered anywhere.

		Returns:
			int: The number of hooks registered to this name and namespace.

		"""
		# Allow get() to do the heavy lifting.
		return len(cls.get(name, namespace))

	@classmethod
	def register_waypoint(
			cls,
			name : str,
			namespace : str = DEFAULT_NAMESPACE,
			positional_arguments : int = 0,
			named_arguments : Optional[list[str]] = None,
			return_type : Any = Any,
			hooks : Optional[list[Hook]] = None) -> Waypoint:
		"""
		Creates and registers a new waypoint.
		"""
		if named_arguments is None:
			named_arguments = []
		if hooks is None:
			hooks = []

		# Make sure one doesn't exist first.
		if cls.has_waypoint(name=name, namespace=namespace):
			raise ValueError(f'Waypoint already exists at {namespace}.{name}')

		# Create a new waypoint
		waypoint = Waypoint(name=name,
					  namespace=namespace,
					  positional_arguments=positional_arguments,
					  named_arguments=named_arguments,
					  return_type = return_type,
					  hooks = hooks)

		# Register it
		cls._initialize_waypoint(name, namespace, waypoint)

		return waypoint

	@classmethod
	def _initialize_waypoint(cls, name: Optional[str] = None, namespace: Optional[str] = None, waypoint : Waypoint = None) -> Waypoint:
		"""
		Private method to initialize a hook point.

		This is used to determine what hook points are available to register hooks to.

		TODO: [AUTO-369] Allow initializing metadata details about hook points for documentation

		Args:
			name (str, optional):
				The name of the hook
			namespace (str, optional):
				The namespace to search for hooks. defaults to the DEFAULT_NAMESPACE constant.
			waypoint (Waypoint, optional):
				The waypoint to set at this name/namespace if it does not already exist.
				If waypoint is None, a new waypoint with no extra parameters will be created.

		Returns:
			None

		"""
		if namespace not in cls._hooks:
			# initialize the namespace
			cls._hooks[namespace] = {}

		if name not in cls._hooks[namespace]:
			# initialize the hook name by creating a new waypoint
			if waypoint is not None:
				cls._hooks[namespace][name] = waypoint
			else:
				cls._hooks[namespace][name] = Waypoint(name=name, namespace=namespace)

		# Return whatever waypoint is now there, newly created or otherwise.
		return cls._hooks[namespace][name]


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
