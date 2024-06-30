"""App entry point."""

import logging

from werkzeug.exceptions import InternalServerError

from tesk.tesk_app import TeskApp

logger = logging.getLogger(__name__)


def main() -> None:
  """Run FOCA application."""
  try:
    TeskApp().run()
  except Exception as error:
    logger.exception("An error occurred while running the application.")
    raise InternalServerError(
      "An error occurred while running the application."
    ) from error


if __name__ == "__main__":
  main()
