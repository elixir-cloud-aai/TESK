"""Custom configuration model for the FOCA app."""

from pydantic import BaseModel

from tesk.api.ga4gh.tes.models import Service


class CustomConfig(BaseModel):
    """Custom configuration model for the FOCA app."""

    # Define custom configuration fields here
    service_info: Service
