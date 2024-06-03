"""Organization providing the service."""

from pydantic import BaseModel, Field, validator

from .validators.rfc3986_validator import RFC3986Validator


class TesServiceInfoOrganization(BaseModel):
	"""Organization providing the service."""

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

	@validator('name', 'url')
	def not_empty(cls, v):
		"""Validate that the value is not empty."""
		if not v:
			raise ValueError(f'{v} must not be empty.')
		return v

	@validator('url')
	def validate_url(cls, v):
		"""Validate the URL format based on RFC 3986 standard."""
		validator = RFC3986Validator()
		return validator.validate(v)
