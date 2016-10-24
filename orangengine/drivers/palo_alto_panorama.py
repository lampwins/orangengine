
from orangengine.drivers.base import BaseDriver

from pandevice import base
from pandevice import panorama
from pandevice import policies
from pandevice import objects


class PaloAltoPanoramaDriver(BaseDriver):

    def __init__(self):
        BaseDriver.__init__(self)
        self.get_device()

    def get_device(self):
        pass

