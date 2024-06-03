"""RFC3339 date validator."""

from datetime import datetime

from pydantic import BaseModel

from .base.validator import BaseValidator


class RFC3339Validator(BaseValidator):
	"""RFC3339Validator date validator.

	Validate a date based on RFC 3339 standard.

	Attributes:
		field (str): The date string to be validated.
		_model (Base_model): The Pydantic _model whose field is being validated.
	"""

	def __init__(self, field: str, _model: BaseModel) -> None:
		"""Initialize the RFC3339Validator.

		Args:
			field (str): The date string to be validated.
			__model (Base_model): The Pydantic _model whose field is being validated.
		"""
		super().__init__()
		self._field = field
		self._model = _model

	@property
	def field(self) -> str:
		"""Return the field to be validated."""
		return self._field

	@property
	def model(self) -> BaseModel:
		"""Return the Pydantic _model whose field is being validated."""
		return self._model

	@property
	def error_message(self) -> str:
		"""Return the error message."""
		return 'Invalid date format, only RFC 3339 standard allowed.'

	def validation_logic(self) -> bool:
		"""Validation logic for RFC 3339 standard."""
		return bool(datetime.strptime(self.field, '%Y-%m-%dT%H:%M:%S%z').tzinfo)
