from abc import ABC, abstractmethod


class AbstractMode(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_min(self):
        pass

    @abstractmethod
    def get_max(self):
        pass

    @abstractmethod
    def get_metric(self, app_task):
        pass