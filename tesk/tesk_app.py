"""Base class for the APP used in initialization of API."""

import logging
import os
from pathlib import Path
from typing import final

from foca import Foca
from foca.config.config_parser import ConfigParser

logger = logging.getLogger(__name__)


class TeskApp(Foca):
	"""TESK API class extending the Foca framework."""

	def __init__(self) -> None:
		"""Initialize the TeskApp class."""
		self._load_config_file()
		self.custom_config_model = 'tesk.custom_config.TeskCustomConfig'
		self.conf = ConfigParser(
			config_file=self.config_file,
			custom_config_model=self.custom_config_model,
			format_logs=True,
		).config

	@final
	def run(self) -> None:
		"""Run the application."""
		_environment = self.conf.server.environment or 'production'
		logger.info(f'Running application in {_environment} environment...')
		_debug = self.conf.server.debug or False
		_app = self.create_app()
		_app.run(host=self.conf.server.host, port=self.conf.server.port, debug=_debug)

	@final
	def _load_config_file(self) -> None:
		"""Load the configuration file path from env variable or default location.

		Raises:
			FileNotFoundError: If the configuration file is not found.
		"""
		logger.info('Loading configuration path...')
		if config_path_env := os.getenv('TESK_FOCA_CONFIG_FILE'):
			self.config_file = Path(config_path_env).resolve()
		else:
			self.config_file = (
				Path(__file__).parents[1] / 'deployment' / 'config.yaml'
			).resolve()

		if not self.config_file.exists():
			raise FileNotFoundError(
				f'Config file not found at: {self.config_file}',
			)
