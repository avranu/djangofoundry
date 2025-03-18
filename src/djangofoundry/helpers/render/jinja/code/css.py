"""

Metadata:

File: css.py
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


class CssHelper(CodeHelper):
	"""
	A helper class for rendering jinja templates that create css code.
	"""
