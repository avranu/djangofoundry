"""

Metadata:

File: generic.py
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
# Generic imports
from __future__ import annotations

# Django Imports
from django.views import View

# Lib Imports
# App Imports

class GenericController(View):
	"""
	Controller for generic views. When we don't want a "Detail" or a "List", but want to inherit from a standard class structure in our app.
	"""
