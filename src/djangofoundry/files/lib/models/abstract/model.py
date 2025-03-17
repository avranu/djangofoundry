
from __future__ import annotations

from typing import Self

# Django Imports
from djangofoundry import models as foundry
from {project_name}.lib.models.abstract.queryset import LibQueue

class LibModel(foundry.Model):
    queue : LibQueue[Self]

    class Meta(foundry.Model.Meta):
        abstract = True
