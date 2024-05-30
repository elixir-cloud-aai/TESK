"""API server entry point."""

import logging
import os
from pathlib import Path

from connexion import FlaskApp
from foca import Foca

logger = logging.getLogger(__name__)


def init_app() -> FlaskApp:
	"""Initialize and return the FOCA app.

	This function initializes the FOCA app by loading the configuration
	from the environment variable `TESK_FOCA_CONFIG_PATH` if set, or from
	the default path if not. It raises a `FileNotFoundError` if the
	configuration file is not found.

	Returns:
			FlaskApp: A Connexion application instance.

	Raises:
			FileNotFoundError: If the configuration file is not found.
	"""
	# Determine the configuration path
	config_path_env = os.getenv('TESK_FOCA_CONFIG_PATH')
	if config_path_env:
		config_path = Path(config_path_env).resolve()
	else:
		config_path = (
			Path(__file__).parents[1] / 'deployment' / 'config.yaml'
		).resolve()

	# Check if the configuration file exists
	if not config_path.exists():
		raise FileNotFoundError(f'Config file not found at: {config_path}')

	foca = Foca(
		config_file=config_path,
	)
	return foca.create_app()


def main() -> None:
	"""Run FOCA application."""
	app = init_app()
	app.run(port=app.port)


if __name__ == '__main__':
	main()
