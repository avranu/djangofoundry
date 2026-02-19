"""


Metadata:

        File: list.py
        Project: Django Foundry
        Created Date: 16 Aug 2022
        Author: Jess Mann
        Email: jess.a.mann@gmail.com

        -----

        Last Modified: Thu Apr 13 2023
        Modified By: Jess Mann

        -----

        Copyright (c) 2022 Jess Mann

"""

# Generic imports
from __future__ import annotations

from django.db.models import QuerySet

# Django Imports
from django.views import generic

# Lib Imports
# App Imports


class TemplateController(generic.ListView):
    """
    Generic controller for providing list views for django models. All list views in our application inherit from this.
    """

    queryset = QuerySet().none()  # pyright: ignore[reportUnknownVariableType]
