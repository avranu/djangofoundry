
from __future__ import annotations

import datetime

import faker
from django.utils import timezone


class Faker:

    def __init__(self, *args, **kwargs):
        # Locale should default to en-US
        if "locale" not in kwargs and not args:
            kwargs["locale"] = "en_US"
        self._faker = faker.Faker(*args, **kwargs)

    def __getattr__(self, name):
        faker_method = getattr(self._faker, name)

        def method(*args, max_length: int = 0, min_length: int = 0, **kwargs):
            # Generate the value using the original Faker method
            value = faker_method(*args, **kwargs)

            # If max_length is provided, truncate the value
            if isinstance(value, str):
                if max_length:
                    value = value[:max_length]
                if min_length and len(value) < min_length:
                    value = value + " " * (min_length - len(value))
                return value

            if isinstance(value, datetime.datetime):
                # Handle naive dates
                if not timezone.is_aware(value):
                    value = timezone.make_aware(value)

            return value

        return method

fake = Faker()
