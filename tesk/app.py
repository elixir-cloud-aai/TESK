"""API server entry point."""

import logging
from pathlib import Path

from connexion import FlaskApp
from foca import Foca

logger = logging.getLogger(__name__)


def init_app() -> FlaskApp:
	"""Initialize the Foca app."""
	config_path = Path(__file__).parent / 'config.yaml'
	foca = Foca(
		config_file=config_path,
	)

	return foca.create_app()


def main(app) -> None:
	"""Run FOCA application."""
	app.run(port=app.port)


if __name__ == '__main__':
	"""This is executed when run from the command line.

    Install `TESK` and run the console script `api`.
    """
	my_app = init_app()
	my_app.run()
