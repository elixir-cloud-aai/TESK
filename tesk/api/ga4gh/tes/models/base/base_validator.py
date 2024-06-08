"""Base validator class, all custom validator must implement it."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import ValidationError

T = TypeVar('T')
logger = logging.getLogger(__name__)


class BaseValidator(ABC, Generic[T]):
	"""Base custom validator class.

	Validators assume that the filed being validated is not optional as
	optional fields are handled by the Pydantic model itself and mypy type
	checking.
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
	def validation_logic(self, v: T) -> bool:
		"""Validation logic for the field.

		Args:
			v: The value being validated.

		Returns:
			bool: True if the validation is successful, False otherwise.
		"""
		pass

	def _raise_error(self, cls: Any, v: T) -> None:
		"""Raise a validation error.

		Args:
			cls: The class being validated.
			v: The value being validated.

		Raises:
			ValidationError: Raised when the validation fails.
		"""
		logger.error(f'Validation failed for {v} in {cls.__name__}.')
		raise ValidationError(
			self.error_message,
			model=cls,
		)

	def validate(self, cls: Any, v: T) -> T:
		"""Validate the value.

		If the value is None, ie the fields is optional
		in the model, then it is returned as is without any validation.

		Args:
			cls: The class being validated.
			v: The value being validated.

		Returns:
			T: The validated value (if valid).

		Raises:
			ValidationError: If the value is not valid.
		"""
		if not v:
			return v
		elif not self.validation_logic(v):
			self._raise_error(cls, v)
		return v
