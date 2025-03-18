
from __future__ import annotations

from djangofoundry.controllers import GenericController
from dashboard.models.abstract import DashboardQuerySet

class IndexController(GenericController):
    template_name = "dashboard/homepage.html"
