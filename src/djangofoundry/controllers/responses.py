"""

Metadata:

File: response.py
Project: Django Foundry
Created Date: 04 May 2023
Author: Jess Mann
Email: jess.a.mann@gmail.com

-----

Last Modified: Thu May 04 2023
Modified By: Jess Mann

-----

Copyright (c) 2023 Jess Mann
"""
from typing import Any, Optional

from rest_framework import response


#
# Generic Responses
#
class Response(response.Response):
	"""
	Represents a generic response. This is the base class for all responses.
	"""

class SuccessResponse(Response):
	"""
	Represents a successful response. This is the base class for all successful responses.
	"""

	def __init__(self, data=None, status=200, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'Success'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class ErrorResponse(Response):
	"""
	Represents an error response. This is the base class for all error responses.
	"""

	def __init__(self, data=None, status=500, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'An Error Occurred'}
		super().__init__(data, status, template_name, headers, exception, content_type)

#
# HTTP CODE 2xx
#
class OkResponse(SuccessResponse):
	"""
	Represents a successful HTTP Code 200 response. This is the base class for all successful responses.
	"""

	def __init__(self, data=None, status=200, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'OK'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class DataResponse(OkResponse):
	"""
	Represents a successful HTTP Code 200 response with data. This is the base class for all successful responses with data.
	"""

	def __init__(self, data=dict, status=200, template_name=None, headers=None, exception=False, content_type=None):
		super().__init__(data, status, template_name, headers, exception, content_type)

class PaginatedResponse(DataResponse):
	"""
	Represents a successful HTTP Code 200 response with paginated data. This is the base class for all successful responses with paginated data.
	"""

	class DataResponse(OkResponse):
		"""
		Represents a successful HTTP Code 200 response with data. This is the base class for all successful responses with data.
		"""

		def __init__(self, data: Optional[dict[str, Any]] = None, status=200, template_name=None, headers=None, exception=False, content_type=None):
			if not data:
				data = {}
			data = {
				'count': 0,
				'next': None,
				'previous': None,
				'results': [],
				**data,
			}
			super().__init__(data, status, template_name, headers, exception, content_type)

class DataModifiedResponse(OkResponse):
	"""
	Represents a successful HTTP Code 201 response that indicates data was modified in any way.
	"""

	def __init__(self, data=None, status=201, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'Data Modified'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class CreatedResponse(DataModifiedResponse):
	"""
	Represents a successful HTTP Code 201 response that indicates a resource was created.
	"""

	def __init__(self, data=None, status=201, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'Created'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class DeletedResponse(DataModifiedResponse):
	"""
	Represents a successful HTTP Code 204 response that indicates a resource was deleted.
	"""

	def __init__(self, data=None, status=204, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'Deleted'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class UpdatedResponse(DataModifiedResponse):
	"""
	Represents a successful HTTP Code 204 response that indicates a resource was updated.
	"""

	def __init__(self, data=None, status=204, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'Updated'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class AcceptedResponse(OkResponse):
	"""
	Represents a successful HTTP Code 202 response that indicates a request was accepted.
	"""

	def __init__(self, data=None, status=202, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'Accepted'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class NonAuthoritativeInformationResponse(OkResponse):
	"""
	Represents a successful HTTP Code 203 response that indicates "Non-Authoritative Information".
	"""

	def __init__(self, data=None, status=203, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'Non-Authoritative Information'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class NoContentResponse(OkResponse):
	"""
	Represents a successful HTTP Code 204 response that has no content attached.
	"""

	def __init__(self, data=None, status=204, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'No Content'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class ResetContentResponse(OkResponse):
	"""
	Represents a successful HTTP Code 205 response that indicates a content was reset.
	"""

	def __init__(self, data=None, status=205, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'Reset Content'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class PartialContentResponse(OkResponse):
	"""
	Represents a successful HTTP Code 206 response that indicates a partial content was returned.
	"""

	def __init__(self, data=None, status=206, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'message': 'Partial Content'}
		super().__init__(data, status, template_name, headers, exception, content_type)

#
# ERROR CODES 5xx
#
class InternalErrorResponse(ErrorResponse):
	"""
	Represents an HTTP Code 500 response that indicates an internal server error.
	"""

	def __init__(self, data=None, status=500, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Internal Server Error'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class NotImplementedResponse(InternalErrorResponse):
	"""
	Represents an HTTP Code 501 response that indicates a request was not implemented.
	"""

	def __init__(self, data=None, status=501, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Not Implemented'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class BadGatewayResponse(InternalErrorResponse):
	"""
	Represents an HTTP Code 502 response that indicates a bad gateway.
	"""

	def __init__(self, data=None, status=502, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Bad Gateway'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class ServiceUnavailableResponse(InternalErrorResponse):
	"""
	Represents an HTTP Code 503 response that indicates a service is unavailable.
	"""

	def __init__(self, data=None, status=503, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Service Unavailable'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class GatewayTimeoutResponse(InternalErrorResponse):
	"""
	Represents an HTTP Code 504 response that indicates a gateway timeout.
	"""

	def __init__(self, data=None, status=504, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Gateway Timeout'}
		super().__init__(data, status, template_name, headers, exception, content_type)

#
# ERROR CODES 4xx
#
class BadRequestResponse(ErrorResponse):
	"""
	Represents an HTTP Code 400 response that indicates a bad request.
	"""

	def __init__(self, data=None, status=400, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Bad Request'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class UnauthorizedResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 401 response that indicates an unauthorized request.
	"""

	def __init__(self, data=None, status=401, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Unauthorized'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class NotFoundResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 404 response that indicates a resource was not found.
	"""

	def __init__(self, data=None, status=404, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': '404: Not Found'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class ForbiddenResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 403 response that indicates a forbidden request.
	"""

	def __init__(self, data=None, status=403, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Forbidden'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class NotAllowedResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 405 response that indicates a method is not allowed.
	"""

	def __init__(self, data=None, status=405, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Method Not Allowed'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class ConflictResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 409 response that indicates a conflict.
	"""

	def __init__(self, data=None, status=409, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Conflict'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class GoneResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 410 response that indicates a resource is gone.
	"""

	def __init__(self, data=None, status=410, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Gone'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class LengthRequiredResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 411 response that indicates a length is required and not provided.
	"""

	def __init__(self, data=None, status=411, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Length Required'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class PreconditionFailedResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 412 response that indicates a precondition failed.
	"""

	def __init__(self, data=None, status=412, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Precondition Failed'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class RequestEntityTooLargeResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 413 response that indicates a request entity is too large.
	"""

	def __init__(self, data=None, status=413, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Request Entity Too Large'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class RequestURITooLongResponse(BadRequestResponse):
	"""
	Represents an HTTP Code 414 response that indicates a request URI is too long.
	"""

	def __init__(self, data=None, status=414, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Request URI Too Long'}
		super().__init__(data, status, template_name, headers, exception, content_type)

#
# ERROR CODES 3xx
#
class MultipleChoicesResponse(ErrorResponse):
	"""
	Represents an HTTP Code 300 response that indicates multiple choices.
	"""

	def __init__(self, data=None, status=300, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Multiple Choices'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class MovedPermanentlyResponse(MultipleChoicesResponse):
	"""
	Represents an HTTP Code 301 response that indicates a resource has moved permanently.
	"""

	def __init__(self, data=None, status=301, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Moved Permanently'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class FoundResponse(MultipleChoicesResponse):
	"""
	Represents an HTTP Code 302 response that indicates a resource has been found.
	"""

	def __init__(self, data=None, status=302, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Found'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class SeeOtherResponse(MultipleChoicesResponse):
	"""
	Represents an HTTP Code 303 response that indicates "See Other"
	"""

	def __init__(self, data=None, status=303, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'See Other'}
		super().__init__(data, status, template_name, headers, exception, content_type)

#
# ERROR CODES 1xx
#
class ContinueResponse(ErrorResponse):
	"""
	Represents an HTTP Code 100 response that indicates a continue.
	"""

	def __init__(self, data=None, status=100, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Continue'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class SwitchingProtocolsResponse(ContinueResponse):
	"""
	Represents an HTTP Code 101 response that indicates switching protocols.
	"""

	def __init__(self, data=None, status=101, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Switching Protocols'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class ProcessingResponse(ContinueResponse):
	"""
	Represents an HTTP Code 102 response that indicates processing.
	"""

	def __init__(self, data=None, status=102, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Processing'}
		super().__init__(data, status, template_name, headers, exception, content_type)

class EarlyHintsResponse(ContinueResponse):
	"""
	Represents an HTTP Code 103 response that indicates early hints.
	"""

	def __init__(self, data=None, status=103, template_name=None, headers=None, exception=False, content_type=None):
		if not data:
			data = {'error': 'Early Hints'}
		super().__init__(data, status, template_name, headers, exception, content_type)
