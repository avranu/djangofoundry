"""

Metadata:

File: queue.py
Project: Django Foundry
Created Date: 09 Aug 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Thu Apr 13 2023
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann
"""
# Generic imports
from __future__ import annotations

import queue
from collections import deque
from typing import Any, Callable, Optional

from psqlextra.query import ConflictAction
from typing_extensions import Self

# Django Imports
# Lib Imports
from djangofoundry.helpers.queue import signals
from djangofoundry.models import Model
from djangofoundry.models.choices import TextChoices

# App Imports

class Callbacks(TextChoices):
	"""
	Constants for the callback points on a queue
	"""

	SAVE = 'save'
	CLEAR = 'clear'
	APPEND = 'append'

class Queue(queue.Queue):
	"""
	This class handles queueing models for a bulk save. When the queue reaches its limit, it will automatically save the queued models and empty the queue
	TODO: Doc is out of date. Will be used for a queue manager in the future.

	Examples:
		queue = Queue(limit=2)
		queue.size(Case) # --> 0
		queue.append( Case, case_instance )
		queue.size(Case) # --> 1
		queue.append( Case, another_case_instance )
		queue.size(Case) # --> 2
		queue.append( Person, person_instance )
		# The above call impacts the Person queue, not the Case queue
		queue.size(Case) # --> 2
		queue.append( Case, third_case_instance )
		queue.size(Case) # --> 0
		# The above call will trigger queue.save( Case ) after the third case is appended to the queue
		queue.append( Case, fourth_case )
		queue.size(Case) # --> 1
		queue.save(Case)
		# The above call clears the queue after save
		queue.size(Case) # --> 0

	"""

	# The point at which we automatically trigger save()
	limit: int = 100

	# The key on this model to check for collisions during save() - if a collision happens, we update instead
	unique_key: list[str] = []

	# A queue ONLY works on a single model. This can be specified in __init__, or determined by the first append
	model: Model

	# Optional callbacks to be used when certain actions occur (like saving the queue, clearing the queue, etc)
	# NOTE: The signature uses "str" instead of "Callbacks" so that subclasses of Queue can implement additional callback points.
	callbacks: dict[str, Callable | None] = {}

	# If True, saving the queue will be deferred until it is turned back on
	# Saving will still occur at the end of a with block.
	_save_deferred : bool = False

	# A queue for one specific model. For example:
	# case_queue = [Case(), Case()]
	# person_queue = [Person()]
	# error_queue = [Case(), Person()] # --> This throws an error
	queue: deque[Model]

	@property
	def save_deferred(self) -> bool:
		"""
		If true, saving the queue will be deferred until it is turned back on
		"""
		return self._save_deferred

	@save_deferred.setter
	def save_deferred(self, value: bool) -> None:
		"""
		Tell the queue to defer saving until it is turned back on.

		Args:
			value (bool):
				If true, turns on deferred saving (which is the normal use case for this method).
				This does NOT trigger the queue to be processed.

		Returns:
			None

		Notes:
			Turning deferred saving off using this method does NOT trigger the queue to be processed.

		"""
		self._save_deferred = value

	def __init__(self,
				 unique_key: str | list[str] | None = None,
				 model: Optional[Model] = None,
				 limit: int = 100,
				 save_deferred : bool = False,
				 callbacks : dict[str, Callable] | None = None):
		"""
		Create a new queue, which handles saving models in batches.

		Args:
			unique_key (str | Array, optional):
				A unique key to use for upserts. Data in the queue which collides with this unique key will be updated instead of inserted.
				The unique_key can also be set in the subclass definition, and then not provided here on init.
				A unique key is required to be set.
			model (Model, optional):
				The model (i.e. db table) to update.
				The modal can also be set in the subclass definition, and then not provided here on init.
				If not provided, the model will be determined by the type of the first queue.append
			limit (int, optional):
				The maximum size of the queue. After this number of items are added, the queue will be saved to the DB and cleared.
				This value can also be set in the subclass definition, and then not provided here on init.
				Defaults to 100.
				If set to -1, limit will be ignored, and saves will only occur when the queue is closed, or save() is called explicitly.
			save_deferred (bool, optional):
				If True, will defer saving until it is turned back on.
				If False, saving will occur normally when the queue capacity is reached or save() is called explicitly.
				Saving will still occur at the end of a with block.
				Defaults to false.
			callbacks (dict[str, Callable]):
				This MAY be deprecated in the future in favor of signals. I'm still fleshing out the API here.
				An optional set of callbacks to use when the queue performs certain actions (such as saving, clearing, etc).
				By default, the base queue class supports callbacks listed in the Callbacks class. Subclasses of Queue may extend these to support more.
				NOTE: The signature uses "str" instead of "Callbacks" so that subclasses of Queue can implement additional callback points.

		Raises:
			TypeError: If no unique key is provided in the class definition or as a param of init.

		"""
		if callbacks is None:
			callbacks = {}

		# Set the unique key (or convert to an array and set it). If not provided, we assume that a subclass has set it manually in the class def.
		if unique_key is not None:
			if isinstance(unique_key, list):
				self.unique_key = unique_key
			else:
				self.unique_key = list(unique_key)

		# If no unique key is available from the class def or __init__, then we can't do bulk_inserts.
		if not self.unique_key:
			raise TypeError(f'No unique key provided to django-foundry.models.Queue: {unique_key}')

		# Allow the default python queue to handle the generic init.
		# maxsize must be 0 to allow us to overflow the queue to trigger a save.
		super().__init__(maxsize=0)

		# Set the limit at which we trigger a save.
		self.limit = limit

		# Initialize the model (if provided). If set to none, this will be determined on the first queue.append()
		if model:
			self.model = model

		# Allow us to start off deferring saves if desired.
		self._save_deferred = save_deferred

		# Initialize the callbacks and merge with anything we passed in.
		if self.callbacks is None:
			self.callbacks = { callback : None for callback, _x in Callbacks.choices }
		else:
			# Allow setting callbacks in the subclass definition (even though doing that is probably a bad idea... supporting it eliminates unexpected behavior)
			self.callbacks = { callback : None for callback, _x in Callbacks.choices } | self.callbacks

		if callbacks:
			self.callbacks.update(callbacks)

	def __enter__(self) -> Self:
		"""
		Allow this to be used in a with block.
		"""
		# Return this instance, so the with statement can set "AS" variables.
		return self

	def __exit__(self, exit_type, value, traceback):
		"""
		When exiting a with block, automatically save all remaining objects in the queue.

		Notes:
			This FORCES a save, even if saving is deferred.

		"""
		# Force the save, but don't change the deferral state.
		self.save(force_save=True)

	def callback(self, callback_name : str, **kwargs) -> Any:
		"""
		Issue a callback (if it is defined)

		Args:
			callback_name (str): The name of the callback (specified in __init__ or the class definition)
			**kwargs: Any additional arguments to pass to the callback

		Returns:
			Any: Special callbacks may define what kinds of data they wish to return.

		Raises:
			ValueError: If the callback_name is not set (i.e. there is a typo)

		"""
		# No callback by this name.
		if callback_name not in self.callbacks:
			raise ValueError(f"No callback defined for {callback_name}")

		# No callback defined.
		if self.callbacks[callback_name] is None:
			return None

		# Call the callback with any args we passed in, and return any result we get.
		cb = self.callbacks[callback_name]

		if cb:
			return cb(**kwargs)

		return None

	# TODO: warning on unsaved queue on __del__

	def defer_save(self, value: bool = True) -> None:
		"""
		Convenience method for queue.save_deferred = True; queue.allow_save()

		Args:
			value (bool):
				If true, turns on deferred saving (which is the normal use case for this method).
				For consistency, we allow passing False to turn deferred saving off.
				Setting this to False DOES trigger the queue to be processed.

		Returns:
			None

		Notes:
			Turning deferred saving off using this method DOES trigger the queue to be processed.

		"""
		self.save_deferred = value

		if value is not True:
			self.allow_save()

	def clear(self) -> int:
		"""
		Empty the queue.

		NOTE: This does not save the items in the queue. It simply removes them.

		Returns:
			int: The number of items removed from the queue

		"""
		# Save the number in the queue before we empty it
		count = self.size()

		# Issue save callbacks with the current queue before being cleared
		#self.callback(Callbacks.CLEAR, queue=self.queue)
		#Hooks.run('queue', 'clear', queue=self.queue)
		signals.QueueCleared().broadcast(self, queue=self.queue)

		# Empty the queue
		self.queue.clear()

		# Return the number removed
		return count

	def size(self) -> int:
		"""
		Return the size of a given model's queue.

		Convenience method for queue.qsize(), so it is more obvious what we're doing.

		Returns:
			int: Return the approximate size of the queue.

		Note:
			From the queue doc: qsize() > 0 doesn’t guarantee that a subsequent get() will not block, nor will qsize() < limit guarantee that put() will not block.

		"""
		# Use get instead of an index so we return 0 when a queue doesn't exist yet
		return self.qsize()

	def save(self, *, force_save : bool = False) -> int:
		"""
		Save all data in the given model queue.

		NOTE: This empties the queue after saving.

		Args:
			force_save (bool, optional):
				If True, ignore deferral and force the queue to be saved.
				Generally speaking, this should not be used in favor of turning off deferral or calling allow_save()
				Must be specified as a named argument for readibility (i.e. to avoid queue.save(True))
				Defaults to False.

		Returns:
			The number of items saved (and removed) from the queue

		"""
		# If saving is deferred, then we have nothing to do right now.
		if self.save_deferred is True and force_save is not True:
			return 0

		# Avoid trying to save an empty set. This is particularly important because self.model may be None if nothing was ever added to the queue
		if self.size() <= 0:
			return 0

		# Convert the entire queue into dicts
		values = [model.to_dict() for model in self.queue]

		# Use Postgres' "on conflict" clause to attempt an INSERT, and fall back to an UPDATE if we have a collision.
		# Collisions are caused by duplicating "case_id", which has a unique constraint in the db.
		results = self.model.objects.on_conflict(self.unique_key, ConflictAction.UPDATE).bulk_insert(values)

		# TODO: [AUTO-368] Validation (all were saved)

		# Issue save callbacks with the current queue and any save results
		#self.callback(Callbacks.SAVE, queue=self.queue, results=results)

		# Run registered hooks
		#Hooks.run('queue', 'save', queue = self.queue, results = results)
		signals.QueueSaved().broadcast(self, queue = self.queue, results = results)

		# Once finished, clear the queue
		count = self.clear()

		# Return the number of models saved
		return count


	def allow_save(self) -> int:
		"""
		Allow the queue to save, if it has reached capacity.

		This is useful if the queue is deferred, or if append() has been called with defer_save=True to delay saving.
		When we've reached a part of our code where saving can be allowed to happen if it is appropriate, we can call this method
		to check the queue size and make a decision to trigger a save.

		Returns:
			int: The number of rows saved (and removed) from the queue.

		Examples:
			>>> frommodels.people import Person
			>>> queue = Queue(limit=2)
			>>> queue.append(Person())
			1
			>>> queue.append(Person())
			0
			>>> queue.defer_save

		"""
		# Check if a save is warranted.
		if self.size() > self.limit > -1:
			# Save them all. NOTE: This will call clear() once finished, setting the queue back to 0 length
			return self.save(force_save=True)

		# Save wasn't triggered, so we acted on 0 rows.
		return 0


	def append(self, model: Model, defer_save : bool = False) -> int:
		"""
		Add a model to the queue, and if limit is reached, save the queue and clear it.

		Args:
			model (Model):
				The model to append to the queue.
			defer_save (bool, optional):
				If set to True, this will append the model but will not save it, even if the queue size overflows.
				defaults to False.

		Returns:
			int: The new queue size.

		"""
		# If the queue's model is not set, determine it from this first append
		if self.model is None:
			self.model = model

		# Validate the model is the correct type
		if model.__class__ is not self.model:
			raise ValueError(f'Unable to add modal of type {type(model)} to a queue for {self.model}')

		# Add it at the end
		self.put(model, block=False)

		# Issue append callbacks with this item and the current queue
		# We probably don't need this callback, but it's cheap to make.
		#self.callback(Callbacks.APPEND, item=model, queue=self.queue)
		#Hooks.run('queue', 'append', item=model, queue=self.queue)

		# If the queue is ready for processing, then handle everything in it now
		if defer_save is not True and self.size() > self.limit > -1:
			# Save them all. NOTE: This will call clear() once finished, setting the queue back to 0 length
			self.save()

		# Return the size of the queue. This tells us if it was saved (and cleared) => 0, or if it was appended => int>0
		return self.size()
