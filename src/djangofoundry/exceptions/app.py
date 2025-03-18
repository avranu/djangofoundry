"""

Metadata:

File: exceptions/app.py
Project: Django Foundry
Created Date: 17 Dec 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Sun Apr 16 2023
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann
"""
class AppException(Exception):
	"""
	Internal exception used in our application.
	"""

	_custom_message : str | None = None

	@property
	def message(self) -> str:
		if self._custom_message is not None:
			return self._custom_message
		return self.args[0] or 'No exception message provided.'

	@message.setter
	def message(self, value : str):
		self._custom_message = value


class ValidationError(AppException):
	"""
	Raised when input validation fails.
	"""


class PermissionDeniedError(AppException):
	"""
	Raised when a user tries to access a resource they do not have permission to access.
	"""

class NotFoundError(AppException):
	"""
	Raised when a requested resource cannot be found.
	"""

class AuthenticationFailedError(AppException):
	"""
	Raised when authentication fails.
	"""

class MethodNotAllowedError(AppException):
	"""
	Raised when an HTTP method is not allowed for a resource.
	"""

class InternalServerError(AppException):
	"""
	Raised when an internal server error occurs.
	"""

class BadRequestError(AppException):
	"""
	Raised when a client request is invalid.
	"""

class ConflictError(AppException):
	"""
	Raised when a request conflicts with the current state of the server.
	"""
