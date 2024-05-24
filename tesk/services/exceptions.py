"""Exceptions used in the services module."""


class ServiceStatusCodes:
	"""A class to represent the HTTP status codes.

	Attributes:
		OK (int): HTTP status code for OK.
		REDIRECT (int): HTTP status code for Redirect.
		CREATED (int): HTTP status code for Created.
		CONFLICT (int): HTTP status code for Conflict.
		NOT_FOUND (int): HTTP status code for Not Found.
		BAD_REQUEST (int): HTTP status code for Bad Request.
		UNAUTHORIZED (int): HTTP status code for Unauthorized.
		FORBIDDEN (int): HTTP status code for Forbidden.
		INTERNAL_SERVER_ERROR (int): HTTP status code for Internal Server Error.
		NOT_IMPLEMENTED (int): HTTP status code for Not Implemented.
		SERVICE_UNAVAILABLE (int): HTTP status code for Service Unavailable.
		GATEWAY_TIMEOUT (int): HTTP status code for Gateway Timeout.

	"""

	OK = 200
	REDIRECT = 300
	CREATED = 201
	CONFLICT = 409
	NOT_FOUND = 404
	BAD_REQUEST = 400
	UNAUTHORIZED = 401
	FORBIDDEN = 403
	INTERNAL_SERVER_ERROR = 500
	NOT_IMPLEMENTED = 501
	SERVICE_UNAVAILABLE = 503
	GATEWAY_TIMEOUT = 504

	@classmethod
	def get(cls, status_name):
		"""Retrieve the corresponding HTTP status code for a given status name.

		Args:
			status_name (str): The name of the HTTP status code to retrieve.

		Returns:
			int or None: Corresponding HTTP status code if found, otherwise None.

		"""
		return getattr(cls, status_name.upper(), None)


class UnknownProtocol(Exception):
	"""Exception raised for using an unknown protocol."""

	pass


class FileProtocolDisabled(Exception):
	"""Exception raised when the file protocol is disabled."""

	pass


class InvalidHostPath(Exception):
	"""Exception raised for an invalid host path."""

	pass
