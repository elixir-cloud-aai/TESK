"""Base class for TES API pydantic models."""

import logging
from contextlib import suppress

from pydantic import BaseModel, ValidationError, validator

from tesk.api.ga4gh.tes.models.validators.rfc2386 import RFC2386
from tesk.api.ga4gh.tes.models.validators.rfc3339 import RFC3339
from tesk.api.ga4gh.tes.models.validators.rfc3986 import RFC3986

logger = logging.getLogger(__name__)


class BaseTesModel(BaseModel):
	"""Base class for TES API pydantic models."""

	_rfc2386 = RFC2386()
	_rfc3339 = RFC3339()
	_rfc3986 = RFC3986()

	_ = validator('documentationUrl', allow_reuse=True, check_fields=False)(_rfc3986.validate)
	_ = validator('created_at', 'updatedAt', allow_reuse=True, check_fields=False)(_rfc3339.validate)

	@validator('contactUrl', allow_reuse=True, check_fields=False)
	def validate_url_and_email(cls, v: str) -> str:
		"""Validate the contactURL format based on RFC 3986 or 2368 standard."""
		url_validator = RFC3986()
		email_validator = RFC2386()

		with suppress(ValidationError):
			return email_validator.validate(cls, v)

		logger.warning('contactUrl is not an email address. Validating as URL.')
		return url_validator.validate(cls, v)
