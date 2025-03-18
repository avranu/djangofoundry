"""

Metadata:

File: code.py
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
import re

from djangofoundry.helpers.render.jinja.template import TemplateHelper

# Set up logging for this module
logger = logging.getLogger(__name__)

class CodeHelper(TemplateHelper):
	"""
	A helper class for rendering jinja templates that create code.

	Attributes:
		env (Environment): The jinja environment.

	"""

	def suggest_class_name(self, input_str: str) -> str:
		"""
		Suggest a class name based on a set of input. This method exists primarily to establish an interface for subclasses.

		Args:
			input_str (str): The input to base the suggested name on

		Returns:
			str: The suggested class name

		"""
		# Remove any non-alpha and title case
		cleaned_name = re.sub(r'[^a-zA-Z]+', ' ', input_str).title().replace(' ', '')

		# Limit to 30 characters
		cleaned_name = cleaned_name[:30]

		return cleaned_name
