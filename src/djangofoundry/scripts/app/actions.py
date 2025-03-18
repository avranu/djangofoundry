from enum import Enum


class Actions(Enum):
	"""
	Defines the commands that can be used to interact with django.

	Attributes:
		start:
			start the django server
		test:
			runs our unit/integration tests

	"""

	START = "runserver"
	TEST = "test"
	STOP = "stop"
	RESTART = "restart"
	STATUS = "status"
	SETUP = 'setup'
	PAGE = 'page'
	MODEL = 'model'
	INSTALL = 'install'

	def __str__(self):
		"""
		Turns an option into a string representation
		"""
		return self.value

	def __repr__(self):
		return self.value
