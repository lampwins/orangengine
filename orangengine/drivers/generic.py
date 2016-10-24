
import abc


class GenericDriver:

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_device(self):
        raise NotImplementedError()
