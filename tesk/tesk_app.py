"""Base class for the APP used in initialization of API."""

import logging
import os

# import signal
# import subprocess
# import sys
# import threading
# import time
# from hashlib import sha256
# from multiprocessing import Process, Queue
from pathlib import Path
from typing import final

from foca import Foca

logger = logging.getLogger(__name__)


class TeskApp:
	"""TESK API class."""

	def __init__(self):
		"""Initializes the TeskApp API.

		Attributes:
			foca (Foca): Foca instance.
			_tesk_foca_config_path (str): Path to the configuration file.
			_app (FlaskApp): Foca app instance.
		"""
		self._tesk_foca_config_path = ''
		self._foca = Foca()
		self._app = self._foca.create_app()
		self._load_config()

	@final
	def run(self) -> None:
		"""Run the application."""
		self._app.run(port=self._app.port)

	@final
	def _load_config_path(self) -> None:
		"""Loads the configuration path.

		Gets the configuration path from the environment variable
		(`TESK_FOCA_CONFIG_PATH`) or uses the default path.

		Raises:
			FileNotFoundError: If the configuration file is not found.
		"""
		logger.info('Loading configuration path...')
		if config_path_env := os.getenv('TESK_FOCA_CONFIG_PATH'):
			self._tesk_foca_config_path = Path(config_path_env).resolve()
		else:
			self._tesk_foca_config_path = (
				Path(__file__).parents[1] / 'deployment' / 'config.yaml'
			).resolve()

		if not self._tesk_foca_config_path.exists():
			raise FileNotFoundError(
				f'Config file not found at: {self._tesk_foca_config_path}',
			)

	@final
	def _load_config(self) -> None:
		"""Loads the configuration and create FOCA and app instance."""
		self._load_config_path()
		self._foca = Foca(
			config_file=self._tesk_foca_config_path,
		)
		self._app = self._foca.create_app()


# class TeskApp:
# 	"""Base class for the APP."""

# 	def __init__(self):
# 		"""Initializes the BaseApp class."""
# 		self._reload_interval = int(os.getenv('CONFIG_RELOAD_INTERVAL', int(60*60)))
# 		self._load_config()
# 		self._prev_config_hash = self._hash_config()
# 		self.restart_server = False

# 		if self._reload_interval > 0:
# 			logger.info(
# 				'The configuration reload interval is set to '
# 				f'{self._reload_interval} seconds.'
# 			)
# 			self._start_reload_thread()
# 		else:
# 			logger.info(
# 				'The configuration reload interval is set to 0. '
# 				'Configuration reload is disabled.'
# 			)

# 	def start_app(self):
# 		"""Starts the application."""
# 		self._app = self.foca.create_app()
# 		self._app.run(port=self._app.port)
# 		self.restart_server = False

# 	def run(self) -> None:
# 		"""Run the application."""
# 		q = Queue()
# 		p = Process(target=self.start_app(), args=(q,))
# 		p.start()
# 		while not self.restart_server:
# 			time.sleep(1)
# 		p.terminate()
# 		args = [sys.executable] + [sys.argv[0]]
# 		subprocess.call(args)

# 	# TODO: Implement the reload method, server still doesn't seem restart
# 	def reload(self) -> None:
# 		"""Reloads the configuration and if changes found restarts the server."""
# 		while True:
# 			time.sleep(self._reload_interval)
# 			# self.reload()
# 			_new_hash = self._hash_config()
# 			if self._prev_config_hash == _new_hash:
# 				logger.info('Configuration has not changed. Skipping reload.')
# 			else:
# 				# reset the hash
# 				self._prev_config_hash = _new_hash
# 				logger.info(f'Reloading configuration at {time.time()}')
# 				# reinitialize the configuration
# 				self._load_config()
# 				logger.info('Configuration reloaded, restarting the server.')
# 				# restart the server
# 				self.restart_server = True

# 	def restart_server(self) -> None:
# 		"""Restarts the server by shutting down and starting it again."""
# 		logger.info('Shutting down the server.')
# 		os.kill(os.getpid(), signal.SIGINT)
# 		self.run()

# 	def _hash_config(self) -> str:
# 		with open(self._tesk_foca_config_path) as file:
# 			data = file.read()
# 			return sha256(data.encode('utf-8')).hexdigest()

# 	def _load_config_path(self) -> None:
# 		"""Loads the configuration path."""
# 		logger.info('Loading configuration path...')
# 		if config_path_env := os.getenv('TESK_FOCA_CONFIG_PATH'):
# 			self._tesk_foca_config_path = Path(config_path_env).resolve()
# 		else:
# 			self._tesk_foca_config_path = (
# 				Path(__file__).parents[1] / 'deployment' / 'config.yaml'
# 			).resolve()

# 		if not self._tesk_foca_config_path.exists():
# 			raise FileNotFoundError(
# 				f'Config file not found at: {self._tesk_foca_config_path}'
# 			)

# 	def _load_config(self) -> None:
# 		"""Loads the configuration."""
# 		self._load_config_path()
# 		self.foca = Foca(
# 			config_file=self._tesk_foca_config_path,
# 		)

# 	def _start_reload_thread(self) -> None:
# 		"""Starts a background thread to reload configuration periodically."""
# 		thread = threading.Thread(target=self.reload, daemon=True)
# 		thread.start()
