
from __future__ import annotations

from djangofoundry.controllers.list import ListController

from dashboard.models.abstract import DashboardQuerySet


class IndexController(ListController):

    template_name = "dashboard/homepage.html"

    def get_queryset(self):
        return DashboardQuerySet.objects.none()
