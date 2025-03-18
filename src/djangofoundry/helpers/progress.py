"""


Metadata:

File: progress.py
Project: Django Foundry
Created Date: 10 Aug 2022
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

from datetime import timedelta
from decimal import Decimal
from time import perf_counter_ns
from typing import Optional

import humanize
from celery.app.task import Task
from celery_progress.backend import PROGRESS_STATE, ProgressRecorder

# Django Imports
from django.db.models import TextChoices
from typing_extensions import Self

# Lib Imports
# App Imports

class ProgressStates(TextChoices):
	"""
	Enum for the possible states of a progress bar.
	"""

	PROGRESS = PROGRESS_STATE
	SUCCESS = 'SUCCESS'
	FAILURE = 'FAILURE'
	RETRY = 'RETRY'
	REVOKED = 'REVOKED'
	IGNORED = 'IGNORED'
	PENDING = 'PENDING'
	STARTED = 'STARTED'

	@classmethod
	def has_started(cls, state : Self | str) -> bool:
		"""
		Checks if the given state is something AFTER "started".
		"""
		return state not in [cls.STARTED, cls.PENDING]

default_settings = {
	'show_eta': True
}

class ProgressBar(ProgressRecorder):
	"""
	Override default ProgressRecorder object to provide a few extra features

	TODO: Rewrite the whole ProgressRecorder module for python3
	"""

	# Typehint the task. This doesn't change functionality at all, but helps with our IDE
	task: Task | None
	_state: str = 'PENDING'
	_start_time: int
	_current: int = 0
	_total: int = 1
	_description: str = ''
	_pending = False
	settings : dict = default_settings

	def __init__(self, task: Optional[Task] = None, total : int = 1, settings: Optional[dict] = None):
		"""
		Initialize the ProgressBar with an optional task and settings.

		Args:
			task (Task, optional):
				The task to use for the progress bar. If None, this progress bar will act like a proxy... allowing us to update
				its fields without interacting with a celery backend.

			total (int, optional):
				The total number of tasks to complete. Defaults to 1. Can be set and updated at any point during the lifetime of this progress bar.

			settings (dict, optional):
				The settings to use for the progress bar.
				Options are:
					show_eta (bool):
						If True, an ETA is shown at the end of the progress description.
						If False, ETA is stil available, but is not automatically shown.
						Default: True

		Examples:
			progress = ProgressBar(task)
			progress.update(current=1, total=5, description="First Task")
			# This will create a progress bar with default settings and report progress to the celery backend through the task object.

			progress = ProgressBar(task, {'show_eta': False})
			progress.total = 10
			progress.next("Starting first task")
			# This creates a progress bar with a custom setting (turning ETA off)

			progress = ProgressBar()
			progress.update()

		Allow None for task, which will effectively suppress output

		"""
		if settings is None:
			settings = {}

		# Set the total early so we can be sure it isn't None when calculations are requested.
		self.total = total

		# Allow settings to be passed in completely, partially, or changed later.
		# This notation indicates a dict merge. Default settings are overwritten by any settings passed in.
		self.settings = default_settings | settings

		super().__init__(task)

		# Start the clock on init
		self._init_start()

	@property
	def meta(self) -> dict:
		return {
			'pending': self.pending,
			'current': self.current,
			'total': self.total,
			'percent': self.percent,
			'description': self.describe()
		}

	@property
	def start(self) -> int:
		"""
		Get the time this job started (in ns)
		"""
		return self._start_time

	def _init_start(self):
		"""
		Private method to set the start time
		"""
		self._start_time = perf_counter_ns()

	def restart_timer(self) -> int:
		"""
		Restarts the timer and returns the previous elapsed time before the reset

		Returns:
			int: The previous elapsed time before the reset (in ns)

		"""
		# This calculates our elapsed time in a @property. Save it here before we reset the timer.
		elapsed = self.elapsed

		# Start a new timer
		self._init_start()

		# Give the calling function the amount of time that elapsed since start
		return elapsed

	def restart(self, total: int = 100, description: Optional[str] = None):
		"""
		Convenience function for self.restart_timer(); self.update()
		"""
		self.restart_timer()
		self.update(current=1, total=total, description=description)

	@property
	def elapsed(self) -> int:
		"""
		Get the time elapsed since start (in nanoseconds)
		"""
		return perf_counter_ns() - self.start

	@property
	def eta(self) -> int | None:
		"""
		Get an ETA to completion (in seconds)

		Returns:
			int | None: An ETA to completion (in seconds). If the percent done is exactly zero, returns None.

		TODO: [AUTO-354] Add support for lambda functions for calculating eta on progress bars
			Add support for passing in lambda functions for calculating this value

		"""
		# Avoid division by 0
		if not self.percent:
			return None

		# Calculate ETA. elapsed / 1e9 converts nanoseconds to seconds (by dividing by 1,000,000,000)
		# This gets multiplied by the remaining part to be completed
		# TODO: [AUTO-353] This calculation may be incorrect?
		result = Decimal(self.elapsed / 1e9) * Decimal( (100 - self.percent) / self.percent )

		# Round off the decimal places and convert it to an int.
		return round(result)

	def describe(self) -> str:
		"""
		Get the description for this progress bar. If show_eta is True, this will include an ETA.
		"""
		# If we've done "enough" work to generate a reasonable ETA, then append it to the description.
		if self.settings['show_eta'] is True and self.percent >= 0.001 and self.current > 3 and self.eta:
			return f'{self.description}. ETA {humanize.naturaldelta(timedelta(seconds=self.eta))}'

		# Otherwise, just return a plain description
		return self.description

	@property
	def description(self) -> str:
		"""
		Get the task description. Default None
		"""
		return self._description

	@description.setter
	def description(self, value: str) -> None:
		"""
		Set the task description, but keep all other values the same
		"""
		# Set our local value on this object
		self._description = value

		# If a task exists, refresh it
		self.refresh_task_state()

	@property
	def pending(self) -> bool:
		"""
		Get the pending state of the task. Default False
		"""
		return self._pending

	@pending.setter
	def pending(self, value: bool):
		"""
		Set our pending state. This gets treated like a normal property (i.e. progress_bar.pending = True), but it runs
		additional code (e.g. progress_bar.refresh_task_state()) whenever the pending state is changed.
		"""
		# Set our local value on this object
		self._pending = value

		# If a task exists, refresh it
		self.refresh_task_state()

	@property
	def current(self) -> int:
		"""
		Get the current number of items completed (out of total). Default 0
		"""
		return self._current

	@current.setter
	def current(self, value: int) -> None:
		# Set our local value on this object
		self._current = int(value)

		# If a task exists, refresh it
		self.refresh_task_state()

	def next(self, description: Optional[str] = None, advance: int = 1) -> int:
		"""
		Increase our current task by a given amount (default 1). Useful when we don't know our current status but know we've completed a task.

		Args:
			description (str, optional):
				An optional description to set
			advance (int, optional):
				The amount to increase in the current task. Defaults to 1.

		Returns:
			int: The current counter after increasing it

		"""
		# Increase it
		self._current += advance

		# Update the description if it was provided
		if description is not None:
			self._description = description

		# If a task exists, refresh it
		self.refresh_task_state()

		# Return the new value
		return self.current

	def advance(self, amount : int, description: Optional[str] = None) -> int:
		"""
		Convenience function for self.next(advance = amount).

		Args:
			amount (int):
				The amount to increase in the current task.
			description (str, optional):
				An optional description to set

		Returns:
			int: The current counter after increasing it

		"""
		return self.next(description, amount)

	@property
	def total(self) -> int:
		"""
		Get the total items for our task to complete. Default 1

		Returns:
			int: The total tasks

		"""
		return self._total

	@total.setter
	def total(self, value: int) -> None:
		"""
		Set the total items for our task to complete.

		Args:
			value (int): The total items

		Returns:
			Nothing

		"""
		self._total = int(value)

		# If a task exists, refresh it
		self.refresh_task_state()

	@property
	def percent(self) -> Decimal:
		"""
		The percent complete. Default 0
		"""
		# Avoid division by 0
		if not self.total:
			return Decimal('0.0')

		# Always calculate it
		percent = (self.current / self.total) * 100
		return Decimal(round(percent, 2))

	@property
	def state(self) -> str:
		return self._state

	@state.setter
	def state(self, value : str) -> None:
		self._state = value

	def update(self, current: Optional[int] = None, description: Optional[str] = None, total: Optional[int] = None):
		"""
		Update one or more params
		"""
		if current is None and total is None and description is None:
			raise ValueError('ProgressBar.update: no values set')

		if current is not None:
			self._current = int(current)
		if total is not None:
			self._total = int(total)
		if description:
			self._description = str(description)

		# If a task exists, refresh it
		self.refresh_task_state()

	def set_progress(self, current: int, total: int = 100, description: str = ""):
		"""
		Overrides default functionality to save meta locally in this class
		"""
		self.update(current=current, description=description, total=total)

		# Return the same thing as our parent
		return self.state, self.meta

	def get_task(self) -> Task | None:
		"""
		Get the task object
		"""
		return self.task

	def refresh_task_state(self) -> None:
		"""
		Update the task state based on our instance attributes
		"""
		# Update to running if we 1) haven't yet and 2) have done anything at all.
		# -- otherwise, trust the end user to update states appropriately
		if not ProgressStates.has_started(self.state) and (self._current > 0 or self._description):
			self._state = PROGRESS_STATE

		# If we don't have a task, there's nothing to refresh
		if not hasattr(self, 'task') or not self.task:
			return

		# Refresh the state of the task we have based on our local values here
		self.task.update_state(
			state=self.state,
			meta=self.meta
		)

class ChildProgressBar():
	"""
	This class can be passed to child tasks in order to update the overall progress bar within the context of a subtask.

	In other words, it can provide progress updates without changing the total number of tasks.

	TODO: Unfinished
	"""

	_parent : ProgressBar
	_total : int = 0
	_current : int = 0

	def __init__(self, parent : ProgressBar, total : int = 0, current : int = 0):
		self._parent = parent
		self.total = total
		self.current = current

		raise NotImplementedError()

	@property
	def parent(self) -> ProgressBar:
		return self._parent

	@property
	def total(self) -> int:
		return self._total

	@total.setter
	def total(self, value : int) -> None:
		self._total = value

	@property
	def current(self) -> int:
		return self._current

	@current.setter
	def current(self, value : int) -> None:
		self._current = value

	def update(self, current : int) -> None:
		pass

	@property
	def description(self) -> str:
		return self.parent.description

	@description.setter
	def description(self, value : str) -> None:
		self.parent.description = value
