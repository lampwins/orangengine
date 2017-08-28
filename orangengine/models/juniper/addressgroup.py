# -*- coding: utf-8 -*-
from orangengine.models.base import BaseAddressGroup, BaseAddress
from orangengine.utils import create_element


class JuniperSRXAddressGroup(BaseAddressGroup):

    def __init__(self, name):

        super(JuniperSRXAddressGroup, self).__init__(name)

    def to_xml(self):
        """Map address group objects to juniper SRX config tree elements
        """

        addressgroup_element = create_element('address-set')
        create_element('name', text=self.name, parent=addressgroup_element)

        for a in self.elements:
            if isinstance(a, BaseAddress):
                address_element = create_element('address', parent=addressgroup_element)
            else:
                address_element = create_element('address-set', parent=addressgroup_element)
            create_element('name', text=a.name, parent=address_element)

        return addressgroup_element
