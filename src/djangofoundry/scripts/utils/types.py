"""

Metadata:

File: types.py
Project: Django Foundry
Created Date: 16 Sep 2022
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

from enum import Enum
from typing import TypedDict


class LoggerLevels(Enum):
	"""
	Enum for the different logging levels.
	"""

	DEBUG = 'debug'
	INFO = 'info'
	ERROR = 'error'
	WARNING = 'warning'
	WARN = WARNING

class YesNo(Enum):
	"""
	Enum for YES/NO fields
	"""

	YES = 'yes'
	Y = YES
	NO = 'no'
	N = NO

class Logger(TypedDict):
	"""
	Expected format for a "logger" in the settings file.
	"""

	level: LoggerLevels
	handlers: list[str]
	propogate: YesNo

class LogFormatter(TypedDict):
	"""
	Expected format for a "formatter" in the settings file.
	"""

	format: str

class LogHandler(TypedDict):
	"""
	Expected format for a "handler" in the settings file.
	"""

	level: LoggerLevels
	formatter: str
	stream: str
	# class: str

class LogRoot(TypedDict):
	"""
	Expected format for the "root" logger in the settings file.
	"""

	level: LoggerLevels
	handlers: list[LogHandler]

class SettingsLog(TypedDict):
	"""
	Expected format for the logging portion of the settings file.

	This is useful to provide type hints in our editor.
	"""

	version: int
	formatters: dict[str, LogFormatter]
	handlers: dict[str, LogHandler]
	loggers: dict[str, Logger]
	root: LogRoot

class BrowserSync(TypedDict):
	"""
	Expected format for the browsersync portion of the settings file.
	"""

	startPath: str
	watch: list[str]
	proxy: str
	reload_delay: int
	reload_debounce: int

class SettingsFile(TypedDict):
	"""
	Expected format of the settings file.

	This is useful to provide type hints in our editor.
	"""

	version: int
	logging: SettingsLog
	browsersync: BrowserSync
