"""Custom configuration model for TESk API Consumed by FOCA."""

from pydantic import BaseModel, Field

from tesk.api.ga4gh.tes.models.tes_service_info import TesServiceInfo


class TeskCustomConfig(BaseModel):
	"""Custom configuration model for TES API."""

	service_info: TesServiceInfo = Field(
		...,
		title='Service Information',
		description='Service information for the TES API.',
	)
