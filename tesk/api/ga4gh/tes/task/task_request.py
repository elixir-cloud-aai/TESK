"""Base class for tesk request."""

import json
import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel

from tesk.k8s.constants import tesk_k8s_constants
from tesk.k8s.converter.converter import TesKubernetesConverter
from tesk.k8s.wrapper import KubernetesClientWrapper

logger = logging.getLogger(__name__)


class TesTaskRequest(ABC):
    """Base class for tesk request ecapsulating common methods and members."""

    def __init__(self):
        """Initialise base class for tesk request."""
        self.kubernetes_client_wrapper = KubernetesClientWrapper()
        self.tes_kubernetes_converter = TesKubernetesConverter()
        self.tesk_k8s_constants = tesk_k8s_constants

    @abstractmethod
    def handle_request(self) -> BaseModel:
        """Business logic for the request."""
        pass

    def response(self) -> dict:
        """Get response for the request."""
        response: BaseModel = self.handle_request()
        try:
            res: dict = json.loads(json.dumps(response))
            return res
        except (TypeError, ValueError) as e:
            logger.info(e)
            return response.dict()
