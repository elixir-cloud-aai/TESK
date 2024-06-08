"""Type of a GA4GH service."""

from typing import Literal

from pydantic import BaseModel, Field


class TesServiceInfoType(BaseModel):
	"""Class represing the type of a `GA4GH` service.

	Attributes:
		group (str): Namespace in reverse domain name format.
		artifact (str): Name of the API or GA4GH specification implemented.
		version (str): Version of the API or specification.

	Example:
		{
			"group": "org.ga4gh",
			"artifact": "tes",
			"version": "1.1.0"
		}
	"""

	group: str = Field(
		default='org.ga4gh',
		example='org.ga4gh',
		description=(
			'Namespace in reverse domain name format. Use `org.ga4gh` for '
			'implementations compliant with official GA4GH specifications. '
			'For services with custom APIs not standardized by GA4GH, or '
			'implementations diverging from official GA4GH specifications, use '
			"a different namespace (e.g. your organization's reverse domain name)."
		),
	)
	artifact: Literal['tes'] = Field(
		default='tes',
		example='tes',
		description=(
			'Name of the API or GA4GH specification implemented. Official GA4GH types '
			'should be assigned as part of standards approval process. '
			'Custom artifacts are supported.'
		),
	)
	version: str = Field(
		default='1.1.0',
		example='1.0.0',
		description=(
			'Version of the API or specification. '
			'GA4GH specifications use semantic versioning.'
		),
	)