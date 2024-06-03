"""Base validator class, all cutom validator must implement it."""

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, final

from pydantic import BaseModel, ValidationError

T = TypeVar('T')
logger = logging.getLogger(__name__)


class BaseValidator(ABC, Generic[T]):
	"""Base custom validator class."""

	@property
	@abstractmethod
	def field(self) -> T:
		"""Returns the field to be validated."""
		pass

	@property
	@abstractmethod
	def model(self) -> BaseModel:
		"""Returns the pydantic model whose field is being validated."""
		pass

	@property
	@abstractmethod
	def error_message(self) -> str:
		"""Returns the error message."""
		pass

	@abstractmethod
	def validation_logic(self) -> bool:
		"""Login validation.

		Returns:
			True if the validation is successful, False otherwise.
		"""
		pass

	@final
	def raiseError(self):
		"""Raise a validation error."""
		logger.error(f"""
			Validation failed for {self.field} in {self.model.__name__}.
		""")
		raise ValidationError(self.error_message, model=self.model, fields={self.field})

	@final
	def validate(self) -> T:
		"""Validate the value.

		Returns:
			The validated value (if valid).

		Raises:
			ValueError: If the value is not valid.
		"""
		if not self.validation_logic():
			self.raiseError()

		return self.field
