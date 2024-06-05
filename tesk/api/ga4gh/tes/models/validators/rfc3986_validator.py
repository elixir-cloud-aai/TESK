"""RFC3986 URL validator."""

import re

from .base.base_validator import BaseValidator


class RFC3986Validator(BaseValidator):
	"""RFC3986Validator URL validator.

	Validate a URL based on RFC 3986 standard.

	Attributes:
			field (str): The URL string to be validated.
			model (BaseModel): The Pydantic model whose field is being validated.
	"""

	@property
	def error_message(self) -> str:
		"""Return the error message."""
		return 'Invalid URL format, only RFC 3986 standard allowed.'

	def validation_logic(self) -> bool:
		"""Validate a URL based on RFC 3986 standard."""
		url_regex = re.compile(
			r'^(?:http|ftp)s?://'  # http:// or https://
			r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain part 1
			r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain part 2
			r'localhost|'  # localhost...
			r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
			r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
			r'(?::\d+)?'  # optional port
			r'(?:/?|[/?]\S+)$',
			re.IGNORECASE,
		)

		return bool(re.match(url_regex, self._field))
