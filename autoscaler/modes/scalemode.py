from abc import ABC, abstractmethod
import logging


class AbstractMode(ABC):

    def __init__(self, api_client=None, app=None):

        super().__init__()
        self.api_client = api_client
        self.app = app
        self.log = logging.getLogger("autoscaler")

    @abstractmethod
    def scale_direction(self):
        pass
