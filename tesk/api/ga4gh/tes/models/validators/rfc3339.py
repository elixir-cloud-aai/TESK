"""RFC3339 date validator."""

import calendar
import re

from tesk.api.ga4gh.tes.models.validators.base.base_validator import BaseValidator


class RFC3339(BaseValidator[str]):
	"""RFC3339Validator date validator.

	Validate a date based on RFC 3339 standard.
	"""

	@property
	def error_message(self) -> str:
		"""Return the error message."""
		return 'Invalid date format, only RFC 3339 standard allowed.'

	def validation_logic(self, v: str) -> bool:
		"""Validation logic for RFC 3339 standard.

		Cf. https://github.com/naimetti/rfc3339-validator
		"""
		date_regex = re.compile(
			r"""
		^
		(\d{4})	# Year
		-
		(0[1-9]|1[0-2])	# Month
		-
		(\d{2})	 # Day
		T
		(?:[01]\d|2[0123])	# Hours
		:
		(?:[0-5]\d)	# Minutes
		:
		(?:[0-5]\d)	# Seconds
		(?:\.\d+)?	# Secfrac
		(?:  Z	# UTC
		| [+-](?:[01]\d|2[0123]):[0-5]\d	# Offset
		)
		$
		""",
			re.VERBOSE,
		)
		_match = date_regex.match(v)
		if _match is None:
			return False
		year, month, day = map(int, _match.groups())
		if not year:
			# Year 0 is not valid a valid date
			return False
		(_, max_day) = calendar.monthrange(year, month)
		return 1 <= day <= max_day
