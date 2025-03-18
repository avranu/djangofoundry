"""

Metadata:

File: javascript.py
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

from djangofoundry.helpers.render.jinja.code.template import CodeHelper

# Set up logging for this module
logger = logging.getLogger(__name__)

class JavascriptHelper(CodeHelper):
	"""
	A helper class for rendering jinja templates that create javascript code.
	"""
