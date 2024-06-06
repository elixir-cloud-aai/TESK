"""Base class for the TES API service info endpoint."""

import os
from abc import abstractmethod
from hashlib import sha256
from threading import Thread
from time import sleep
from typing import Optional, final

from yaml import safe_load

from tesk.api.ga4gh.tes.base.base_tesk_request import BaseTeskRequest
from tesk.api.ga4gh.tes.models.tes_service_info import TesServiceInfo


class BaseServiceInfoRequest(BaseTeskRequest):
	"""Base class for the TES API service info endpoint.

	Abstraction class to hide away reload and parsing of service info from
	the config file.

	Attributes:
		_prev_service_info_hash (str): Hash of the service info configuration taken
		at init or after a set interval.
		_service_info (TesServiceInfo): Service info Pydantic model.
		_tesk_service_info_reload_interval (float): Interval to reload the service info.
	"""

	def __init__(self) -> None:
		"""Initializes the BaseServiceInfoRequest class."""
		super().__init__()
		self._prev_service_info_hash = self._hash_service_info_config()
		self._tesk_service_info_reload_interval = os.getenv(
			'TESK_SERVICE_INFO_RELOAD_INTERVAL',
			float(60 * 60),
		)
		self._service_info = self._get_service_info()
		thread = Thread(target=self._reload_service_info)
		thread.start()

	@abstractmethod
	def _get_default_service_info(self) -> TesServiceInfo:
		"""Loads the default service info."""
		pass

	@final
	def _reload_service_info(self) -> None:
		"""Reloads the service info."""
		while True:
			if self._service_info_in_config_changed():
				self._get_service_info()
			sleep(float(self._tesk_service_info_reload_interval))

	@final
	def _get_service_info(self) -> TesServiceInfo:
		"""Get and set the service info.

		Returns:
			TesServiceInfo: Pydantic model representing service info.
		"""
		if _service_info := self._get_service_info_present_in_config():
			self._service_info = _service_info
		else:
			self._service_info = self._get_default_service_info()
		return self._service_info

	@final
	def _service_info_present_in_config(self) -> bool:
		"""Checks if service info is present in the config file.

		Returns:
			bool: True if service info is present in the config file,
				False otherwise.
		"""
		with open(self._tesk_foca_config_path) as config_file:
			_config = safe_load(config_file)
			return 'serviceInfo' in _config

	@final
	def _service_info_in_config_changed(self) -> bool:
		"""Checks if service info changed in the config file and updates the hash.

		Returns:
			bool: True if the service info in the config file has changed,
				False otherwise.
		"""
		_new_hash = self._hash_service_info_config()
		if _new_hash == self._prev_service_info_hash:
			return False
		self._prev_service_info_hash = _new_hash
		return True

	@final
	def _get_service_info_present_in_config(self) -> Optional[TesServiceInfo]:
		"""Get service info if present in the config file.

		Returns:
			TesServiceInfo: Pydantic model representing service info from config file
											if present, None otherwise.

		Raises:
			NotFound: If service info is not present in the config file.
		"""
		if not self._service_info_present_in_config():
			return None
		with open(self._tesk_foca_config_path) as config_file:
			_config = safe_load(config_file)
			_tes_service_info = _config['serviceInfo']
			return TesServiceInfo(**_tes_service_info)

	@final
	def _hash_service_info_config(self) -> str:
		"""Hashes the service info configuration.

		Returns:
			str: Hash of the service info configuration.
		"""
		if not self._service_info_present_in_config():
			return ''
		_service_info = self._get_service_info_present_in_config()
		assert _service_info is not None
		_config_to_hash = _service_info.json().encode('utf-8')
		return sha256(_config_to_hash).hexdigest()
