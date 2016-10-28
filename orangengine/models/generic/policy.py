
from itertools import chain


class Policy(object):

    def __init__(self, name, action, description, logging):
        """init policy"""

        self.name = name
        self.src_zones = list()
        self.dst_zones = list()
        self.src_addresses = list()
        self.dst_addresses = list()
        self.services = list()
        self.action = action
        self.description = description
        self.logging = logging

    def add_src_zone(self, zone):
        self.src_zones.append(zone)

    def add_dst_zone(self, zone):
        self.dst_zones.append(zone)

    def add_src_address(self, address):
        self.src_addresses.append(address)

    def add_dst_address(self, address):
        self.dst_addresses.append(address)

    def add_service(self, service):
        self.services.append(service)

    def __getattr__(self, item):
        """
        return a tuple representation of the policy with normalized values
        """

        if item == 'value':

            if self.name == 'wug_mon_Jackson_jones':
                pass

            s_addrs = chain.from_iterable([a.value for a in self.src_addresses])
            d_addrs = [a.value for a in self.dst_addresses]
            services = [s.value for s in self.services]

            return self.src_zones, self.dst_zones, s_addrs, d_addrs, services, self.action

        else:
            raise AttributeError()
