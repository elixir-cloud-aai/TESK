
"""TesServiceInfo model, used to represent the service information."""

import logging
from contextlib import suppress
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError, validator

from tesk.api.ga4gh.tes.models.tes_service_info_organization import (
	TesServiceInfoOrganization,
)
from tesk.api.ga4gh.tes.models.tes_service_info_type import TesServiceInfoType
from tesk.api.ga4gh.tes.models.validators.rfc2386_validator import RFC2386Validator
from tesk.api.ga4gh.tes.models.validators.rfc3339_validator import RFC3339Validator
from tesk.api.ga4gh.tes.models.validators.rfc3986_validator import RFC3986Validator

logger = logging.getLogger(__name__)


class TesServiceInfo(BaseModel):
	"""TesServiceInfo model, used to represent the service information.

	Attributes:
		id (str): Unique ID of this service.
		name (str): Name of this service.
		type (TesServiceInfoType): Type of a GA4GH service.
		description (str): Description of the service.
		organization (TesServiceInfoOrganization): Organization providing the service.
		contactUrl (str): URL of the contact for the provider of this service.
		documentationUrl (str): URL of the documentation for this service.
		created_at (str): Timestamp describing when the service was first deployed
											and available.
		updatedAt (str): Timestamp describing when the service was last updated.
		environment (str): Environment the service is running in.
		version (str): Version of the service being described.
		storage (List[str]): Lists some, but not necessarily all, storage locations
												supported by the service.
		tesResources_backend_parameters (List[str]): Lists of supported
																								tesResources.backend_parameters
																								keys.

	Example:
		{
			"id": "org.ga4gh.myservice",
			"name": "My project",
			"type": {
				"group": "org.ga4gh",
				"artifact": "tes",
				"version": "1.0.0"
			},
			"description": "This service provides...",
			"organization": {
				"name": "My organization",
				"url": "https://example.com"
			},
			"contactUrl": "mailto:support@example.com",
			"documentationUrl": "https://docs.myservice.example.com",
			"createdAt": "2019-06-04T12:58:19Z",
			"updatedAt": "2019-06-04T12:58:19Z",
			"environment": "test",
			"version": "1.0.0",
			"storage": [
				"file:///path/to/local/funnel-storage",
				"s3://ohsu-compbio-funnel/storage"
			]
		}
	"""

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
	type: TesServiceInfoType
	description: Optional[str] = Field(
		default=None,
		example='This service provides...',
		description=(
			'Description of the service. Should be human readable and '
			'provide information about the service.'
		),
	)
	organization: TesServiceInfoOrganization
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
	storage: List[str] = Field(
		default_factory=list,
		example=[
			'file:///path/to/local/funnel-storage',
			's3://ohsu-compbio-funnel/storage',
		],
		description=(
			'Lists some, but not necessarily all, storage locations supported '
			'by the service.'
		),
	)
	tesResources_backend_parameters: List[str] = Field(
		default_factory=list,
		example=['VmSize'],
		description=(
			'Lists all tesResources.backend_parameters keys supported by the service'
		),
	)

	# Remarks:
	# @uniqueg: There is a better way to do this, create a ValidateClass, which
	# has all the validators and date sanitizers, create a
	# BaseTeskModel(BaseModel, ValidateClass), this class will then be implemented
	# by all the models, and the validators will be reused.
	# The issue with this approach is that we don't have consistent field names and I
	# feel they might be subject to change in future or among different models.
	# This is why I have not implemented this approach.
	#
	# Another cool approach would be to create a decorator, I tried that but given
	# FOCA uses pydantic v1.*, and if FOCA is to be upgraded to v2.*, the decorator
	# validate would be removed and the code would break.

	# validators
	_ = validator('documentationUrl', allow_reuse=True)(RFC3986Validator().validate)
	_ = validator('created_at', 'updatedAt', allow_reuse=True)(
		RFC3339Validator().validate
	)

	@validator('contactUrl')
	def validate_url_and_email(cls, v: str) -> str:
		"""Validate the contactURL format based on RFC 3986 or 2368 standard."""
		url_validator = RFC3986Validator()
		email_validator = RFC2386Validator()

		with suppress(ValidationError):
			return email_validator.validate(cls, v)

		with suppress(ValidationError):
			return url_validator.validate(cls, v)

		logger.error('contactUrl must be based on RFC 3986 or 2368 standard.')
		raise ValidationError(
			'contactUrl must be based on RFC 3986 or 2368 standard.', model=cls
		)
