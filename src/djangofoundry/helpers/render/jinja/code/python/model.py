"""

Metadata:

File: model.py
Project: Django Foundry
Created Date: 09 Apr 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Thu Apr 13 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
from __future__ import annotations

import logging
import re
from typing import Optional

# DJANGO imports
from django.db import connections
from django.db.backends.utils import CursorWrapper
from jinja2 import TemplateNotFound

from djangofoundry.helpers.render.jinja.code.python.template import PythonHelper

# LIB imports
from djangofoundry.helpers.render.meta.model import ColumnInfo, ConstraintInfo, IndexColumnInfo, IndexInfo
from djangofoundry.models import Model

# Set up logging for this module
logger = logging.getLogger(__name__)

class ModelHelper(PythonHelper):
	"""
	A helper class for rendering jinja templates that create django models.
	"""

	template_path: str = 'templates/jinja'
	_table_name : str
	_database : str
	_schema : str | None = None

	@property
	def table_name(self) -> str:
		"""
		The name of the table to generate a model for.
		"""
		return self._table_name

	@property
	def database(self) -> str:
		"""
		The name of the database to generate a model for.
		"""
		return self._database

	@property
	def schema(self) -> str | None:
		"""
		The name of the schema to generate a model for.
		"""
		return self._schema

	@property
	def connection(self):
		"""
		The django connection handler for the database to generate a model for.
		"""
		return connections[self.database]

	@property
	def cursor(self) -> CursorWrapper:
		"""
		The django connection handler cursor for the database to generate a model for.
		"""
		return self.connection.cursor()

	def __init__(self, table_name: str, database: str, schema: Optional[str] = None, app_name: str = 'lib', template_path: str = 'templates/jinja', autoescape: list = list, template_suffix: str = '.py.jinja'):
		"""
		Initializes a new instance of the ModelHelper class.

		Args:
			template_suffix (str): The suffix to use for template files (defaults to ".py.jinja")
			table_name (str): The name of the table to generate a model for

		"""
		self._table_name = table_name
		self._database = database
		self._schema = schema
		super().__init__(app_name, template_path, autoescape, template_suffix)

	def suggest_model_name(self, table_name: Optional[str] = None) -> str:
		"""
		Suggest a model name based on the DB table name

		Args:
			table_name (str): The DB table name

		Returns:
			str: The suggested model name

		"""
		if not table_name:
			table_name = self.table_name

		# Remove any prefixes or suffixes (e.g. PS_, _TMP)
		cleaned_name = self.humanize_table_name(table_name)
		result = "".join(part.capitalize() for part in cleaned_name.split(' '))
		if len(result) < 2:
			logger.warning(f'suggest_model_name too short for {table_name} -> {cleaned_name} -> {result}')
			return table_name

		return result

	def humanize_table_name(self, table_name : Optional[str] = None) -> str:
		"""
		Converts a messy table name to a cleaner, more human-readable format.

		Args:
			table_name (str): The table name to clean

		Returns:
			str: The cleaned table name

		"""
		if not table_name:
			table_name = self.table_name

		# Remove any suffixes (e.g. PS_, _TMP)
		cleaned_name = re.sub(r'_(TMP|STG|TBL|VW)[_\d]*$', '', table_name)

		# Make sure we have something left
		if not cleaned_name or len(cleaned_name) < 3:
			logger.warning(f'Could not clean table name: "{table_name}" -> "{cleaned_name}"')
			return table_name

		# Split into words, and capitalize each word
		result = re.sub(r'[\s_]+', ' ', cleaned_name).title()
		if len(result) < 2:
			logger.warning(f'humanize_name too short for {table_name} -> {cleaned_name} -> {result}')
			return table_name
		return result

	@classmethod
	def remove_duplicate_indexes(cls, indexes: list[IndexInfo]) -> list[IndexInfo]:
		"""
		Remove duplicate indexes from the list of indexes.

		Args:
			indexes (list[IndexInfo]): The list of indexes to filter

		Returns:
			list[IndexInfo]: The filtered list of indexes

		"""
		unique_indexes = []
		for index in indexes:
			if index not in unique_indexes:
				unique_indexes.append(index)
		return unique_indexes

	def get_columns(self, table_name: Optional[str] = None) -> list[ColumnInfo]:
		"""
		Get the list of columns for the given table.

		Args:
			table_name (str): The name of the table to get columns for

		Returns:
			list[ColumnInfo]: The list of columns for the given table

		"""
		if not table_name:
			table_name = self.table_name

		# Query the DB for the columns directly using connection.cursor().execute()
		with self.cursor as cursor:
			# Get the column details from the ALL_TAB_COLUMNS view
			cursor.execute(f"""
					SELECT column_name, data_type, data_length, nullable, data_default
					FROM all_tab_columns
					WHERE table_name = '{self.table_name}'
					AND owner = '{self.schema}'
				""")
			results = cursor.fetchall()

			# Convert the results to a list of ColumnInfo objects
			columns = []
			for result in results:
				# Ignore fields defined in our parent model
				parent_fields = set(dir(Model))
				if result[0] in parent_fields:
					continue

				columns.append(ColumnInfo(
					name=result[0],
					data_type=result[1],
					data_length=result[2],
					nullable=result[3],
					data_default=result[4]
				))
			return columns

	def get_constraints(self, table_name: Optional[str] = None) -> list[ConstraintInfo]:
		"""
		Get the list of constraints for the given table.

		Args:
			table_name (str): The name of the table to get constraints for

		Returns:
			list[ConstraintInfo]: The list of constraints for the given table

		"""
		if not table_name:
			table_name = self.table_name

		# Query the DB for the constraints directly using connection.cursor().execute()
		with self.cursor as cursor:
			# Get the constraint details from the ALL_CONSTRAINTS view
			cursor.execute(f"""
					SELECT SELECT cc.constraint_name, cc.column_name, c.constraint_type, c.search_condition, c.r_owner, c.r_constraint_name
					FROM all_constraints c, JOIN all_cons_columns cc ON c.constraint_name = cc.constraint_name
					WHERE table_name = '{self.table_name}'
					AND owner = '{self.schema}'
				""")
			results = cursor.fetchall()

			# Convert the results to a list of ConstraintInfo objects
			constraints = []
			for result in results:
				constraints.append(ConstraintInfo(
					name=result[0],
					column_name=result[1],
					constraint_type=result[2],
					search_condition=result[3],
					r_owner=result[4],
					r_constraint_name=result[5]
				))
			return constraints

	def get_indexes(self, table_name: Optional[str] = None) -> list[IndexInfo]:
		"""
		Get the list of indexes for the given table.

		Args:
			table_name (str): The name of the table to get indexes for

		Returns:
			list[IndexInfo]: The list of indexes for the given table

		"""
		if not table_name:
			table_name = self.table_name

		# Query the DB for the indexes directly using connection.cursor().execute()
		with self.cursor as cursor:
			# Get the index details from the ALL_INDEXES view
			cursor.execute(f"""
					SELECT i.index_name, i.column_name, i.column_position, ind.uniqueness
					FROM all_ind_columns i JOIN ALL_INDEXES ind ON i.index_name = ind.index_name AND i.index_owner = ind.owner
					WHERE i.table_name = '{self.table_name}'
					AND i.index_owner = '{self.schema}'
				""")
			results = cursor.fetchall()

			# Convert the results to a list of IndexInfo objects
			indexes = []
			for result in results:
				indexes.append(IndexInfo(
					name = result[0],
					columns = [ IndexColumnInfo( name=result[1], position=result[2] )],
					uniqueness=result[3]
				))
			return self.remove_duplicate_indexes(indexes)

	def get_row_count(self, table_name: Optional[str] = None) -> int:
		"""
		Get the row count for the given table.

		Args:
			table_name (str): The name of the table to get the row count for

		Returns:
			int: The row count for the given table

		"""
		if not table_name:
			table_name = self.table_name

		# Query the DB for the row count directly using connection.cursor().execute()
		with self.cursor as cursor:
			cursor.execute(f'SELECT COUNT(*) FROM "{self.schema}"."{self.table_name}"')
			result = cursor.fetchone()

			if not result:
				return 0

			return result[0]

	def render(self, variables: dict, template_name: str = 'model') -> str | None:
		"""
		Render a template with the given variables.

		Args:
			variables (dict): The variables to pass to the template.
			template_name (str): The name of the template to render (defaults to "model")

		Returns:
			str: The rendered template.

		"""
		try:
			template = self.env.get_template(template_name + self.template_suffix)
			return template.render(variables)
		except TemplateNotFound as e:
			logger.error(f"Template '{template_name}' not found: {str(e)}")
			return None
		except Exception as e:
			logger.error(f"Error generating code from template '{template_name}': {str(e)}")
			return None
