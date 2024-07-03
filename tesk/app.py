"""App entry point."""

import logging

from tesk.tesk_app import TeskApp

logger = logging.getLogger(__name__)


def main() -> None:
    """Run FOCA application."""
    TeskApp().run()


if __name__ == "__main__":
    main()
