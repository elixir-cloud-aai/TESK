"""Base validator class, all custom validators must implement it."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import ValidationError

T = TypeVar('T')
logger = logging.getLogger(__name__)


class BaseValidator(ABC, Generic[T]):
	"""Base custom validator class.

	Base validator class for fields in Pydantic models,
	if the field is empty, ie None, then it is returned as is without any validation.
	otherwise the validation logic is applied to the field.
	"""

	@property
	@abstractmethod
	def error_message(self) -> str:
		"""Returns the error message.

		Returns:
			str: The error message to be used when validation fails.
		"""
		pass

	@abstractmethod
	def validation_logic(self, value: T) -> bool:
		"""Validation logic for the field.

		Args:
			value: The value of the field being validated.

		Returns:
			bool: True if the validation is successful, False otherwise.
		"""
		pass

	def _raise_error(self, cls: Any, value: T) -> None:
		"""Raise a validation error.

		Args:
			cls: The class being validated.
			value: The value of the field being validated.

		Raises:
			ValidationError: Raised when the validation fails.
		"""
		logger.error(f'Validation failed for {value} in {cls.__name__}.')
		raise ValidationError(
			self.error_message,
			model=cls,
		)

	def validate(self, cls: Any, value: T) -> T:
		"""Validate the value.

		If the value is None, that is the fields is optional
		in the model, then it is returned as is without any validation.

		Args:
			cls: The class being validated.
			value: The value of the field being validated.

		Returns:
			value: The validated value (if valid).

		Raises:
			ValidationError: If the value is not valid.
		"""
		if not value:
			return value
		elif not self.validation_logic(value):
			self._raise_error(cls, value)
		return value
