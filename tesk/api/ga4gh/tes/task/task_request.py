import logging
from abc import ABC, abstractmethod
import json
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class TesTaskRequest(ABC):
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
