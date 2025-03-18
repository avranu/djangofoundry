"""

Metadata:

File: exceptions.py
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

class AppException(Exception):
	"""
	A base exception that all our custom app exceptions extend from.
	"""

class FileEmptyError(AppException):
	"""
	Raised when a file is empty that is required to have content (i.e. our settings file)
	"""

class DbError(AppException):
	"""
	Raised when there is a problem with the DB.

	This is inherited by several subclasses.
	"""

class DbConnectionError(DbError, ConnectionError):
	"""
	Raised when the database cannot be contacted, but it appears to be running.
	"""

class DbStartError(DbError, ConnectionError):
	"""
	Raised when the database cannot be started.
	"""

class UnsupportedCommandError(AppException):
	"""
	Raised when a command is passed to our app that isn't valid.
	"""
