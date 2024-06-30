"""Service info for TES API."""

import json
from typing import Any, Optional

from pydantic import AnyUrl

from tesk.api.ga4gh.tes.models import (
  Artifact,
  Organization,
  TesServiceInfo,
  TesServiceType,
)
from tesk.exceptions import ConfigNotFoundError
from tesk.tesk_app import TeskApp


class ServiceInfo:
  """Service info for TES API."""

  def __init__(self) -> None:
    """Initializes the BaseServiceInfoRequest class."""
    self.service_info: Optional[TesServiceInfo] = None
    self.config = TeskApp().conf

  def get_default_service_info(self) -> TesServiceInfo:
    """Get the default service info.

    if service info is not provided in the config,
    this method will return the default service info.

    Returns:
        TesServiceInfo: Default service info.
    """
    return TesServiceInfo(
      id="org.ga4gh.tes",
      name="TES",
      type=TesServiceType(
        group="org.ga4gh",
        artifact=Artifact.tes,
        version="1.1.0",
      ),
      organization=Organization(
        name="my_organization",
        url=AnyUrl("https://example.com"),
      ),
      version="1.1.0",
    )

  def get_service_info_from_config(self) -> TesServiceInfo:
    """Returns service info from config.

    Returns:
      TesServiceInfo: Service info from config.

    Raises:
      ConfigNotFoundError: If custom config or part of it is not found
        in the config file.
    """
    if not self.config.custom:
      raise ConfigNotFoundError("Custom configuration not found.")

    service_info_data = self.config.custom.get("service_info")
    if not service_info_data:
      raise ConfigNotFoundError("Service info not found in custom configuration.")

    try:
      service_info = TesServiceInfo(**service_info_data)
    except TypeError as e:
      raise ConfigNotFoundError(f"Invalid service info format: {e}") from None

    return service_info

  def response(self) -> dict[str, Any]:
    """Returns serialized response for /service-info.

    Returns:
      dict: Serialized response.
    """
    if self.service_info is None:
      try:
        self.service_info = self.get_service_info_from_config()
      except ConfigNotFoundError:
        self.service_info = self.get_default_service_info()

    # return self.service_info.dict()
    return dict(json.loads(self.service_info.json()))
