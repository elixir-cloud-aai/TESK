"""TesServiceInfo model, used to represent the service information."""

import logging
from contextlib import suppress
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError, validator

from .service_info_organization import TesServiceInfoOrganization
from .service_info_type import TesServiceInfoType
from .validators.rfc2386_validator import RFC2386Validator
from .validators.rfc3339_validator import RFC3339Validator
from .validators.rfc3986_validator import RFC3986Validator

logger = logging.getLogger(__name__)

class TesServiceInfo(BaseModel):
	"""TesServiceInfo model, used to represent the service information."""

	id: str = Field(
		...,
		example='org.ga4gh.myservice',
		description=(
			'Unique ID of this service. Reverse domain name notation is recommended, '
			'though not required. The identifier should attempt to be globally unique '
			'so it can be used in downstream aggregator services e.g. Service Registry.'
		),
	)
	name: str = Field(
		...,
		example='My project',
		description='Name of this service. Should be human readable.',
	)
	type: TesServiceInfoType = Field(
		...,
		description='Type of a GA4GH service',
	)
	description: Optional[str] = Field(
		default=None,
		example='This service provides...',
		description=(
			'Description of the service. Should be human readable and '
			'provide information about the service.'
		),
	)
	organization: TesServiceInfoOrganization = Field(
		...,
		example='My organization',
	)
	contactUrl: Optional[str] = Field(
		default=None,
		example='mailto:support@example.com',
		description=(
			'URL of the contact for the provider of this service, '
			'e.g. a link to a contact form (RFC 3986 format), '
			'or an email (RFC 2368 format).'
		),
	)
	documentationUrl: Optional[str] = Field(
		default=None,
		example='https://docs.myservice.example.com',
		description='URL of the documentation for this service.',
	)
	created_at: Optional[str] = Field(
		default=None,
		example='2019-06-04T12:58:19Z',
		description=(
			'Timestamp describing when the service was first deployed '
			'and available (RFC 3339 format)'
		),
	)
	updatedAt: Optional[str] = Field(
		default=None,
		example='2019-06-04T12:58:19Z',
		description=(
			'Timestamp describing when the service was last updated (RFC 3339 format)'
		),
	)
	environment: Optional[str] = Field(
		default=None,
		example='test',
		description=(
			'Environment the service is running in. Use this to distinguish '
			'between production, development and testing/staging deployments. '
			'Suggested values are prod, test, dev, staging. However this is '
			'advised and not enforced.'
		),
	)
	version: str = Field(
		...,
		example='1.0.0',
		description=(
			'Version of the service being described. Semantic versioning is '
			'recommended, but other identifiers, such as dates or commit hashes, '
			'are also allowed. The version should be changed whenever the service '
			'is updated.'
		),
	)
	storage: List[str] = (
		Field(
			default_factory=list,
			example=[
				'file:///path/to/local/funnel-storage',
				's3://ohsu-compbio-funnel/storage',
			],
			description=(
				'Lists some, but not necessarily all, storage locations supported '
				'by the service.'
			),
		),
	)
	tesResources_backend_parameters: List[str] = Field(
		default_factory=list,
		example=['VmSize'],
		description=(
			'Lists all tesResources.backend_parameters keys ' 'supported by the service'
		),
	)

	@validator('id', 'name', 'type', 'organization', 'version')
	def not_empty(cls, v):
		"""Validate that the value is not empty."""
		if not v:
			raise ValueError('must not be empty')
		return v

	@validator('contactUrl')
	def validate_contact(cls, v):
		"""Validate the contactURL format based on RFC 3986 or 2368 standard."""
		if v:
			url_validator = RFC3986Validator(field=v, model=cls)
			email_validator = RFC2386Validator(field=v, model=cls)

			with suppress(ValidationError):
				return email_validator.validate()

			with suppress(ValidationError):
				return url_validator.validate()

			logger.error('contactUrl must be based on RFC 3986 or 2368 standard.')
			raise ValidationError(
				'contactUrl must be based on RFC 3986 or 2368 standard.'
			)
		return v

	@validator('createdAt', 'updatedAt')
	def validate_timestamp(cls, v):
		"""Validate the timestamp format based on RFC 3339 standard."""
		if v:
			date_validator = RFC3339Validator(field=v, model=cls)
			date_validator.validate()
		return v
