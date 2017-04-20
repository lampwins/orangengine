# -*- coding: utf-8 -*-
from orangengine.models.base import BaseService

from pandevice import objects


class PaloAltoService(BaseService):
    """Palo Alto Service

    Inherits from BaseService and provides access to the underlying pandevice object
    """

    def __init__(self, pandevice_object):

        self.pandevice_object = pandevice_object

        super(PaloAltoService, self).__init__(name=pandevice_object.name, protocol=pandevice_object.protocol,
                                              port=pandevice_object.destination_port)

    @classmethod
    def from_criteria(cls, criteria):
        """Create an instance from the provided criteria
        """

        pandevice_object = objects.ServiceObject()
        pandevice_object.name = criteria['name']
        pandevice_object.protocol = criteria['protocol']
        pandevice_object.destination_port = criteria['port']

        return cls(pandevice_object)
