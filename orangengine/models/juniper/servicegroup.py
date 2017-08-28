# -*- coding: utf-8 -*-
from orangengine.models.base import BaseServiceGroup
from orangengine.utils import create_element


class JuniperSRXServiceGroup(BaseServiceGroup):

    def __init__(self, name):

        super(JuniperSRXServiceGroup, self).__init__(name)

    def to_xml(self):
        """Map service group objects to juniper SRX config tree elements
        """

        servicegroup_element = create_element('application-set')
        create_element('name', text=self.name, parent=servicegroup_element)
        for service in self.elements:
            service_element = create_element('application', parent=servicegroup_element)
            create_element('name', text=service.name, parent=service_element)

        return servicegroup_element