"""
Metadata:

File: queryset.py
Project: Django Foundry
Created Date: 18 Aug 2022
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Tue Apr 11 2023
Modified By: Jess Mann

-----

Copyright (c) 2022 Jess Mann

"""
# Generic imports
from __future__ import annotations

import logging
import operator
from datetime import datetime
from decimal import Decimal
from functools import reduce
from math import sqrt
from time import perf_counter_ns
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union

# Django extensions
import auto_prefetch
import numpy as np
import pandas as pd

# Django Imports
from django.db.models import (
	Avg,
	BigIntegerField,
	Count,
	DecimalField,
	DurationField,
	ExpressionWrapper,
	F,
	FloatField,
	IntegerField,
	Max,
	Min,
	PositiveBigIntegerField,
	PositiveIntegerField,
	PositiveSmallIntegerField,
	Q,
	SmallIntegerField,
	StdDev,
	Sum,
)
from django.db.models.query import RawQuerySet
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import grangercausalitytests
from typing_extensions import Self

# App Imports

if TYPE_CHECKING:
	pass

#
# Set up logging for this module. __name__ includes the namespace (e.g. dashboard.models.cases).
#
# We can adjust logging settings from the namespace down to the module level in DjangoFoundry/settings
#
logger = logging.getLogger(__name__)

