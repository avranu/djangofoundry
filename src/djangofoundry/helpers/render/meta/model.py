"""
Metadata:

File: model.py
Project: Django Foundry
Created Date: 11 Apr 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Fri Apr 14 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class ConstraintType(Enum):
	"""
	Possible constraints for a column in Oracle
	"""

	PRIMARY_KEY = 'P'
	UNIQUE = 'U'
	FOREIGN_KEY = 'R'
	CHECK = 'C'
	NOT_NULL = 'N'

class DbInfo:
	"""
	Store information about a structure of a database (such as a table, column, etc)

	Atributes:
		name (str): The name of the database object
	"""

	name : str

	def __init__(self, name : str, *args, **kwargs):
		self.name = name

	def __str__(self) -> str:
		"""
		Returns the name of the database object

		Returns:
			str: The name of the database object

		"""
		return self.name

	def __repr__(self) -> str:
		"""
		Returns the name of the database object

		Returns:
			str: The name of the database object

		"""
		return self.name

class TableInfo(DbInfo):
	"""
	Store information about a table in Oracle.

	Atributes:
		name (str): The name of the table
		has_model (bool): Whether or not the table has a corresponding Django model
		relevant (bool): Whether or not the table contains columns that are relevant to the project
		rows (int): The number of rows in the table
	"""

	def __init__(self, name: str, has_model: bool, relevant: bool, marked : bool, rows: int, *args, **kwargs):
		super().__init__(name)
		self.has_model = has_model
		self.relevant = relevant
		self.marked = marked
		self.rows = rows

	def to_dict(self) -> dict:
		return {
			'name': self.name,
			'has_model' : self.has_model,
			'relevant': self.relevant,
			'marked': self.marked,
			'rows': self.rows,
		}

class ColumnInfo(DbInfo):
	"""
	Store information about a column in a table in Oracle.

	Atributes:
		name (str): The name of the column
		data_type (str): The data type of the column
		data_length (int): The length of the column
		nullable (bool): Whether or not the column can be null
		default (Any): The default value of the column
		precision (int): The precision of the column
		scale (int): The scale of the column
	"""

	def __init__(
		self,
		name: str,
		data_type: str,
		data_length: int | None,
		nullable: str,
		data_default: Any = '',
		precision: Optional[int] = None,
		scale: Optional[int] = None,
	):
		super().__init__(name)
		self.data_type = data_type
		self.data_length = data_length
		self.precision = precision
		self.scale = scale
		self.default = data_default

		match nullable.lower():
			case 'y':
				self.nullable = True
			case 'n':
				self.nullable = False
			case _:
				raise ValueError(f'Unknown value for nullable: "{nullable}"')


	def get_django_field_type(self) -> str:
		"""
		Returns the corresponding Django field type based on the column's data type.

		Returns:
			str: The Django field type

		"""
		data_type_mapping = {
			"VARCHAR2": 	"CharField",
			"NVARCHAR2": 	"CharField",
			"CHAR": 		"CharField",
			"NCHAR": 		"CharField",
			"CLOB": 		"TextField",
			"NCLOB": 		"TextField",
			"NUMBER": 		"DecimalField" if self.scale and self.scale > 0 else "IntegerField",
			"DATE": 		"DateField",
			"TIMESTAMP": 	"DateTimeField",
			"TIMESTAMP WITH TIME ZONE": "DateTimeField",
			"TIMESTAMP WITH LOCAL TIME ZONE": "DateTimeField",
			"BLOB": 		"BinaryField",
			"RAW": 			"BinaryField",
			"BFILE": 		"FileField",
			"FLOAT": 		"FloatField",
		}

		return data_type_mapping.get(self.data_type.upper(), "TextField")

class ConstraintInfo(DbInfo):
	"""
	Store information about a constraint in a table in Oracle.

	Atributes:
		name (str): The name of the constraint
		constraint_type (ConstraintType): The type of constraint
		column_name (str): The name of the column that the constraint is applied to
		search_condition (str): The search condition of the constraint
		r_constraint_name (str): The name of the constraint that the constraint references
		r_owner (str): The owner of the constraint that the constraint references
		delete_rule (str): The delete rule of the constraint
		status (str): The status of the constraint
		deferrable (str): Whether or not the constraint is deferrable
		deferred (str): Whether or not the constraint is deferred
		validated (str): Whether or not the constraint is validated
		generated (str): Whether or not the constraint is generated
		last_change (str): The last time the constraint was changed
	"""

	def __init__(self, name, constraint_type: ConstraintType, column_name, search_condition : Optional[str] = None, r_constraint_name : Optional[str] = None, r_owner : Optional[Any] = None, delete_rule : Optional[str] = None, status : Optional[str] = None, deferrable : Optional[str] = None, deferred : Optional[str] = None, validated : Optional[str] = None, generated : Optional[str] = None, last_change : Optional[str] = None, *args, **kwargs):
		super().__init__(name)
		self.constraint_type = constraint_type
		self.column_name = column_name
		self.search_condition = search_condition
		self.r_constraint_name = r_constraint_name
		self.r_owner = r_owner
		self.delete_rule = delete_rule
		self.status = status
		self.deferrable = deferrable
		self.deferred = deferred
		self.validated = validated
		self.generated = generated
		self.last_change = last_change

class IndexColumnInfo(DbInfo):
	"""
	Store information about a column in an index in Oracle.

	Atributes:
		name (str): The name of the column
		position (int): The position of the column in the index
	"""

	def __init__(self, name: str, position: int):
		super().__init__(name)
		self.position = position

	def __eq__(self, other: 'IndexColumnInfo') -> bool:
		return self.name == other.name and self.position == other.position

	def __hash__(self) -> int:
		return hash((self.name, self.position))

	def __lt__(self, other: 'IndexColumnInfo') -> bool:
		return self.position < other.position

	def __le__(self, other: 'IndexColumnInfo') -> bool:
		return self.position <= other.position

	def __gt__(self, other: 'IndexColumnInfo') -> bool:
		return self.position > other.position

	def __ge__(self, other: 'IndexColumnInfo') -> bool:
		return self.position >= other.position

	def __ne__(self, other: 'IndexColumnInfo') -> bool:
		return not self.__eq__(other)

class IndexInfo(DbInfo):
	"""
	Store information about an index in Oracle.

	Atributes:
		name (str): The name of the index
		uniqueness (str): Whether or not the index is unique
		columns (list[IndexColumnInfo]): The columns in the index
	"""

	def __init__(self, name: str, columns: Optional[list[IndexColumnInfo]] = None, uniqueness: str = ''):
		if not name:
			name = f'index.{"-".join([column.name for column in columns or []])}'
		super().__init__(name)
		self.uniqueness = uniqueness
		self.columns = columns if columns is not None else []

	def add_column(self, column_name: str, column_position: int):
		"""
		Add a column to the index.

		Args:
			column_name (str): The name of the column
			column_position (int): The position of the column in the index

		Returns:
			None

		Example:
			>>> index = IndexInfo('index_name', 'UNIQUE')
			>>> index.add_column('column_name', 1)

		"""
		index_column = IndexColumnInfo(column_name, column_position)
		self.columns.append(index_column)

	def __eq__(self, other: 'IndexInfo') -> bool:
		return self.name == other.name and self.uniqueness == other.uniqueness and self.columns == other.columns

	def __hash__(self) -> int:
		return hash((self.name, self.uniqueness, tuple(self.columns)))

class ForeignKeyInfo:
	"""
	Store information about a foreign key in Oracle.

	Atributes:
		column (str): The name of the column
		constraint_type (ConstraintType): The type of constraint
		referenced_table (str): The name of the table that the foreign key references
		referenced_column (str): The name of the column that the foreign key references
		related_name (str): The name of the related name
	"""

	def __init__(self, column: str, constraint_type: ConstraintType, referenced_table: str, referenced_column: str, related_name: Optional[str] = None):
		self.column = column
		self.constraint_type = constraint_type
		self.referenced_table = referenced_table
		self.referenced_column = referenced_column
		self.related_name = related_name

	def __str__(self) -> str:
		"""
		Returns the name of the column.

		Returns:
			str: The name of the column

		"""
		return self.column

	def __repr__(self) -> str:
		"""
		Returns the name of the column.

		Returns:
			str: The name of the column

		"""
		return self.column

	def __eq__(self, other: 'ForeignKeyInfo') -> bool:
		return self.column == other.column and self.constraint_type == other.constraint_type and self.referenced_table == other.referenced_table and self.referenced_column == other.referenced_column and self.related_name == other.related_name

	def __hash__(self) -> int:
		return hash((self.column, self.constraint_type, self.referenced_table, self.referenced_column, self.related_name))


# Create a variabletype for a dictionary of constraints that can be used in type checking later.
# { 'column_name' : [ConstraintType, ConstraintType, ...] }
ConstraintDict = dict[str, list[ConstraintType]]
