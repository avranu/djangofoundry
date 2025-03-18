"""
This module defines constants that relate to our hook classes.

These can be imported in other packages with minimal dependencies that could cause a circular import.

Metadata:

File: constants.py
Project: Django Foundry
Created Date: 02 Sep 2022
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

# The default namespace to use when no namespace is specified
DEFAULT_NAMESPACE = 'application'
# The default priority to use when no priority is specified
DEFAULT_PRIORITY = 50
