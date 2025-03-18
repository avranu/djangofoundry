"""

Metadata:

File: abstract.py
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

from django import dispatch


class Signal(dispatch.Signal):
	"""
	A base signal class that our application inherits from to detect application-specific signals.
	"""

	def broadcast(self, sender, **named):
		"""
		Send signal from sender to all connected receivers.

		This works the same as django's Signal.send() except that it takes an instance as a first positional argument for convenience.

		If any receiver raises an error, the error propagates back through send,
		terminating the dispatch loop. So it's possible that all receivers
		won't be called if an error is raised.

		Arguments:
			sender
				The sender of the signal. Either a specific object or None.

			named
				Named arguments which will be passed to receivers.

		Return a list of tuple pairs [(receiver, response), ... ].

		"""
		return self.send(sender.__class__, **named)
