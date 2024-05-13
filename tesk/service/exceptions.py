class ServiceStatusCodes:
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
		return getattr(cls, status_name.upper(), None)


class UnknownProtocol(Exception):
	pass


class FileProtocolDisabled(Exception):
	pass


class InvalidHostPath(Exception):
	pass
