"""RFC2386 email validator."""

import re

from .base.base_validator import BaseValidator


class RFC2386Validator(BaseValidator):
	"""RFC2386 email validator.

	Validate an email based on RFC 2386 standard.

	Attributes:
		field (str): The email string to be validated.
		model (BaseModel): The Pydantic model whose field is being validated.
	"""

	@property
	def error_message(self) -> str:
		"""Return the error message."""
		return 'Invalid email format, only RFC 2386 standard allowed.'

	def validation_logic(self) -> bool:
		"""Validation logic for RFC 2386 standard."""
		email_regex = re.compile(
			r'^mailto:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$',
		)
		return bool(re.match(email_regex, self._field))
