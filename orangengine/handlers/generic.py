
import abc


class GenericHandler:

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_device(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_recommendation(self):
        raise NotImplementedError()
