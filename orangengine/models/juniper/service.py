# -*- coding: utf-8 -*-
from orangengine.models.base import BaseService, BasePortRange
from orangengine.utils import create_element


class JuniperSRXService(BaseService):

    def __init__(self, name, protocol=None, port=None):

        super(JuniperSRXService, self).__init__(name, protocol, port)

    def to_xml(self):
        """Map service objects to juniper SRX config tree elements
        """

        def map_destination_port(port):
            if isinstance(port, BasePortRange):
                port = port.value
            return create_element('destination-port', text=port)

        service_element = create_element('application')
        create_element('name', text=self.name, parent=service_element)
        if len(self.terms) > 0:
            # termed based service
            for term in self.terms:
                term_element = create_element('term', parent=service_element)
                term_element.append(map_destination_port(term.port))
                create_element('source-port', text='0-65535', parent=term_element)
                create_element('protocol', text=term.protocol, parent=term_element)
                create_element('name', text=term.name, parent=term_element)
        else:
            service_element.append(map_destination_port(self.port))
            create_element('source-port', text='0-65535', parent=service_element)
            create_element('protocol', text=self.protocol, parent=service_element)

        return service_element
