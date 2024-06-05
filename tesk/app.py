"""API server entry point."""

import logging
import os

from tesk.tesk_app import TeskApp

logger = logging.getLogger(__name__)


def main() -> None:
	"""Run FOCA application."""
	if os.getenv('CODE_ENVIRONMENT') != 'dev':
		os.environ['CODE_ENVIRONMENT'] = 'prod'

	tesk_app = TeskApp()
	tesk_app.run()


if __name__ == '__main__':
	os.environ['CODE_ENVIRONMENT'] = 'dev'
	main()
