# -*- coding: utf-8 -*-
from orangengine.utils import enum, bidict
from orangengine.models.base import BaseService
from orangengine.models.base import BaseObject


class PaloAltoApplication(BaseObject):
    """Palo Alto Appliciation
    """

    IdentTypes = enum('PORT', 'PROTOCOL', 'ICMP', 'ICMP6')
    IdentTypeMap = bidict({
        IdentTypes.PORT: 'port',
        IdentTypes.PROTOCOL: 'ident-by-ip-protocol',
        IdentTypes.ICMP: 'ident-by-icmp-type',
        IdentTypes.ICMP6: 'ident-by-icmp6-type',
        None: None,
    })

    WellKnownServiceMap = bidict({
        ('tcp', 80): 'web-browsing',
        ('tcp', 443): 'ssl',
        ('tcp', 22): 'ssh',
        ('udp', 123): 'ntp',
        ('tcp', 21): 'ftp',
        ('tcp', 23): 'telnet',
        ('tcp', 25): 'smtp',
        ('tcp', 1521): 'oracle',
        ('tcp', 1433): 'mssql-db',
        ('tcp', 445): 'ms-ds-smb',
    })

    def __init__(self, pandevice_object):

        self.pandevice_object = pandevice_object

        self.name = self.pandevice_object.name
        self.default_type = PaloAltoApplication.IdentTypeMap[self.pandevice_object.default_type]
        self.services = []

        if self.default_type == PaloAltoApplication.IdentTypes.PORT:
            for p in self.pandevice_object.default_port:
                protocol = p.split('/')[0]
                port = p.split('/')[1]
                for port_element in port.split(','):
                    self.services.append(BaseService(name="{0}-{1}".format(self.name, port_element),
                                                     port=port_element, protocol=protocol))

    def match_service(self, service_tuple):
        """Return true if self contains the given service, else false
        """
        for service in self.services:
            if service.protocol == service_tuple[0] and service.port == service_tuple[1]:
                return True
        return False

    def __getattr__(self, item):

        if item == 'value':
            return self.name
        else:
            raise AttributeError

    def table_value(self):
        return self.name

    def serialize(self):
        """Searialize self to a json acceptable data structure
        """

        services = []
        for s in self.services:
            services.append(s.serialize())

        return {
            'name': self.name,
            'default_type': self.default_type,
            'services': services,
        }
