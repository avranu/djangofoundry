"""

Metadata:

File: serializer.py
Project: Django Foundry
Created Date: 12 Sep 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Sat Apr 22 2023
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann
"""
# Generic imports
from __future__ import annotations

from rest_framework.serializers import ModelSerializer


class Serializer(ModelSerializer):
	"""
	A base serializer class that can be used to dynamically include or exclude fields based on context.
	"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Dynamically include or exclude fields based on context
		context = kwargs.get('context', {})
		exclude_fields = context.get('exclude_fields', [])
		include_fields = context.get('include_fields', [])

		if exclude_fields:
			for field in exclude_fields:
				if field in self.fields:
					self.fields.pop(field)

		if include_fields:
			allowed = set(include_fields)
			for field in list(self.fields):
				if field not in allowed:
					self.fields.pop(field)

	@classmethod
	def get_fieldnames(cls) -> list:
		"""
		Get a list of field names for this model.
		"""
		return cls.Meta.fields

	@classmethod
	def get_native_fields(cls) -> list:
		"""
		Get fields that are native to this model, (i.e. normal fields), not generated or calculated properties.

		Returns:
			list: A truncated list of cls.get_fieldnames()

		"""
		fields = cls.get_fieldnames()
		for field in cls.Meta.generated_fields:
			if field in fields:
				fields.remove(field)
		return fields

	class Meta:
		"""
		Serializer metadata.
		"""

		fields = [
			'id'
		]
		generated_fields = []
