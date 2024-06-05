"""RFC3339 date validator."""

from datetime import datetime

from .base.base_validator import BaseValidator


class RFC3339Validator(BaseValidator):
	"""RFC3339Validator date validator.

	Validate a date based on RFC 3339 standard.

	Attributes:
		field (str): The date string to be validated.
		_model (Base_model): The Pydantic _model whose field is being validated.
	"""

	@property
	def error_message(self) -> str:
		"""Return the error message."""
		return 'Invalid date format, only RFC 3339 standard allowed.'

	def validation_logic(self) -> bool:
		"""Validation logic for RFC 3339 standard."""
		return bool(datetime.strptime(self._field, '%Y-%m-%dT%H:%M:%S%z').tzinfo)
