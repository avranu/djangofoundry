"""


Metadata:

File: retry.py
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

import math
import time
from decimal import Decimal


# Retry decorator with exponential backoff
def retry(tries, delay : Decimal | int | float = 3, backoff : int = 2):
	"""
	Based on https://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties

	Retries a function or method until it returns True.

	delay sets the initial delay in seconds, and backoff sets the factor by which
	the delay should lengthen after each failure. backoff must be greater than 1,
	or else it isn't really a backoff. tries must be at least 0, and delay
	greater than 0.
	"""
	if backoff <= 1:
		raise ValueError("backoff must be greater than 1")

	tries = math.floor(tries)
	if tries < 0:
		raise ValueError("tries must be 0 or greater")

	if delay <= 0:
		raise ValueError("delay must be greater than 0")

	def deco_retry(callback):
		def f_retry(*args, **kwargs):
			mtries, mdelay = tries, float(delay)  # make mutable

			result = callback(*args, **kwargs)  # first attempt
			while mtries > 0:
				if result is True:  # Done on success
					return True

				mtries -= 1	  # consume an attempt
				time.sleep(mdelay)  # wait...
				mdelay *= backoff  # make future wait longer

				result = callback(*args, **kwargs)  # Try again

			return False  # Ran out of tries :-(

		return f_retry  # true decorator -> decorated function
	return deco_retry  # @retry(arg[, ...]) -> true decorator
