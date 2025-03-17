
from __future__ import annotations

from typing import Self

from {project_name}.lib import models

class DashboardModel(models.LibModel):
    class Meta(models.LibModel.Meta):
        abstract = True
