"""

Metadata:

File: mixins.py
Project: Django Foundry
Created Date: 15 Sep 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Fri Dec 02 2022
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann
"""
# Generic imports
import logging

# Django imports
from django.http import JsonResponse

# Get a logger for logging messages
#
# Set up logging for this module. __name__ includes the namespace (e.g. dashboard.models.cases).
#
# We can adjust logging settings from the namespace down to the module level in project/settings
#
logger = logging.getLogger(__name__)

class JSONResponseMixin:
	"""
	Mixin for a controller that render JSON responses.
	"""

	def render_to_json_response(self, context, **kwargs):
		return JsonResponse(self.get_data(context), **kwargs)

	def get_data(self, context):
		return context
