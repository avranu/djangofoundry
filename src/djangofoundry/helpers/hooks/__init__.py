"""
This module provides classes which allow us to register and call hooks in arbitrary points of our code.

Metadata:

File: __init__.py
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

from djangofoundry.helpers.hooks.exceptions import MaxExecutionsError
from djangofoundry.helpers.hooks.hooks import Hook, Hooks
from djangofoundry.helpers.hooks.meta import DEFAULT_NAMESPACE, DEFAULT_PRIORITY
