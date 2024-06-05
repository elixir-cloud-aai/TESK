"""TesServiceInfo model, used to represent the service information."""

import logging
from typing import List, Optional

from pydantic import BaseModel, Field

from tesk.api.ga4gh.tes.models.service_info_organization import (
	TesServiceInfoOrganization,
)
from tesk.api.ga4gh.tes.models.service_info_type import TesServiceInfoType

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

	# @validator('id', 'name', 'type', 'organization', 'version')
	# def not_empty(cls, v):
	# 	"""Validate that the value is not empty."""
	# 	if not v:
	# 		logger.error(f'Field {v} must not be empty in model {cls.__name__}.')
	# 		raise ValueError(f'Field {v} must not be empty in model {cls.__name__}.')
	# 	return v

	# @validator('documentationUrl')
	# def validate_url(cls, v):
	# 	"""Validate the documentationURL format based on RFC 3986 standard."""
	# 	if v:
	# 		validator = RFC3986Validator(field=v, model=cls)
	# 		return validator.validate()
	# 	return v

	# @validator('contactUrl')
	# def validate_url_and_email(cls, v):
	# 	"""Validate the contactURL format based on RFC 3986 or 2368 standard."""
	# 	if v:
	# 		url_validator = RFC3986Validator(field=v, model=cls)
	# 		email_validator = RFC2386Validator(field=v, model=cls)

	# 		with suppress(ValidationError):
	# 			return email_validator.validate()

	# 		with suppress(ValidationError):
	# 			return url_validator.validate()

	# 		logger.error('contactUrl must be based on RFC 3986 or 2368 standard.')
	# 		raise ValidationError(
	# 			'contactUrl must be based on RFC 3986 or 2368 standard.'
	# 		)
	# 	return v

	# @validator('createdAt', 'updatedAt')
	# def validate_timestamp(cls, v):
	# 	"""Validate the timestamp format based on RFC 3339 standard."""
	# 	if v:
	# 		date_validator = RFC3339Validator(field=v, model=cls)
	# 		return date_validator.validate()
	# 	return v
