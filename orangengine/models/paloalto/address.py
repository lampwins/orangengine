# -*- coding: utf-8 -*-
from orangengine.models.base import BaseAddress
from orangengine.utils import bidict

from pandevice import objects


class PaloAltoAddress(BaseAddress):
    """Palo Alto Address

    Inherits from BaseAddress and provides access to the underlying pandevice object.
    Also provides and mapper for the type field.
    """

    TypeMap = bidict({
        BaseAddress.AddressTypes.IPv4: 'ip-netmask',
        BaseAddress.AddressTypes.RANGE: 'ip-range',
        BaseAddress.AddressTypes.DNS: 'fqdn',
        BaseAddress.AddressTypes.ANY: 'any'
    })

    def __init__(self, pandevice_object):

        self.pandevice_object = pandevice_object

        super(PaloAltoAddress, self).__init__(name=pandevice_object.name, value=pandevice_object.value,
                                              a_type=PaloAltoAddress.TypeMap[pandevice_object.type])

    @classmethod
    def from_criteria(cls, criteria):
        """Create an instance from the provided criteria
        """

        pandevice_object = objects.AddressObject()
        pandevice_object.name = criteria['name']
        pandevice_object.value = criteria['value']
        pandevice_object.type = criteria['type']

        return cls(pandevice_object)
