"""Service info for TES API.

This module provides the TesServiceInfo class, which is
the response to the service info request for the TES API.
"""

from tesk.api.ga4gh.tes.models.tes_service_info import TesServiceInfo
from tesk.api.ga4gh.tes.models.tes_service_info_organization import (
	TesServiceInfoOrganization,
)
from tesk.api.ga4gh.tes.models.tes_service_info_type import TesServiceInfoType
from tesk.api.ga4gh.tes.service_info.base.base_service_info_request import (
	BaseServiceInfoRequest,
)


class ServiceInfo(BaseServiceInfoRequest):
	"""Service info for TES API."""

	def _get_default_service_info(self) -> TesServiceInfo:
		_example_service_info_type = TesServiceInfoType(
			group='org.ga4gh',
			artifact='tes',
			version='1.1.0',
		)
		_example_service_info_organization = TesServiceInfoOrganization(
			name='my_organization',
			url='https://example.com',
		)
		return TesServiceInfo(
			id='org.ga4gh.tes',
			name='TES',
			type=_example_service_info_type,
			organization=_example_service_info_organization,
			version='1.1.0',
		)

	def api_response(self) -> TesServiceInfo:
		"""Executes the service info request."""
		return self._service_info
