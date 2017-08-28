# -*- coding: utf-8 -*-
from orangengine.models.base import BaseAddress
from orangengine.utils import create_element


class JuniperSRXAddress(BaseAddress):

    def __init__(self, name, value, a_type):

        super(JuniperSRXAddress, self).__init__(name, value, a_type)

    def to_xml(self):
        """Map address objects to juniper SRX config tree elements
        """

        address_element = create_element('address')
        create_element('name', text=self.name, parent=address_element)
        if self.a_type == BaseAddress.AddressTypes.IPv4:
            # ipv4
            create_element('ip-prefix', text=self.value, parent=address_element)
        elif self.a_type == BaseAddress.AddressTypes.DNS:
            # dns
            dns_element = create_element('dns-name', parent=address_element)
            create_element('name', text=self.value, parent=dns_element)

        return address_element