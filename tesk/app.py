"""App entry point."""

import logging

from tesk.tesk_app import TeskApp

logger = logging.getLogger(__name__)


def main() -> None:
	"""Run FOCA application."""
	try:
		TeskApp().run()
	except Exception:
		logger.exception('An error occurred while running the application.')
		raise


if __name__ == '__main__':
	main()
