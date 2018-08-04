from abc import ABC, abstractmethod


class AbstractMode(ABC):

    def __init__(self, marathon_client, app_name):
        super().__init__()
        self.marathon_client = marathon_client
        self.app_name = app_name

    @abstractmethod
    def get_min(self):
        pass

    @abstractmethod
    def get_max(self):
        pass

    @abstractmethod
    def get_value(self):
        pass
