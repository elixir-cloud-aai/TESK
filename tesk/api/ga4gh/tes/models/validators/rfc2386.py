"""RFC2386 email validator."""

import re

from tesk.api.ga4gh.tes.models.validators.base.base_validator import BaseValidator


class RFC2386(BaseValidator[str]):
	"""RFC2386 email validator.

	Validate an email based on RFC 2386 standard.
	"""

	@property
	def error_message(self) -> str:
		"""Return the error message."""
		return 'Invalid email format, only RFC 2386 standard allowed.'

	def validation_logic(self, v: str) -> bool:
		"""Validation logic for RFC 2386 standard."""
		email_regex = re.compile(
			r'^mailto:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$',
		)
		return bool(re.match(email_regex, v))
