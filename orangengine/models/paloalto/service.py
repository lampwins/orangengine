
from orangengine.models.base import BaseService


class PaloAltoService(BaseService):
    """Palo Alto Service

    Inherits from BaseService and provides access to the underlying pandevice object
    """

    def __init__(self, pandevice_object):

        self.pandevice_object = pandevice_object

        super(PaloAltoService, self).__init__(name=pandevice_object.name, protocol=pandevice_object.protocol,
                                              port=pandevice_object.destination_port)
