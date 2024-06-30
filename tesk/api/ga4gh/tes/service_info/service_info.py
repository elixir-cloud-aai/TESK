"""Service info for TES API."""

from tesk.api.ga4gh.tes.models import Organization, Service, ServiceType


class ServiceInfo:
  """Service info for TES API."""

  def __init__(self, config: Config = None):
    self.config = config
    self.service_info = None

  def _get_default_service_info(self) -> Service:
    return Service(
      id="org.ga4gh.tes",
      name="TES",
      type=ServiceType(
        group="org.ga4gh",
        artifact="tes",
        version="1.1.0",
      ),
      organization=Organization(
        name="my_organization",
        url="https://example.com",
      ),
      version="1.1.0",
    )

  def api_response(self) -> Service:
    """Returns service info either from config or default."""
		# If service info is cached, return it.
    if self.service_info:
      return self.service_info

    if not self.config.custom:
      raise ConfigNotFoundError('Custom configuration not found.')

    self.service_info = (
      self.config.custom.service_info or self._get_default_service_info()
    )
    return self.service_info
