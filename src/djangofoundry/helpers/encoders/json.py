"""

Metadata:

File: json.py
Project: Django Foundry
Created Date: 24 Apr 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Mon Apr 24 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
import json
from decimal import Decimal


class JSONEncoder(json.JSONEncoder):
	"""
	JSON encoder that can handle Decimal objects
	"""

	def default(self, obj):
		if isinstance(obj, Decimal):
			return float(obj)
		return super().default(obj)
