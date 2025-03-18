"""

Metadata:

File: logging.py
Project: Django Foundry
Created Date: 19 Oct 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Fri Dec 02 2022
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann
"""
from __future__ import annotations

import logging

# Set up logging for this module. __name__ includes the namespace (e.g. dashboard.models.cases).
#
# We can adjust logging settings from the namespace down to the module level in project/settings
#
logger = logging.getLogger(__name__)

def log_object( obj, level : str = 'DEBUG', name : str = 'Reference', use_logger = None ) -> None:
	if use_logger is None:
		use_logger = logger

	try:
		message : str = f'{name}: {obj}'
		match level:
			case 'DEBUG':
				logger.debug(message)
			case 'ERROR':
				logger.error(message)
			case 'WARN':
				logger.warning(message)
			case 'INFO':
				logger.info(message)
			case _:
				# Note a missing loglevel
				use_logger.error(f'Unknown level: {level}')
				# Default to error so it definitely shows up
				logger.error(message)
	except Exception as e:
		# Note exceptions, but otherwise ignore them.
		use_logger.debug(f'Unable to log object named "{name}": {e}')
