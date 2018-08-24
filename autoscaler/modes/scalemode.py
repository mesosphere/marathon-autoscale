from abc import ABC, abstractmethod
import logging


class AbstractMode(ABC):

    def __init__(self, api_client=None, app=None, dimension=None):

        super().__init__()

        self.api_client = api_client
        self.app = app
        self.min_range = 0
        self.max_range = 1

        if dimension is not None:
            if isinstance(dimension["min"], list):
                self.min_range = dimension["min"][0]
            else:
                self.min_range = dimension["min"]

            if isinstance(dimension["max"], list):
                self.max_range = dimension["max"][0]
            else:
                self.max_range = dimension["max"]

        self.log = logging.getLogger("autoscaler")

    @abstractmethod
    def scale_direction(self):
        pass

    def get_min(self):
        return self.min_range

    def get_max(self):
        return self.max_range

