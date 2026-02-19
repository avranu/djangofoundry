"""


Metadata:

        File: objects.py
        Project: Django Foundry
        Created Date: 22 Aug 2022
        Author: Jess Mann
        Email: jess.a.mann@gmail.com

        -----

        Last Modified: Thu May 04 2023
        Modified By: Jess Mann

        -----

        Copyright (c) 2022 Jess Mann

"""

# Generic imports
from __future__ import annotations

# Django imports
from django.db import models
from django.db.models import Func

# 3rd Party imports
from psqlextra import fields

# Optional imports
try:
    import picklefield.fields

    PICKLEFIELD_AVAILABLE = True
except ImportError:
    PICKLEFIELD_AVAILABLE = False


class HStoreField(fields.HStoreField):
    """
    An HStoreField that uses the psqlextra library.
    """


class JSONField(models.JSONField):
    """
    def get_prep_value(self, value):
            if value is None:
                    return value
            return orjson.dumps(value)

    def validate(self, value, model_instance):
            super().validate(value, model_instance)
            try:
                    orjson.dumps(value)
            except TypeError:
                    raise exceptions.ValidationError(
                            self.error_messages["invalid"],
                            code="invalid",
                            params={"value": value},
                    )
    """


class JsonFloatValues(Func):
    """
    Extracts the values from a JSON object and casts them to floats.
    """

    function = "jsonb_each_text"

    def __init__(self, expression, **extra):
        super().__init__(expression, output_field=models.FloatField(), **extra)


class PickledObjectField(models.Field):
    """
    A PickledObjectField that uses the picklefield library.

    Requires picklefield to be installed.
    """

    def __new__(cls, *args, **kwargs):
        if not PICKLEFIELD_AVAILABLE:
            raise ImportError(
                "picklefield is required to use PickledObjectField. " "Install it with: pip install django-picklefield"
            )
        # If picklefield is available, return an instance of the actual PickledObjectField
        return picklefield.fields.PickledObjectField(*args, **kwargs)
