"""

Metadata:

File: template.py
Project: Django Foundry
Created Date: 09 Apr 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Thu Apr 13 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
from __future__ import annotations

import logging

from jinja2 import Environment, PackageLoader, TemplateNotFound, select_autoescape
from pyparsing import Optional

from djangofoundry.helpers.render.template import TemplateHelper as BaseTemplate

# Set up logging for this module
logger = logging.getLogger(__name__)

class TemplateHelper(BaseTemplate):
	"""
	A helper class for rendering jinja templates

	Attributes:
		env (Environment): The jinja environment.

	"""

	_env: Environment
	template_path: str = 'templates/jinja'
	template_suffix: str = '.jinja'
	autoescape: list = ['html', 'xml']

	def __init__(self, app_name: str, template_path: str = 'templates/jinja', autoescape: Optional[list[str]] = None, template_suffix: str = '.jinja'):
		"""
		Initialize the code helper.

		Args:
			app_name (str): The name of the app to load the templates from.
			template_path (str, optional): The path to the templates. Defaults to 'templates/jinja'.
			template_suffix (str, optional): The suffix for the templates. Defaults to '.jinja'.

		Raises:
			ValueError: If app_name is None.

		"""
		if app_name is None:
			raise ValueError('app_name cannot be None')

		if autoescape is None:
			autoescape = ['html', 'xml']

		super().__init__(app_name, template_path, template_suffix)

		self.autoescape = autoescape

	@property
	def env(self) -> Environment:
		"""
		The jinja environment.

		Returns:
			Environment: The jinja environment.

		"""
		return self._env

	def setup_environment(self) -> None:
		"""
		Setup the jinja environment.
		"""
		logger.debug(f'Setting up jinja environment: {self.app_name} : {self.template_path}')
		self._env = Environment(
			loader=PackageLoader(self.app_name, self.template_path),
			autoescape=select_autoescape(self.autoescape)
		)

	def render(self, variables: dict, template_name: str) -> str | None:
		"""
		Render a template with the given variables.

		Args:
			variables (dict): The variables to pass to the template.
			template_name (str): The name of the template to render.

		Returns:
			str: The rendered template.

		"""
		try:
			template = self.env.get_template(template_name + self.template_suffix)
			return template.render(variables)
		except TemplateNotFound as e:
			logger.error(f"Template '{template_name}' not found: {str(e)}")
			return None
		except Exception as e:
			logger.error(
				f"Error generating code from template '{template_name}': {str(e)}")
			return None
