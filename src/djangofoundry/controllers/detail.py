"""


Metadata:

File: detail.py
Project: Django Foundry
Created Date: 16 Aug 2022
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

from typing import TYPE_CHECKING, Any

from django.http import HttpRequest, JsonResponse

# Django Imports
from django.views import generic

# App Imports
from djangofoundry.mixins import JSONResponseMixin

if TYPE_CHECKING:
	pass

class DetailController(generic.DetailView):
	"""
	Generic controller for providing detail views for django models. All detail views in our application inherit from this.
	"""

class JsonDetailController(JSONResponseMixin, DetailController):
	"""
	Controller for providing detail views for django models. All detail views in our application inherit from this.
	"""

	def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
		data = super().get(request, *args, **kwargs)
		return self.render_to_response(data)

	def render_to_response(self, context, **kwargs):
		return self.render_to_json_response(context, **kwargs)
