"""


Metadata:

File: timeout.py
Project: Django Foundry
Created Date: 03 Aug 2022
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

import functools
import signal


def timeout(seconds : int, error_message : str = 'Function call timed out'):
	"""
	Based on: https://wiki.python.org/moin/PythonDecoratorLibrary#Function_Timeout
	Example:  @timeout(1, 'Function slow; aborted')
	"""
	def decorated(func):
		def _handle_timeout(signum, frame):
			raise TimeoutError(error_message)

		def wrapper(*args, **kwargs):
			# TODO: [AUTO-370] This throws an exception on windows because windows doesn't implement SIGALRM.
			signal.signal(signal.SIGALRM, _handle_timeout)
			signal.alarm(seconds)
			try:
				result = func(*args, **kwargs)
			finally:
				signal.alarm(0)
			return result

		return functools.wraps(func)(wrapper)

	return decorated
