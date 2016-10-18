
from handlers import generic

from pandevice import base
from pandevice import panorama
from pandevice import policies
from pandevice import objects


class PaloAltoPanorama(generic.GenericHandler):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.get_device()

    def get_device(self):
        pass

    def get_recommendation(self):
        pass
