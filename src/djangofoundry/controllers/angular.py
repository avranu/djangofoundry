"""

Metadata:

        File: angular.py
        Project: Django Foundry
        Created Date: 23 Apr 2023
        Author: Jess Mann
        Email: jess.a.mann@gmail.com

        -----

        Last Modified: Sun Apr 23 2023
        Modified By: Jess Mann

        -----

        Copyright (c) 2023 Jess Mann
"""

from django.shortcuts import render

from djangofoundry.controllers.generic import GenericController


class AngularController(GenericController):
    """
    This controller passes routing responsibility off to the Angular frontend.
    """

    # The template that contains our react js code.
    template_name = "angular/base.html"

    def get_queryset(self):
        """
        Do not make any queries or return any data. Angular will connect via our REST API to get the data it needs.

        Returns:
                An empty object.
        """
        return {}

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, *args, **kwargs)
