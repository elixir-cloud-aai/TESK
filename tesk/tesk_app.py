"""Base class for the APP used in initialization of API."""

import logging
import os
from pathlib import Path
from typing import final

from foca import Foca
from foca.config.config_parser import ConfigParser  # type: ignore

from tesk.exceptions import ConfigNotFoundError

logger = logging.getLogger(__name__)


class TeskApp(Foca):
  """TESK API class extending the Foca framework.

  This class is used to initialize the TESK API application, contains
  business logic for parsing configuration files and starting the
  application server.

  Attributes:
    config_file (Path): Path to the configuration file.
    conf (Any): Configuration object.

  Args:
    config_file (Optional[Path]): Path to the configuration file.
      Defaults to None.

  Notes: TeskApp class uses environment variables to load the configuration
    file and custom configuration model file with `TESK_FOCA_CONFIG_FILE`
    and `TESK_FOCA_CUSTOM_CONFIG_MODEL` respectively.

  Raises:
    ConfigNotFoundError: If the configuration file is not found.

  Method:
    run: Run the application.

  Example:
  >>> from tesk.tesk_app import TeskApp
  >>> app = TeskApp()
  >>> app.run()
  """

  def __init__(self) -> None:
    """Initialize the TeskApp class."""
    self._load_config_file()
    self.conf = ConfigParser(
      config_file=self.config_file,
      format_logs=True,
    ).config

  @final
  def run(self) -> None:
    """Run the application."""
    _environment = self.conf.server.environment or "production"
    logger.info(f"Running application in {_environment} environment...")
    _debug = self.conf.server.debug or False
    _app = self.create_app()
    _app.run(host=self.conf.server.host, port=self.conf.server.port, debug=_debug)

  @final
  def _load_config_file(self) -> None:
    """Load the configuration file path from env variable or default location.

    Raises:
            ConfigNotFoundError: If the configuration file is not found.
    """
    logger.info("Loading configuration path...")
    if config_path_env := os.getenv("TESK_FOCA_CONFIG_FILE"):
      self.config_file = Path(config_path_env).resolve()
    else:
      self.config_file = (
        Path(__file__).parents[1] / "deployment" / "config.yaml"
      ).resolve()

    if not self.config_file.exists():
      raise ConfigNotFoundError(
        f"Config file not found at: {self.config_file}",
      )
