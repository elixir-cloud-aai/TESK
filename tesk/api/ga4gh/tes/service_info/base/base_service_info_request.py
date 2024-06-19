"""Base class for the TES API service info endpoint."""

from abc import abstractmethod
from typing import Optional

from tesk.api.ga4gh.tes.base.base_tesk_request import BaseTeskRequest
from tesk.api.ga4gh.tes.models.tes_service_info import TesServiceInfo
from tesk.exceptions import ConfigNotFoundError
from tesk.tesk_app import TeskApp


class BaseServiceInfoRequest(BaseTeskRequest):
	"""Base class for the TES API service info endpoint."""

	def __init__(self) -> None:
		"""Initializes the BaseServiceInfoRequest class."""
		self.service_info: Optional[TesServiceInfo] = None
		self.config = TeskApp().conf

	@abstractmethod
	def _get_default_service_info(self) -> TesServiceInfo:
		"""Loads the default service info."""
		pass

	def api_response(self) -> TesServiceInfo:
		"""Returns service info either from config or default."""
		# If service info is cached, return it.
		if self.service_info:
			return self.service_info

		if not self.config.custom:
			raise ConfigNotFoundError('Custom configuration not found.')

		self.service_info = (
			self.config.custom.service_info or self._get_default_service_info()
		)
		return self.service_info
