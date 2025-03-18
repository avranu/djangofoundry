"""
This module contains all our abstract classes for our other models to inherit from.

Every model in every application throughout our software should inherit from this Model class.

Metadata:

File: model.py
Project: Django Foundry
Created Date: 18 Aug 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Mon Apr 24 2023
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann

"""
# Generic imports
from __future__ import annotations

import logging
from typing import Iterable, Optional

# Django extensions
import auto_prefetch

# Django Imports
from django.db import models

# Lib Imports
from djangofoundry.mixins import Hookable

# Set up a logger for this module.
#
# Set up logging for this module. __name__ includes the namespace (e.g. dashboard.models.cases).
#
# We can adjust logging settings from the namespace down to the module level in DjangoFoundry/settings
#
logger = logging.getLogger(__name__)

class Model(auto_prefetch.Model, Hookable):
	"""
	An abstract class for interacting with DB tables. All models in every part of our software should inherit from this class.

	"""

	@property
	def model_name(self) -> str:
		return self.__class__.__name__

	def save(self, force_insert: bool = False, force_update: bool = False, using: Optional[str] = None, update_fields: Optional[Iterable[str]] = None) -> None:
		"""
		Override the default behavior to automatically validate the model before inserting it into the DB.
		Throw any errors returned back to the calling function
		"""
		self.presave(force_insert = force_insert, force_update = force_update, using = using, update_fields = update_fields)

		'''
		# Set defaults before full_clean
		for field in self._meta.get_fields():
			value = getattr(self, field.name)
			if value is None and (field.default is not None and field.default != NOT_PROVIDED):
				if isinstance(field.default, (str, int)) or field.default == [] or field.default == {}:
					setattr(self, field.name, field.default)
				elif field.default == list or field.default == dict:
					setattr(self, field.default())
				else:
					logger.warning('Unable to create default for %s before full_clean: %s', field.name, field.default)
		'''

		# TODO re-assess whether this (and the code above) is helpful
		#self.full_clean()

		# Let our parent handle the actual save functionality
		return super().save(force_insert, force_update, using, update_fields)

	def presave(self, **kwargs) -> None:
		"""
		Allow subclasses to define functionality before a save.

		Subclasses should override this, and call super.presave(**kwargs)

		TODO move to a signal
		"""
		# By default, do nothing
		return None

	def to_dict(self) -> dict:
		"""
		Convert this model into a dictionary of values.
		This differs from Model.__dict__ and django.forms.models.model_to_dict in the fields it includes and the labels it uses for foreign keys.
		This method, in contrast to them, returns a result which can be used in postgres bulk_inserts.
		"""
		# Start with __dict__, and filter out all fields that begin with an underscore (i.e. Model._state)
		data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

		# Use the instance's metadata to find all many-to-many fields
		opts = self._meta

		# Include many-to-many relationships
		for field in opts.many_to_many:
			# Suffix _id to keys (i.e. document_id, not document)
			# TODO there is a bug here with plurals (i.e. documents_id)
			raise NotImplementedError('For many-to-many relationships: field name suffixed with _id is not implemented for plurals.')
			"""
			data[f'{field.name}_id'] = [
				i.id for i in field.value_from_object(instance)]
			"""

		# Exclude auto values that are Null
		for field in self._meta.get_fields():
			# Don't remove actual values
			if field.name in data and data[field.name] is not None:
				continue

			# Check that it's an auto field
			match field:
				case models.AutoField() | models.BigAutoField():
					# Remove it from our values dict
					del data[field.name]

		# Return everything we found
		return data

	def get_related_models(self):
		related_models = []
		for relation in self._meta.related_objects:
			related_field_name = relation.name
			related_models.append((related_field_name, relation.related_model))
		return related_models

	def get_field_column(self, attribute_name: str) -> str:
		"""
		Gets the column name (exactly as represented in the SQL DB) of a given field
		"""
		field = self._meta.get_field(attribute_name)
		return field.column

	def get_name(self) -> str:
		"""
		A convenience method for accessing the verbose_name of this model instance

		Returns:
			str: The name of the model (stored in Meta.verbose_name)

		"""
		return self._meta.verbose_name or self._meta.model_name or self.__class__.__name__

	def get_plural_name(self) -> str:
		"""
		A convenience method for accessing the plural name of this model instance

		Returns:
			str: The plural name of the model (stored in Meta.verbose_name_plural)

		"""
		return self._meta.verbose_name_plural or self._meta.model_name or self.__class__.__name__

	def __repr__(self) -> str:
		"""
		Returns a string representation of every attribute within this model instance.

		Returns:
			str: A string representation of every attribute within this model instance

		"""
		return str(self.to_dict())

	def __str__(self) -> str:
		"""
		Returns a string representation of this model instance very simply. (e.g. Person R12345678)

		Returns:
			str: A string representation of this model instance very simply.

		"""
		return f'{self.get_name()} {self.pk}'

	class Meta(auto_prefetch.Model.Meta):
		"""
		Metadata about this model (such as the table name)

		Attributes:
			db_table (str):
				The name of the table in the DB
			unique_together (list of str):
				A list of attributes which form unique keys
			indexes (list of Index):
				A list of indexes to create on the table

		"""

		abstract = True
