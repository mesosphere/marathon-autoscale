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
    def scale_direction(self, value):

        if value > self.max_range:
            self.log.debug("Scaling mode above max threshold of %s"
                           % self.max_range)
            return 1
        elif value < self.min_range:
            self.log.debug("Scaling mode below threshold of %s"
                           % self.min_range)
            return -1
        else:
            self.log.debug("Scaling mode within thresholds (min=%s, max=%s)"
                           % (self.min_range, self.max_range))
            return 0
