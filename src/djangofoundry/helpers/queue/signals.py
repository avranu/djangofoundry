"""

Metadata:

File: signals.py
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

from djangofoundry.signals import Signal


class QueueSignal(Signal):
	"""
	A signal issued by a Queue
	"""

class QueueSaved(QueueSignal):
	"""
	Emitted when a Queue is saved
	"""

class QueueCleared(QueueSignal):
	"""
	Emitted when a Queue is cleared
	"""
