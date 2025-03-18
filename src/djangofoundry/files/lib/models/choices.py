from __future__ import annotations

from typing import Any

import django.db.models
import djangofoundry.models


class TextChoices(djangofoundry.models.TextChoices):
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, django.db.models.TextChoices):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)
