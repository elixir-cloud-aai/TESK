"""Base class for the TES API request."""

from abc import ABC, abstractmethod
from typing import Any, final

from pydantic import BaseModel

from tesk.tesk_app import TeskApp


class BaseTeskRequest(ABC, TeskApp):
	"""Base class for the TES API.

	This class is an abstract class that defines the common properties and
	methods needed by all of the TES API endpoint business logic.

	Notes: This initializes the parent class `TeskApp` and will give
		all the subclasses access to the configuration object `conf` and
		config path.
	"""

	def __init__(self) -> None:
		"""Initializes the BaseTeskRequest class."""
		super().__init__()

	@abstractmethod
	def api_response(self) -> BaseModel:
		"""Returns the response as Pydantic model.

		Should be implemented by the child class as final
		business logic for the specific endpoint.

		Returns:
			BaseModel: API response for the specific endpoint.

		Raises:
			Exception: If API response break due to something unhandled.
		"""
		return BaseModel()

	@final
	def response(self) -> dict[str, Any]:
		"""Returns serialized response.

		Should be invoked by controller.

		Returns:
			dict: Serialized response for the specific endpoint.
		"""
		_response = self.api_response()
		if not isinstance(_response, BaseModel):
			raise TypeError('API response must be a Pydantic model.')
		return _response.dict()
