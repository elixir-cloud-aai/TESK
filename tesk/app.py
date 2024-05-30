"""API server entry point."""

import logging
import os
from pathlib import Path

from connexion import FlaskApp
from foca import Foca

logger = logging.getLogger(__name__)


def init_app() -> FlaskApp:
	"""Initialize the FOCA app."""

	# Use environment variables, this will be useful for docker
	config_path_env = os.getenv('TESK_FOCA_CONFIG_PATH')
	config_filename_env = os.getenv('TESK_FOCA_CONFIG_FILENAME', 'config.yaml')

	if config_path_env:
		config_path = Path(config_path_env).resolve() / config_filename_env
	else:
		base_path = Path(__file__).parents[1]
		config_path = (base_path / 'deployment' / config_filename_env).resolve()

	if not config_path.exists():
		raise FileNotFoundError(f'Config file not found: {config_path}')

	foca = Foca(
		config_file=config_path,
	)
	return foca.create_app()


if __name__ == '__main__':
	app = init_app()
	app.run()


def main() -> None:
	"""Run FOCA application."""
	app = init_app()
	app.run(port=app.port)


if __name__ == '__main__':
	"""This is executed when run from the command line.

	Install `TESK` and run the console script `api`.
	"""
	my_app = init_app()
	my_app.run()
