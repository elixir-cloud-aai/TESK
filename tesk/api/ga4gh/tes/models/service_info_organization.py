"""Organization providing the service."""

from pydantic import BaseModel, Field, validator

from tesk.api.ga4gh.tes.models.validators.rfc3986_validator import RFC3986Validator


class TesServiceInfoOrganization(BaseModel):
	"""Organization providing the service.

	Attributes:
		name (str): Name of the organization providing the service.
		url (str): URL of the website of the organization (RFC 3986 format).

	Example:
		{
			"name": "My organization",
			"url": "https://example.com"
		}
	"""

	name: str = Field(
		...,
		example='My organization',
		description='Name of the organization providing the service.',
	)
	url: str = Field(
		...,
		example='https://example.com',
		description='URL of the website of the organization (RFC 3986 format).',
	)

	# validators
	_ = validator('url')(RFC3986Validator().validate)
