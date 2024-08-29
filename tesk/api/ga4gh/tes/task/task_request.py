"""Base class for tesk request."""

import json
import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel

from tesk.api.kubernetes.client_wrapper import KubernetesClientWrapper
from tesk.api.kubernetes.constants import Constants
from tesk.api.kubernetes.convert.converter import TesKubernetesConverter

logger = logging.getLogger(__name__)


class TesTaskRequest(ABC):
    """Base class for tesk request ecapsulating common methods and members."""

    def __init__(self):
        """Initialise base class for tesk request."""
        self.kubernetes_client_wrapper = KubernetesClientWrapper()
        self.tes_kubernetes_converter = TesKubernetesConverter()
        self.constants = Constants()

    @abstractmethod
    def handle_request(self) -> BaseModel:
        """Business logic for the request."""
        pass

    def response(self) -> dict:
        """Get response for the request."""
        response: BaseModel = self.handle_request()
        try:
            return json.load(json.dumps(response))
        except (TypeError, ValueError) as e:
            logger.info(e)
            return response.dict()
