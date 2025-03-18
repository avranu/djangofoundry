"""

Metadata:

File: template.py
Project: Django Foundry
Created Date: 09 Apr 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Sun Apr 09 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

# Set up logging for this module
logger = logging.getLogger(__name__)

class TemplateHelper(ABC):
	"""
	A helper class for rendering templates

	Attributes:
		template_path (str): The path to the templates.
		template_suffix (str): The suffix for the templates.

	"""

	_app_name: str
	template_path: str
	template_suffix: str

	def __init__(self, app_name: str, template_path: str, template_suffix: str):
		"""
		Initialize the code helper.

		Args:
			app_name (str): The name of the app to load the templates from.
			template_path (str, optional): The path to the templates.
			template_suffix (str, optional): The suffix for the templates.

		Raises:
			ValueError: If app_name is None.

		"""
		if app_name is None:
			raise ValueError('app_name cannot be None')

		self._app_name = app_name
		self.template_path = template_path
		self.template_suffix = template_suffix
		self.setup_environment()

	@property
	def app_name(self) -> str:
		"""
		The name of the app to load the templates from.

		Returns:
			str: The name of the app to load the templates from.

		"""
		return self._app_name

	@property
	def application(self) -> str:
		"""
		The name of the app to load the templates from. (Same as "app_name")

		Returns:
			str: The name of the app to load the templates from.

		"""
		return self.app_name

	def setup_environment(self) -> None:
		"""
		Setup a templating environment. Subclasses should implement this method if an environment is needed. This is called at the end of __init__.
		"""
		return None

	@abstractmethod
	def render(self, variables: dict, template_name: str) -> str | None:
		"""
		Render a template with the given variables.

		Args:
			variables (dict): The variables to pass to the template.
			template_name (str): The name of the template to render.

		Returns:
			str: The rendered template.

		"""
		raise NotImplementedError("Subclasses of TemplateHelper must implement render()")
