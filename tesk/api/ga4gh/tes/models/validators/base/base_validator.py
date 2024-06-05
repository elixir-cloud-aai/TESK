"""Base validator class, all custom validator must implement it."""

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, final

from pydantic import BaseModel, ValidationError

T = TypeVar('T')
logger = logging.getLogger(__name__)


class BaseValidator(ABC, Generic[T]):
	"""Base custom validator class."""

	def __init__(self, field: T, model: BaseModel) -> None:
		"""Initialize the validator.

		Args:
			field (T): The field to be validated.
			model (BaseModel): The pydantic model whose field is being validated.
		"""
		self._field = field
		self._model = model

	@property
	@abstractmethod
	def error_message(self) -> str:
		"""Returns the error message.

		Returns:
			str: The error message to be used when validation fails.
		"""
		pass

	@abstractmethod
	def validation_logic(self) -> bool:
		"""Validation logic for the field.

		Returns:
			True if the validation is successful, False otherwise.
		"""
		pass

	@final
	def _raise_error(self):
		"""Raise a validation error.

		Raises:
			ValidationError: Raised when the validation fails.
		"""
		logger.error(f"""
			Validation failed for {self._field} in {self._model.__name__}.
		""")
		raise ValidationError(
			self.error_message,
			model=self._model,
			fields={self._field},
		)

	@final
	def validate(self) -> T:
		"""Validate the value.

		Returns:
			The validated value (if valid).

		Raises:
			ValueError: If the value is not valid.
		"""
		if not self.validation_logic():
			self._raise_error()

		return self._field