class QuerySet(auto_prefetch.QuerySet):
	"""
	A custom queryset. All models below will use this for interacting with results from the db.
	"""

	# A map of registered filters. This allows us to whitelist filters and then call them by their (string) name. Used primarily in Celery.
	filters: dict[str, Callable] = {}

	def is_evaluated(self) -> bool:
		"""
		Determines whether the queryset has been evaluated.

		TODO: [AUTO-366] This probably returns an unexpected result if the QS is evaluated and subseqently filtered.

		Returns:
			bool: True if the queryset was EVER evaluated, False if it has NEVER been evaluated

		Example:
			>>> qs = Case.objects.filter(processing_ms__gt=100)
			>>> qs.is_evaluated()
			False
			>>> qs.count()
			>>> qs.is_evaluated()
			True

		"""
		#return self._result_cache is not None
		raise NotImplementedError('_result_cache does not appear to exist on django querysets anymore.')

	def field_is_numeric(self, field_name: str) -> bool:
		"""
		Determines whether a field is numeric or not. This is used primarily for determining if we can perform math operations on its value.

		Args:
			field_name (str): The name of the field to check

		Returns:
			bool: True if the field is numeric, False if not

		Raises:
			ValueError: If the field does not exist on the model

		Example:
			>>> Case.objects.field_is_numeric('processing_ms')
			True
			>>> Case.objects.field_is_numeric('case_id')
			False

		"""
		if not hasattr(self.model, field_name):
			raise ValueError(f"No field '{field_name}' on queryset")

		# List of all fields that are numeric
		numeric_fields = [
			IntegerField,
			FloatField,
			DecimalField,
			BigIntegerField,
			PositiveIntegerField,
			SmallIntegerField,
			PositiveSmallIntegerField,
			DurationField,
			PositiveBigIntegerField,
		]
		attr = getattr(self.model, field_name)

		return any(isinstance(attr, field) for field in numeric_fields)

	def latest_value(self, property_name: str) -> Any:
		"""
		Attempts to get the lastest record, and returns the requested property from it. If no record is found, returns None.
		This bypasses an exception being thrown on no results.

		Args:
			property_name (str): The name of the property to get

		Returns:
			Any: The value of the property, or None if no record is found

		Example:
			>>> Case.objects.latest_value('amount')
			1000

		"""
		try:
			result = self.latest(property_name)
			return getattr(result, property_name, None)

		except Exception as _e:
			logger.debug(f"No result found for latest {property_name}")
			return None

	def min(self, property_name: str) -> Union[float, None]:
		"""
		Attempts to get the minimum value for the given property. If no record is found, returns None.
		This bypasses an exception being thrown on no results.

		Args:
			property_name (str): The name of the property to get

		Returns:
			Any: The minimum value of the property, or None if no record is found

		"""
		try:
			return self.aggregate(Min(property_name))[f'{property_name}__min']

		except Exception as _e:
			logger.debug(f"No result found for min {property_name}")
			return None

	def max(self, property_name: str) -> Union[float, None]:
		"""
		Attempts to get the maximum value for the given property. If no record is found, returns None.
		This bypasses an exception being thrown on no results.

		Args:
			property_name (str): The name of the property to get

		Returns:
			Union[float, None]: The maximum value of the property, or None if no record is found

		"""
		try:
			return self.aggregate(Max(property_name))[f'{property_name}__max']

		except Exception as _e:
			logger.debug(f"No result found for max {property_name}")
			return None

	def filter_smallest(self, property_name: str, margin: float = 0) -> Self:
		"""
		Attempts to get the entry with the smallest value for the given property.

		Args:
			property_name (str): The name of the property filter by
			margin (float): The amount of margin to allow for around the smallest value. Defaults to 0

		Returns:
			This queryset, filtered to include only results that tie for the smallest value of the given property (or are within the given margin)

		Example:
			>>> Case.objects.smallest('amount')
			<QuerySet [<Case: Case 1>]>

		"""
		min_value = self.min(property_name)
		if min_value is None:
			return self.none()

		# Reduce the queryset to only results with the smallest value for the given property, after accounting for the margin
		return self.filter(**{property_name: min_value - margin})

	def filter_largest(self, property_name: str, margin: float = 0) -> Self:
		"""
		Attempts to get the entry with the largest value for the given property.

		Args:
			property_name (str): The name of the property filter by
			margin (float): The amount of margin to allow for around the largest value. Defaults to 0

		Returns:
			This queryset, filtered to include only results that tie for the largest value of the given property

		Example:
			>>> Case.objects.largest('amount')
			<QuerySet [<Case: Case 1>]>

		"""
		max_value = self.max(property_name)
		if max_value is None:
			return self.none()

		# Reduce the queryset to only results with the largest value for the given property, after accounting for the margin
		return self.filter(**{property_name: max_value + margin})

	def has_blank(self, property_name: str, include_null: bool = True) -> Self:
		"""
		Attempts to get any entries with a blank value (or optionally null) for the given property.

		Args:
			property_name (str): The name of the property filter by
			include_null (bool): Whether or not to include null values. Defaults to True

		Returns:
			This queryset, filtered to include only results that have a blank value (or optionally null) for the given property

		"""
		if include_null:
			return self.filter(**{f'{property_name}__isnull': True}) | self.filter(**{f'{property_name}__exact': ''})

		return self.filter(**{f'{property_name}__exact': ''})

	def have_blanks(self, include_null: bool = True, number_of_blank_fields: int = 1) -> Self:
		"""
		Attempts to get any entries with a blank value (or optionally null) for any property.

		Args:
			include_null (bool): Whether or not to include null values. Defaults to True
			number_of_blank_fields (int): The number of blank fields that must be present for a record to be included. Defaults to 1

		Returns:
			This queryset, filtered to include only results that have a blank value (or optionally null) for any property

		"""
		# This is a minimum, not an exact number, so <= 0 doesn't make sense.
		if number_of_blank_fields <= 0:
			raise ValueError("Number of blank fields must be greater than 0")

		# Annotate the queryset with the number of blank fields
		# TODO not sure this is the right way to do this.
		annotated = self.annotate(blank_fields=Count('pk', filter=self.has_blank('pk', include_null=include_null)))

		# Filter the queryset to only include records with the minimum number of blank fields
		return annotated.filter(blank_fields__gte=number_of_blank_fields)

	def total(self, property_name: str) -> Union[float, int, Decimal]:
		"""
		Adds up the values of a given property and returns the result

		Args:
			property_name (str): The name of the property to sum

		Returns:
			Real: The sum of the property

		Raises:
			ValueError: If the property does not exist on the model, or if the property is not numeric

		Example:
			>>> Case.objects.total('amount')
			1000

		"""
		if not hasattr(self.model, property_name):
			raise ValueError(f"No field '{property_name}' on queryset")

		if not self.field_is_numeric(property_name):
			raise ValueError(f"Field '{property_name}' is not numeric")

		return self.aggregate(Sum(property_name))[f'{property_name}__sum'] or 0

	def request(self, request_str: str) -> Union[Self, RawQuerySet]:
		"""
		Makes a request, as a string, to be turned into a queryset
		For example: request('open recalc missing-docs') on the Cases queryset will build a query for open recalc cases with no documents.
		This is used primarily for Celery tasks, which require querysets to be represented as strings
		"""
		# Break it into individual requests
		arguments = request_str.split()

		# Start with this queryset
		qs = self

		# Iterate over all requests
		for arg in arguments:
			if arg is None or len(arg) < 1 or arg == ' ':
				raise ValueError(f'Request {request_str} returned an empty argument')

			# Build a new queryset with the single request
			qs = qs.apply_filter(arg)

			# If the queryset returned was a RawQuerySet, then we can't filter it any further
			if isinstance(qs, RawQuerySet):
				return qs

		# Give the full queryset to the calling function
		return qs

	def apply_filter(self, filter_name: str) -> Union[Self, RawQuerySet]:
		"""
		Builds a queryset by providing a string that refers to a filter.
		For example: build('open') on the Cases QuerySet will build an open cases query.
		This is used primarily for Celery tasks, which require querysets to be represented as strings

		If more complicated logic is needed, subclasses can override this method and call super().apply_filter(filter) as a fallback.
		"""
		# Try our whitelisted filters. These are generally registered using the @Queryset_Filter decorator.
		if filter_name in self.filters:
			# If it exists, run it
			result = self.filters[filter_name](self)

			# Verify that we got a result (so we can guarantee our return type)
			if not isinstance(result, QuerySet | RawQuerySet):
				raise ValueError(f"Filter {filter_name} returned the wrong type: {type(result)}")

			# Return the queryset
			return result

		# By default, no other filters are valid
		raise NotImplementedError(f'Bad Queryset filter requested: {filter_name}')

	def filter_by_related(self, foreign_key: str, filter_expression: Q, alias_name: Optional[str] = None) -> Self:
		"""
		Filters this model based on the existence of a related model with a given property

		Args:
			foreign_key (str):
				The name of the foreign key on this model
			filter_expression (Q):
				The filter to apply to the related model
			alias_name (str, optional):
				The name of the alias to use. If None is provided, we will generate one. Defaults to None.

		Returns:
			QuerySet: A filtered copy of this queryset

		Example:
			>>> Case.objects.filter_by_related('documents', Q(document_type='invoice'))
			<QuerySet [<Case: Case 1>, <Case: Case 2>]>

		"""
		# Allow for default alias names
		if alias_name is None:
			# Guarantee unique name
			time = perf_counter_ns()
			alias_name = f'alias_{foreign_key}{time}_count'

		# Create a new "field" to count all related models matching the filter
		qs = self.alias(**{f'{alias_name}_count': Count(foreign_key, filter=filter_expression)})
		# If this model has at least one of those, include it in the results
		return qs.filter(**{f'{alias_name}_count__gte': 1})

	def foreignkey_exists(self, attribute_name: str) -> Self:
		"""
		Filters this queryset to only include objects that have a non-null foreign key.

		Args:
			attribute_name (str): The name of the attribute to check

		Returns:
			QuerySet: A filtered copy of this queryset

		Example:
			>>> Case.objects.foreignkey_exists('assigned_to')
			<QuerySet [<Case: Case 1>, <Case: Case 2>, <Case: Case 3>]>

		"""
		return self.filter(**{f'{attribute_name}__isnull': False})

	def summarize_x_by_average_y(self, x_field_name: str, y_field_name: str) -> dict[str, float]:
		"""
		Summarizes the values of a given field. This is used to summarize the values of a field in a queryset.
		For example, if we have a queryset of cases, we get a list of statuses mapped to the average processing time for each status.

		Args:
			x_field_name (str): The name of the field to summarize
			y_field_name (str): The name of the field to average

		Returns:
			dict[str, float]: A dictionary mapping the values of the x field to the average of the y field

		Raises:
			ValueError: If the x or y field is not a valid field

		Example:
			>>> Case.objects.summarize_x_by_average_y('status', 'processing_time')
			{ 'open': 1.5, 'closed': 2.0 }

		"""
		summary_data = (self.values(x_field_name).annotate(count=Avg(y_field_name)).order_by(x_field_name))
		return {result[x_field_name]: result['count'] for result in summary_data}

	def summarize_x_by_sum_y(self, x_field_name: str, y_field_name: str) -> dict[str, float]:
		"""
		Summarizes the values of a given field. This is used to summarize the values of a field in a queryset.
		For example, if we have a queryset of cases, we get a list of statuses mapped to the total processing time for each status.

		Args:
			x_field_name (str): The name of the field to summarize
			y_field_name (str): The name of the field to sum

		Returns:
			dict[str, float]: A dictionary mapping the values of the x field to the sum of the y field

		Raises:
			ValueError: If the x or y field is not a valid field

		Example:
			>>> Case.objects.summarize_x_by_sum_y('status', 'processing_time')
			{ 'open': 3.0, 'closed': 2.5 }

		"""
		summary_data = (self.values(x_field_name).annotate(count=Sum(y_field_name)).order_by(x_field_name))
		return {result[x_field_name]: result['count'] for result in summary_data}

	def summarize_x_by_high_y(self, x_field_name: str, y_field_name: str) -> dict[str, int]:
		"""
		Summarizes the values of a given field. This is used to summarize the values of a field in a queryset.
		For example, if we have a queryset of cases, we get a list of statuses mapped to the top half processing time for each status.
		This will always get half the dataset.

		Args:
			x_field_name (str): The name of the field to summarize
			y_field_name (str): The name of the field to require being higher than the average

		Returns:
			dict[str, float]: A dictionary mapping the values of the x field to a count of entries that have a higher than average y field.

		Raises:
			ValueError: If the x or y field is not a valid field

		Example:
			>>> Case.objects.summarize_x_by_high_y('status', 'processing_time')
			{ 'open': 2, 'closed': 5 }

		"""
		summary_data = (self.values(x_field_name).annotate(count=Count(y_field_name, filter=Q(**{f"{y_field_name}__gt": Avg(y_field_name)}))).order_by(x_field_name))

		return {result[x_field_name]: result['count'] for result in summary_data}

	def summarize_x_by_low_y(self, x_field_name: str, y_field_name: str) -> dict[str, int]:
		"""
		Summarizes the values of a given field. This is used to summarize the values of a field in a queryset.
		For example, if we have a queryset of cases, we get a list of statuses mapped to a count of entries that have a lower than average processing time for each status.

		Args:
			x_field_name (str): The name of the field to summarize
			y_field_name (str): The name of the field to require being lower than the average

		Returns:
			dict[str, float]: A dictionary mapping the values of the x field to a count of entries that have a lower than average y field.

		Raises:
			ValueError: If the x or y field is not a valid field

		Example:
			>>> Case.objects.summarize_x_by_low_y('status', 'processing_time')
			{ 'open': 1, 'closed': 3 }

		"""
		summary_data = (self.values(x_field_name).annotate(count=Count(y_field_name, filter=Q(**{f"{y_field_name}__lt": Avg(y_field_name)}))).order_by(x_field_name))

		return {result[x_field_name]: result['count'] for result in summary_data}

	def anomalies_in(self, field_name: str, deviations: int = 2) -> Self:
		"""
		Finds anomalies in a field. This is used to find anomalies in a field in a queryset.
		For example, if we have a queryset of cases, we get a list of anomalies in the processing time field.

		Args:
			field_name (str): The name of the field to find anomalies in
			deviations (int): The number of standard deviations above the average to consider an anomaly

		Returns:
			Self: A queryset of anomalies

		Raises:
			ValueError: If the field is not a valid field

		Example:
			>>> Case.objects.anomalies_in('processing_time')
			<QuerySet [<Case: Case 1>, <Case: Case 2>]>

		"""
		# Get the average and standard deviation of the field
		avg = self.aggregate(Avg(field_name))[f"{field_name}__avg"]
		std = self.aggregate(StdDev(field_name))[f"{field_name}__stddev"]

		# Get the anomalies (2 standard deviations above the average)
		return self.filter(**{f"{field_name}__gt": avg + deviations * std})

	def summarize_distribution(self, field_name: str, bins: int = 10) -> dict[int, int]:
		"""
		Summarizes the distribution of a field. This is used to summarize the distribution of a field in a queryset.
		For example, if we have a queryset of cases, we get a list of the distribution of the processing time field.

		Args:
			field_name (str): The name of the field to find anomalies in
			bins (int): The number of bins to use when summarizing the distribution

		Returns:
			dict[int, int]: A dictionary mapping the bins to the number of entries in that bin

		Raises:
			ValueError: If the field is not a valid field

		Example:
			>>> Case.objects.summarize_distribution('processing_time', 5)
			{ 0: 1, 1: 2, 2: 1, 3: 1, 4: 1 }

		"""
		# Get the min and max of the field
		min_value = self.aggregate(Min(field_name))[f"{field_name}__min"]
		max_value = self.aggregate(Max(field_name))[f"{field_name}__max"]

		# Get the distribution
		distribution = (self.values(field_name).annotate(bin=ExpressionWrapper(F(field_name) - min_value, output_field=IntegerField()) // ((max_value - min_value) // bins)).values("bin").annotate(count=Count("bin")).order_by("bin"))

		return {result["bin"]: result["count"] for result in distribution}

	def summarize_x_by_y_distribution(self, x_field_name: str, y_field_name: str, bins: int = 10) -> dict[str, dict[int, int]]:
		"""
		Summarizes the distribution of a field by another field. This is used to summarize the distribution of a field in a queryset by another field.
		For example, if we have a queryset of cases, we get a list of the distribution of the processing time field by status.

		Args:
			x_field_name (str): The name of the field to summarize
			y_field_name (str): The name of the field to summarize by
			bins (int): The number of bins to use when summarizing the distribution

		Returns:
			dict[str, dict[int, int]]: A dictionary mapping the values of the x field to a dictionary mapping the bins to the number of entries in that bin

		Raises:
			ValueError: If the x or y field is not a valid field

		Example:
			>>> Case.objects.summarize_x_by_distribution('status', 'processing_time', 5)
			{ 'open': { 0: 1, 1: 1, 2: 1, 3: 1, 4: 1 }, 'closed': { 0: 1, 1: 1, 2: 1, 3: 1, 4: 1 } }

		"""
		# Get the min and max of the field
		min_value = self.aggregate(Min(y_field_name))[f"{y_field_name}__min"]
		max_value = self.aggregate(Max(y_field_name))[f"{y_field_name}__max"]

		# Get the distribution
		distribution = (self.values(x_field_name, y_field_name).annotate(bin=ExpressionWrapper(F(y_field_name) - min_value, output_field=IntegerField()) // ((max_value - min_value) // bins)).values(x_field_name,
																																																			 "bin").annotate(count=Count("bin")).order_by(x_field_name, "bin"))

		# Convert the distribution to a dictionary
		distribution_dict = {}
		for result in distribution:
			if result[x_field_name] not in distribution_dict:
				distribution_dict[result[x_field_name]] = {}

			distribution_dict[result[x_field_name]][result["bin"]] = result["count"]

		return distribution_dict

	def count_unique(self, field_name: str) -> int:
		"""
		Counts the number of unique values in a field.

		Args:
			field_name (str): The name of the field to count the unique values of

		Returns:
			int: The number of unique values in the field

		Example:
			>>> Case.objects.count_unique('status')
			2

		"""
		unique_count = self.aggregate(unique_count=Count(field_name, distinct=True))['unique_count']
		return unique_count

	def count_x_by_unique_y(self, field_name_x: str, field_name_y: str) -> dict[str, int]:
		"""
		Counts entries in groups of X, only including those which have a unique Y.

		For example: Count the number of cases that have a unique location, grouped by status.

		Args:
			field_name_x (str): The name of the field to summarize (or group by)
			field_name_y (str): The name of the field to find unique values for.

		Returns:
			dict[str, int]: A dictionary mapping the values of the x field to the number of y field entries that are unique

		Example:
			>>> Case.objects.count_x_by_unique_y('status', 'location')
			{ 'open': 1, 'closed': 0 }

		"""
		# Annotate entries that have a unique y_field
		unique_qs = self.values(field_name_x, field_name_y).annotate(unique=Count(field_name_y, distinct=True))

		# Get a count of entries, grouped by x_field
		counts = unique_qs.values(field_name_x).annotate(count=Count(field_name_x))

		# Convert the counts to a dictionary
		return {result[field_name_x]: result['count'] for result in counts}

	def median(self, field_name: str) -> float | None:
		"""
		Get the median value of a field.

		The median represents the middle value of the field.
		If there are an even number of entries, the median is the average of the two middle values.

		Args:
			field_name (str): The name of the field to get the median of

		Returns:
			float: The median value of the field

		Example:
			>>> Case.objects.median('processing_time')
			1.5

		"""
		row_count = self.count()
		if not row_count:
			return None

		median_index = row_count // 2
		if row_count % 2 == 1:
			median_value = self.order_by(field_name).values_list(field_name, flat=True)[median_index]
		else:
			median_value = (self.order_by(field_name).values_list(field_name, flat=True)[median_index - 1:median_index + 1].aggregate(median_value=Avg(ExpressionWrapper(F(field_name), output_field=FloatField())))["median_value"])
		return median_value

	def filter_median(self, field_name: str, deviation: int = 0) -> Self:
		"""
		Filter the queryset to only include entries that are the median value of the field.

		The median represents the middle value of the field.
		If there are an even number of entries, the median is the average of the two middle values.

		Args:
			field_name (str): The name of the field to filter by the median of
			deviation (int): The number of standard deviations away from the median to include

		Returns:
			Self: The filtered queryset

		Example:
			>>> Case.objects.filter_median('processing_time')
			<QuerySet [<Case: Case 1>, <Case: Case 2>]>

		"""
		median = self.median(field_name)
		if median is None:
			logger.error(f"Unable to calculate median for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		# If deviation is 0, we can skip calculating the deviation
		if not deviation:
			return self.filter(**{field_name: median})

		standard_deviation = self.standard_deviation(field_name)
		if standard_deviation is None:
			logger.error(f"Unable to calculate standard deviation for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		return self.filter(**{f"{field_name}__gte": median - (standard_deviation * deviation), f"{field_name}__lte": median + (standard_deviation * deviation)})

	def percentile(self, field_name: str, percentile: float) -> float | None:
		"""
		Get the percentile value of a field.

		The percentile represents the value at which a certain percentage of the data is below that value.
		For example, the 0.5 percentile is the value at which 50% of the data is below that value.

		It is useful for identifying outliers.

		Args:
			field_name (str): The name of the field to get the percentile of
			percentile (float): The percentile to get

		Returns:
			float: The percentile value of the field

		Example:
			>>> Case.objects.percentile('processing_time', 0.5)
			1.5

		"""
		row_count = self.count()
		if not row_count:
			return None

		percentile_index = int(row_count * percentile)
		percentile_value = self.order_by(field_name).values_list(field_name, flat=True)[percentile_index]
		return percentile_value

	def filter_percentile(self, field_name: str, percentile: float, deviation: int = 0) -> Self:
		"""
		Filter the queryset to only include entries that are the percentile value of the field.

		The percentile represents the value at which a certain percentage of the data is below that value.
		For example, the 0.5 percentile is the value at which 50% of the data is below that value.

		It is useful for identifying outliers.

		Args:
			field_name (str): The name of the field to filter by the percentile of
			percentile (float): The percentile to filter by
			deviation (int): The number of standard deviations away from the percentile to include

		Returns:
			Self: The filtered queryset

		Example:
			>>> Case.objects.filter_percentile('processing_time', 0.5)
			<QuerySet [<Case: Case 1>, <Case: Case 2>]>

		"""
		result = self.percentile(field_name, percentile)
		if result is None:
			logger.error(f"Unable to calculate percentile for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		# If deviation is 0, we can skip calculating the deviation
		if not deviation:
			return self.filter(**{field_name: result})

		standard_deviation = self.standard_deviation(field_name)
		if standard_deviation is None:
			logger.error(f"Unable to calculate standard deviation for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		return self.filter(**{f"{field_name}__gte": result - (standard_deviation * deviation), f"{field_name}__lte": result + (standard_deviation * deviation)})

	def mode(self, field_name: str) -> float:
		"""
		Get the mode value of a field.

		The mode represents the value that occurs most frequently in a set of data.

		Args:
			field_name (str): The name of the field to get the mode of

		Returns:
			float: The mode value of the field

		Example:
			>>> Case.objects.mode('status')
			'open'

		"""
		# Get the count of each value
		value_counts = self.values(field_name).annotate(count=Count(field_name))

		# Get the value with the highest count
		mode_value = max(value_counts, key=lambda result: result['count'])[field_name]
		return mode_value

	def filter_mode(self, field_name: str, deviation: int = 0) -> Self:
		"""
		Filter the queryset to only include entries that are the mode value of the field.

		The mode is the value that occurs most frequently in a set of data.

		Args:
			field_name (str): The name of the field to filter by the mode of
			deviation (int): The number of standard deviations away from the mode to include

		Returns:
			Self: The filtered queryset

		Example:
			>>> Case.objects.filter_mode('status')
			<QuerySet [<Case: Case 1>, <Case: Case 2>]>

		"""
		mode = self.mode(field_name)
		if mode is None:
			logger.error(f"Unable to calculate mode for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		# If deviation is 0, we can skip calculating the deviation
		if not deviation:
			return self.filter(**{field_name: mode})

		standard_deviation = self.standard_deviation(field_name)
		if standard_deviation is None:
			logger.error(f"Unable to calculate standard deviation for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		return self.filter(**{f"{field_name}__gte": mode - (standard_deviation * deviation), f"{field_name}__lte": mode + (standard_deviation * deviation)})

	def mean(self, field_name: str) -> float:
		"""
		Get the mean (average) of a field.

		Args:
			field_name (str): The name of the field to get the mean of

		Returns:
			float: The mean of the field

		Example:
			>>> Case.objects.mean('processing_time')
			1.5

		"""
		mean = self.aggregate(mean=Avg(field_name))['mean']
		return mean

	def filter_mean(self, field_name: str, deviation: int = 0) -> Self:
		"""
		Filter the queryset to only include entries that are the mean (average) value of the field.

		Args:
			field_name (str): The name of the field to filter by the mean of
			deviation (int): The number of standard deviations away from the mean to include

		Returns:
			Self: The filtered queryset

		Example:
			>>> Case.objects.filter_mean('processing_time')
			<QuerySet [<Case: Case 1>, <Case: Case 2>]>

		"""
		mean = self.mean(field_name)
		if mean is None:
			logger.error(f"Unable to calculate mean for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		# If deviation is 0, we can skip calculating the deviation
		if not deviation:
			return self.filter(**{field_name: mean})

		standard_deviation = self.standard_deviation(field_name)
		if standard_deviation is None:
			logger.error(f"Unable to calculate standard deviation for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		return self.filter(**{f"{field_name}__gte": mean - (standard_deviation * deviation), f"{field_name}__lte": mean + (standard_deviation * deviation)})

	def mean_nonzero(self, field_name: str) -> float:
		"""
		Get the mean (average) of a field, ignoring zero values.

		Args:
			field_name (str): The name of the field to get the mean of

		Returns:
			float: The mean of the field, ignoring zero values

		Example:
			>>> Case.objects.mean_nonzero('processing_time')
			1.5

		"""
		mean = self.exclude(**{field_name: 0}).aggregate(mean=Avg(field_name))['mean']
		return mean

	def filter_mean_nonzero(self, field_name: str, deviation: int = 0) -> Self:
		"""
		Filter the queryset to only include entries that are the mean value of the field, ignoring zero values.

		Args:
			field_name (str): The name of the field to filter by the mean of
			deviation (int): The number of standard deviations away from the mean to include

		Returns:
			Self: The filtered queryset

		Example:
			>>> Case.objects.filter_mean_nonzero('processing_time')
			<QuerySet [<Case: Case 1>, <Case: Case 2>]>

		"""
		mean = self.mean_nonzero(field_name)
		if mean is None:
			logger.error(f"Unable to calculate mean for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		# If deviation is 0, we can skip calculating the deviation
		if not deviation:
			return self.filter(**{field_name: mean})

		standard_deviation = self.standard_deviation(field_name)
		if standard_deviation is None:
			logger.error(f"Unable to calculate standard deviation for field {field_name} in queryset {self.model.__name__}")
			return self.none()

		return self.filter(**{f"{field_name}__gte": mean - (standard_deviation * deviation), f"{field_name}__lte": mean + (standard_deviation * deviation)})

	def variance(self, field_name: str) -> float:
		"""
		Get the variance of a field.

		The variance represents how spread out the values are from the mean.
		The variance is a range from 0 to 1. A variance of 0 means all values are the same, and a variance of 1 means all values are different.

		The variance can be used to filter out outliers. If the variance is 0.5, then the values are spread out by 50% of the mean.
		For example, by calculating the variance of the processing time of cases, we can filter out cases that took more than 50% longer than the average.

		Args:
			field_name (str): The name of the field to get the variance of

		Returns:
			float: The variance of the field

		Example:
			>>> Case.objects.variance('processing_time')
			0.5

		"""
		# Get the mean of the field
		mean = self.aggregate(mean=Avg(field_name))['mean']

		# Get the variance
		variance = self.aggregate(variance=Avg((F(field_name) - mean)**2))['variance']
		return variance

	def standard_deviation(self, field_name: str) -> float:
		"""
		Get the standard deviation of a field.

		Args:
			field_name (str): The name of the field to get the standard deviation of

		Returns:
			float: The standard deviation of the field

		Example:
			>>> Case.objects.standard_deviation('processing_time')
			0.7071067811865476

		"""
		# Get the variance
		variance = self.variance(field_name)

		# Get the standard deviation
		standard_deviation = sqrt(variance)
		return standard_deviation

	def covariance(self, field_name_x: str, field_name_y: str) -> float:
		"""
		Get the covariance of two fields.

		The covariance is a measure of how much two fields vary together.
		If the covariance is positive, the fields tend to increase together.
		If the covariance is negative, the fields tend to decrease together.
		If the covariance is zero, the fields are independent.

		For example, if the processing time of a case increases, the number of steps in the case also tends to increase.

		Args:
			field_name_x (str): The name of the first field to get the covariance of
			field_name_y (str): The name of the second field to get the covariance of

		Returns:
			float: The covariance of the two fields

		Example:
			>>> Case.objects.covariance('processing_time', 'processing_time')
			0.5

		"""
		# Get the mean of the fields
		mean_x = self.aggregate(mean=Avg(field_name_x))['mean']
		mean_y = self.aggregate(mean=Avg(field_name_y))['mean']

		# Get the covariance
		covariance = self.aggregate(covariance=Avg((F(field_name_x) - mean_x) * (F(field_name_y) - mean_y)))['covariance']
		return covariance

	def correlation(self, field_name_x: str, field_name_y: str) -> float:
		"""
		Get the correlation of two fields.

		The correlation represents how strongly two fields are related.

		A higher correlation means that the two fields are more strongly related.
		A lower correlation means that the two fields are less strongly related.

		The correlation is a value between -1 and 1. A correlation of 1 means that the two fields are perfectly correlated.

		Args:
			field_name_x (str): The name of the first field to get the correlation of
			field_name_y (str): The name of the second field to get the correlation of

		Returns:
			float: The correlation of the two fields

		Example:
			>>> Case.objects.correlation('processing_time', 'processing_time')
			1.0

		"""
		# Get the standard deviation of the fields
		standard_deviation_x = self.standard_deviation(field_name_x)
		standard_deviation_y = self.standard_deviation(field_name_y)

		# Get the correlation
		correlation = self.covariance(field_name_x, field_name_y) / (standard_deviation_x * standard_deviation_y)
		return correlation

	def find_correlated_fields(self, field_name: str, threshold: float = 0.5) -> list[str]:
		"""
		Find the fields that are correlated with a given field.

		Args:
			field_name (str): The name of the field to find correlated fields of
			threshold (float): The minimum correlation to consider a field correlated

		Returns:
			list[str]: The names of the fields that are correlated with the given field

		Example:
			>>> Case.objects.find_correlated_fields('processing_time')
			['tasks']

		"""
		# Get the correlation of the field with every other field
		correlations = {correlated_field_name: self.correlation(field_name, correlated_field_name) for correlated_field_name in self.model._meta.get_fields() if (field_name != correlated_field_name and self.field_is_numeric(correlated_field_name))}
		correlations = {correlated_field_name: correlation for correlated_field_name, correlation in correlations.items() if correlation >= threshold}

		# Sort the correlations by their correlation
		correlations = sorted(correlations.items(), key=lambda item: item[1], reverse=True)

		# Return the names of the correlated fields
		return [correlated_field_name for correlated_field_name, _correlation in correlations]

	def linear_regression(self, field_name_x: str, field_name_y: str) -> Tuple[float, float]:
		"""
		Get the linear regression of two fields.

		The linear regression is a tuple of the slope and y-intercept of the line of best fit.
		It is useful for predicting the value of one field given the value of another field.

		For example, you can use the linear regression of an employee's income and their age to predict the income of an employee given their age.

		Here are several more examples of linear regressions:
			Predicting the processing time of a case given the number of cases in the queue
			Predicting an employee's income given the number of years they have been employed
			Predicting the time it will take to complete all remaining cases given the number of cases completed so far

		Args:
			field_name_x (str): The name of the first field to get the linear regression of
			field_name_y (str): The name of the second field to get the linear regression of

		Returns:
			Tuple[float, float]: The linear regression of the two fields

		Example:
			>>> Case.objects.linear_regression('processing_time', 'processing_time')
			(0.0, 1.0)

		"""
		# Get the correlation
		correlation = self.correlation(field_name_x, field_name_y)

		# Get the standard deviation of the fields
		standard_deviation_x = self.standard_deviation(field_name_x)
		standard_deviation_y = self.standard_deviation(field_name_y)

		# Get the mean of the fields
		mean_x = self.aggregate(mean=Avg(field_name_x))['mean']
		mean_y = self.aggregate(mean=Avg(field_name_y))['mean']

		# Get the linear regression
		slope = correlation * (standard_deviation_y / standard_deviation_x)
		intercept = mean_y - (slope * mean_x)
		return slope, intercept

	def linear_regression_prediction(self, field_name_x: str, field_name_y: str, x: float) -> float:
		"""
		Get the linear regression prediction of two fields.

		The linear regression prediction is the value of one field given the value of another field.

		Here are several examples of linear regression predictions:
			Predicting the processing time of a case given the number of cases in the queue
			Predicting an employee's income given the number of years they have been employed
			Predicting the time it will take to complete all remaining cases given the number of cases completed so far

		Args:
			field_name_x (str): The name of the first field to get the linear regression prediction of
			field_name_y (str): The name of the second field to get the linear regression prediction of
			x (float): The value to predict

		Returns:
			float: The linear regression prediction of the two fields

		Example:
			>>> Case.objects.linear_regression_prediction('processing_time', 'processing_time', 1.0)
			1.0

		"""
		# Get the linear regression
		slope, intercept = self.linear_regression(field_name_x, field_name_y)

		# Get the linear regression prediction
		y = (slope * x) + intercept
		return y

	def linear_regression_residuals(self, field_name_x: str, field_name_y: str) -> list[float]:
		"""
		Get the linear regression residuals of two fields.

		The linear regression residuals are the difference between the actual value and the predicted value.
		They are useful for determining the accuracy of the linear regression.

		Args:
			field_name_x (str): The name of the first field to get the linear regression residuals of
			field_name_y (str): The name of the second field to get the linear regression residuals of

		Returns:
			list[float]: The linear regression residuals of the two fields

		Example:
			>>> Case.objects.linear_regression_residuals('processing_time', 'processing_time')
			[0.0, 0.0, 0.0, 0.0, 0.0]

		"""
		# Get the linear regression
		slope, intercept = self.linear_regression(field_name_x, field_name_y)

		# Get the linear regression residuals
		residuals = []
		for entry in self:
			residuals.append(entry[field_name_y] - ((slope * entry[field_name_x]) + intercept))
		return residuals

	def linear_regression_deviation(self, field_name_x: str, field_name_y: str) -> float:
		"""
		Get the standard deviation of the linear regression residuals of two fields.

		The standard deviation of the linear regression residuals is useful for determining the overall accuracy of the linear regression.

		Args:
			field_name_x (str): The name of the first field to use in the linear regression
			field_name_y (str): The name of the second field to use in the linear regression

		Returns:
			float: The standard deviation of the linear regression residuals of the two fields

		Example:
			>>> Case.objects.linear_regression_deviation('processing_time', 'processing_time')
			0.0

		"""
		# Get the linear regression residuals
		residuals = self.linear_regression_residuals(field_name_x, field_name_y)

		# Get the standard deviation of the linear regression residuals
		standard_deviation = self.aggregate(standard_deviation=StdDev(residuals))['standard_deviation']
		return standard_deviation

	def random_sample(self, sample_size: int) -> Self:
		"""
		Get a random sample of the entries.

		Args:
			sample_size (int): The size of the sample

		Returns:
			Self: The random sample of the entries

		Example:
			>>> Case.objects.random_sample(5)
			[<Case: Case object (1)>, <Case: Case object (2)>, <Case: Case object (3)>, <Case: Case object (4)>, <Case: Case object (5)>]

		"""
		# Get the random sample
		entries = self.order_by('?')[:sample_size]
		return entries

	def search(self, search_term: str, fields: Optional[list[str]] = None) -> Self:
		"""
		Get the entries that match the search term.

		Args:
			search_term (str): The search term to filter by
			fields (list[str]): The fields to search

		Returns:
			Self: The entries that match the search term

		Example:
			>>> Case.objects.filter_by_search('search term')
			[<Case: Case object (1)>, <Case: Case object (2)>, <Case: Case object (3)>, <Case: Case object (4)>, <Case: Case object (5)>]

		"""
		# Get the entries that match the search term
		if fields is None:

			# Get fields that are searchable
			fields = [field.name for field in self.model._meta.get_fields() if not field.is_relation]

		entries = self.filter(Q(**{f'{format(field)}__icontains': search_term}) for field in fields)
		return entries

	def annotate_duration(self, start_field: str, end_field: str, alias: str = 'duration') -> Self:
		"""
		Annotate the entries with the duration between two fields.

		Args:
			start_field (str): The name of the start field
			end_field (str): The name of the end field
			alias (str): The name of the alias, defaults to 'duration'

		Returns:
			Self: The annotated entries

		Example:
			>>> Case.objects.annotate_duration('start_time', 'end_time', 'duration')
			[<Case: Case object (1)>, <Case: Case object (2)>, <Case: Case object (3)>, <Case: Case object (4)>, <Case: Case object (5)>]

		"""
		# Annotate the entries with the duration between two fields
		entries = self.annotate(**{alias: F(end_field) - F(start_field)})
		return entries

	def date_range(self, start_date: datetime, end_date: datetime, date_field: str) -> Self:
		"""
		Get the entries within a date range.

		Args:
			start_date (datetime): The start date
			end_date (datetime): The end date
			date_field (str): The name of the date field

		Returns:
			Self: The entries within the date range

		Example:
			>>> Case.objects.date_range(datetime(2020, 1, 1), datetime(2020, 1, 31), 'date')
			[<Case: Case object (1)>, <Case: Case object (2)>, <Case: Case object (3)>, <Case: Case object (4)>, <Case: Case object (5)>]

		"""
		# Get the entries within a date range
		entries = self.filter(**{f"{format(date_field)}__range": [start_date, end_date]})
		return entries

	def rolling_mean(self, field_name: str, window: int) -> list[float]:
		"""
		Get the rolling mean of a field.

		The rolling mean represents the average of the last n values, where n is the window size.

		It is useful for smoothing out the data and removing noise.

		Args:
			field_name (str): The name of the field
			window (int): The size of the window

		Returns:
			list[float]: The rolling mean of the field

		"""
		data = self.values_list(field_name, flat=True)
		return pd.Series(data).rolling(window=window).mean().tolist()

	def exponential_smoothing(self, field_name: str, alpha: float) -> list[float]:
		"""
		Get the exponential smoothing of a field.

		Args:
			field_name (str): The name of the field
			alpha (float): The smoothing factor

		Returns:
			list[float]: The exponential smoothing of the field

		"""
		data = self.values_list(field_name, flat=True)
		return pd.Series(data).ewm(alpha=alpha).mean().tolist()

	def seasonal_decomposition(self, field_name: str, freq: int) -> Tuple[list[float], list[float], list[float]]:
		"""
		Get the seasonal decomposition of a field.

		The seasonal decomposition represents the trend, seasonal, and residual components of the data.

		It is useful for identifying the trend, seasonality, and noise in the data.

		Args:
			field_name (str): The name of the field
			freq (int): The frequency of the data

		Returns:
			Tuple[list[float], list[float], list[float]]: The trend, seasonal, and residual components

		"""
		data = self.values_list(field_name, flat=True)
		decomposition = seasonal_decompose(data, period=freq)
		return decomposition.trend.tolist(), decomposition.seasonal.tolist(), decomposition.resid.tolist()

	def autocorrelation(self, field_name: str, lag: int) -> float:
		"""
		Get the autocorrelation of a field.

		The autocorrelation represents the correlation between the field and a lagged version of itself.
		It is useful for identifying the strength of the relationship between the field and a lagged version of itself.

		The autocorrelation is a range between -1 and 1, where:
			1 is a perfect positive correlation,
			0 is no correlation
			-1 is a perfect negative correlation.

		Args:
			field_name (str): The name of the field
			lag (int): The lag

		Returns:
			float: The autocorrelation of the field

		Example:
			>>> Case.objects.autocorrelation('field', 1)
			0.5

		"""
		data = self.values_list(field_name, flat=True)
		return pd.Series(data).autocorr(lag=lag)

	def partial_autocorrelation(self, field_name: str, lag: int) -> Any:
		"""
		Get the partial autocorrelation of a field.

		The partial autocorrelation differs from the autocorrelation in that it removes the effect of the intermediate lags.
		It is useful for identifying the strength of the relationship between the field and a lagged version of itself,
		while controlling for the values of the intermediate lags.

		A sample usecase for a partial autocorrelation would be a case where the data is seasonal, so the autocorrelation would be high for the seasonal lag.

		Args:
			field_name (str): The name of the field
			lag (int): The lag

		Returns:
			float: The partial autocorrelation of the field (TODO)

		Example:
			>>> Case.objects.partial_autocorrelation('field', 1)
			0.5

		"""
		from statsmodels.tsa.stattools import pacf
		data = self.values_list(field_name, flat=True)
		return pacf(data, nlags=lag)[lag]

	def granger_causality(self, field_name_x: str, field_name_y: str, max_lag: int) -> list[float]:
		"""
		Get the granger causality of two fields.

		The granger causality represents the likelihood that the field x causes the field y.
		It is useful for identifying the likelihood that the field x causes the field y.

		The granger causality is a range between 0 and 1, where:
			0 is no causality
			1 is perfect causality.

		Args:
			field_name_x (str): The name of the field x
			field_name_y (str): The name of the field y
			max_lag (int): The maximum lag

		Returns:
			list[float]: The granger causality of the two fields

		Example:
			>>> Case.objects.granger_causality('field_x', 'field_y', 1)
			[0.5]

		"""
		data_x = self.values_list(field_name_x, flat=True)
		data_y = self.values_list(field_name_y, flat=True)
		data = pd.DataFrame({'x': data_x, 'y': data_y})
		results = grangercausalitytests(data, max_lag, verbose=False)
		return [result[0]['ssr_ftest'][1] for result in results.values()]

	def cumulative_sum(self, field_name: str) -> list[float]:
		"""
		Calculate the cumulative sum of a field.

		The cumulative sum represents the sum of the field up to the current row.

		Args:
			field_name (str): The name of the field

		Returns:
			list[float]: The cumulative sum of the field

		Example:
			>>> Case.objects.cumulative_sum('field')
			[1, 3, 6]

		"""
		data = self.values_list(field_name, flat=True)
		return pd.Series(data).cumsum().tolist()

	def z_score(self, field_name: str) -> list[float]:
		"""
		Calculate the z-score of a field.

		The z-score represents the number of standard deviations away from the mean of the field.

		It is useful for identifying outliers in the data.

		Args:
			field_name (str): The name of the field

		Returns:
			list[float]: The z-score of the field

		Example:
			>>> Case.objects.z_score('field')
			[1.1, 3.5, 6.0]

		"""
		data = self.values_list(field_name, flat=True)
		return stats.zscore(data).tolist()

	def iqr_outliers(self, field_name: str, multiplier: float = 1.5) -> Self:
		"""
		Calculate the interquartile range (IQR) of a field.

		The IQR represents the range between the first and third quartile of the field.

		Args:
			field_name (str): The name of the field
			multiplier (float): The multiplier to use for the IQR

		Returns:
			list[float]: The IQR of the field

		Example:
			>>> Case.objects.iqr_outliers('field')
			<QuerySet [<Case: Case object (1)>, <Case: Case object (2)>]>

		"""
		data = list(self.values_list(field_name, flat=True))
		q1 = np.percentile(data, 25)
		q3 = np.percentile(data, 75)
		iqr = q3 - q1
		lower_bound = q1 - multiplier * iqr
		upper_bound = q3 + multiplier * iqr
		return self.filter(**{f"{field_name}__gte": lower_bound, f"{field_name}__lte": upper_bound})

	def filter_anomalies_in(self, field_name: str, method: Union[str, None] = None, z_threshold: float = 2, iqr_multiplier: float = 1.5) -> Self:
		"""
		Detect anomalies in a field.

		Anomalies are identified using the z-score and interquartile range (IQR) methods.

		Args:
			field_name (str): The name of the field
			method (str): The method to use for detecting anomalies. Can be 'z_score', 'iqr' or None (default)
			z_threshold (float): The threshold to use for the z-score method
			iqr_multiplier (float): The multiplier to use for the IQR method

		Returns:
			QuerySet: The anomalies

		Example:
			>>> Case.objects.detect_anomalies('field')
			<QuerySet [<Case: Case object (1)>, <Case: Case object (2)>]>

		"""
		if method == 'z_score':
			return self.filter(self.get_zscore_Q(field_name, z_threshold))

		if method == 'iqr':
			return self.filter(self.get_iqr_Q(field_name, iqr_multiplier))

		if method is None:
			combined_filter = self.get_zscore_Q(field_name, z_threshold) | self.get_iqr_Q(field_name, iqr_multiplier)
			return self.filter(combined_filter)

		raise ValueError("Invalid method specified. Use 'z_score', 'iqr', or None.")

	def get_zscore_Q(self, field_name: str, z_threshold: float = 2) -> Q:
		z_scores = self.z_score(field_name)
		z_score_anomalies = [i for i, z in enumerate(z_scores) if abs(z) > z_threshold]
		z_score_ids = [self.values_list('id', flat=True)[i] for i in z_score_anomalies]
		z_score_filter = Q(id__in=z_score_ids)
		return z_score_filter

	def get_iqr_Q(self, field_name: str, iqr_multiplier: float = 1.5) -> Q:
		iqr_outliers = self.iqr_outliers(field_name, multiplier=iqr_multiplier)
		return Q(id__in=iqr_outliers.values_list('id', flat=True))

	def filter_anomalies(self, method: Union[str, None] = None, z_threshold: float = 2, iqr_multiplier: float = 1.5) -> Self:
		"""
		Detect anomalies in all fields.

		Anomalies are identified using the z-score and interquartile range (IQR) methods.

		Args:
			method (str): The method to use for detecting anomalies. Can be 'z_score', 'iqr' or None (default)
			z_threshold (float): The threshold to use for the z-score method
			iqr_multiplier (float): The multiplier to use for the IQR method

		Returns:
			QuerySet: The anomalies

		Example:
			>>> Case.objects.detect_anomalies()
			<QuerySet [<Case: Case object (1)>, <Case: Case object (2)>]>

		"""
		# Get all fields that are numeric
		numeric_fields = [field.name for field in self.model._meta.get_fields() if self.field_is_numeric(field)]

		# Construct a filter for each field, so that we return all anomalies (using OR) rather than just entries that are anomalous in all fields (using AND)
		filters = []
		for _i, field in enumerate(numeric_fields):
			filter_q = Q(**{f"{field}__in": self.filter_anomalies_in(field, method, z_threshold, iqr_multiplier).values_list(field, flat=True)})
			filters.append(filter_q)

		# Filter the queryset using the OR of all the filters
		return self.filter(reduce(operator.or_, filters))
