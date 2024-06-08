"""Base class for the APP used in initialization of API."""

import logging
import os
from pathlib import Path
from typing import Optional, final

from foca import Foca
from foca.config.config_parser import ConfigParser

logger = logging.getLogger(__name__)


class TeskApp(Foca):
	"""TESK API class extending the Foca framework."""

	def __init__(
		self,
		config_file: Optional[Path] = None,
		custom_config_model: Optional[Path] = None,
	) -> None:
		"""Initialize the TeskApp class.

		Args:
			config_file (Optional[Path]): Path to the configuration file.
				Defaults to None.
			custom_config_model (Optional[Path]): Path to the custom
				configuration model file. Defaults to None.
		"""
		if not config_file:
			self._load_config_file()
		else:
			self.config_file = config_file
		if not custom_config_model:
			self.custom_config_model = self._load_custom_config_model()
		else:
			self.custom_config_model = custom_config_model
		self.conf = ConfigParser(
			config_file=self.config_file,
			custom_config_model=self.custom_config_model,
			format_logs=True,
		).config
		self._app = self.create_app()

	@final
	def run(self) -> None:
		"""Run the application."""
		_environment = self.conf.server.environment or 'production'
		logger.info(f'Running application in {_environment} environment...')
		_debug = self.conf.server.debug or False
		self._app.run(
			host=self.conf.server.host, port=self.conf.server.port, debug=_debug
		)

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

	@final
	def _load_custom_config_model(self) -> None:
		"""Load the custom configuration model path from environment variable or None.

		Raises:
			FileNotFoundError: If the custom configuration model is specified and found.
		"""
		logger.info('Loading custom configuration model path...')
		if custom_config_model_env := os.getenv('TESK_FOCA_CUSTOM_CONFIG_MODEL'):
			self.custom_config_model = Path(custom_config_model_env).resolve()
		else:
			self.custom_config_model = None

		if self.custom_config_model and not self.custom_config_model.exists():
			raise FileNotFoundError(
				f'Custom configuration model not found at: {self.custom_config_model}',
			)
