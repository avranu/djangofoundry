"""
This module defines types that we use in our hook classes.

Metadata:

File: types.py
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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from djangofoundry.helpers.hooks.waypoint import Waypoint

# A type representing { hook_name => Waypoint }
# Waypoints store a list of registered hooks as well as metadata about the hook waypoint.
WaypointMap = dict[str, Waypoint]

# A type representing { namespace => WaypointMap }
NamespaceMap = dict[str, WaypointMap]
