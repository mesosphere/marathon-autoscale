from abc import ABC, abstractmethod
import logging


class AbstractMode(ABC):

    def __init__(self, api_client, app_name):
        super().__init__()
        self.api_client = api_client
        self.app_name = app_name

        self.log = logging.getLogger("autoscaler")

    @abstractmethod
    def get_min(self):
        pass

    @abstractmethod
    def get_max(self):
        pass

    @abstractmethod
    def get_value(self):
        pass
