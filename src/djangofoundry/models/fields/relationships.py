"""


Metadata:

File: relationships.py
Project: Django Foundry
Created Date: 18 Aug 2022
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

import auto_prefetch

# Django Imports
from django.db import models

# App Imports

class ForeignKey(auto_prefetch.ForeignKey):
	"""
	A ForeignKey that uses the auto_prefetch library.
	"""


class OneToOneField(auto_prefetch.OneToOneField):
	"""
	A OneToOneField that uses the auto_prefetch library.
	"""

class ManyToManyField(models.ManyToManyField):
	"""
	A ManyToManyField (for future expansion, and consistency)
	"""
