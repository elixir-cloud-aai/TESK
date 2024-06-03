"""RFC2386 email validator."""

import re

from pydantic import BaseModel

from .base.validator import BaseValidator


class RFC2386Validator(BaseValidator):
	"""RFC2386 email validator.

	Validate an email based on RFC 2386 standard.

	Attributes:
		field (str): The email string to be validated.
		model (BaseModel): The Pydantic model whose field is being validated.
	"""

	def __init__(self, field: str, model: BaseModel) -> None:
		"""Initialize the RFC2386Validator.

		Args:
			field (str): The field to be validated.
			model (BaseModel): The Pydantic model whose field is being validated.
		"""
		super().__init__()
		self._field = field
		self._model = model

	@property
	def field(self) -> str:
		"""Return the field to be validated."""
		return self._field

	@property
	def model(self) -> BaseModel:
		"""Return the Pydantic model whose field is being validated."""
		return self._model

	@property
	def error_message(self) -> str:
		"""Return the error message."""
		return 'Invalid email format, only RFC 2386 standard allowed.'

	def validation_logic(self) -> bool:
		"""Validation logic for RFC 2386 standard."""
		email_regex = re.compile(
			r'^mailto:[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
		)
		return bool(re.match(email_regex, self.field))
