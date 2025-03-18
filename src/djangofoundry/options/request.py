from enum import Enum


class RequestType(Enum):
	"""
	Valid types of HTTP Requests
	"""

	GET = 'GET'
	POST = 'POST'
	SOAP = 'SOAP'
