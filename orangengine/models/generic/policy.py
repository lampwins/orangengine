
from collections import Iterable


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

            if self.name == 'c2e-O365-access':
                pass

            s_addrs = set(Policy.__flatten([a.value for a in self.src_addresses]))
            d_addrs = set(Policy.__flatten([a.value for a in self.dst_addresses]))
            services = set(Policy.__flatten([s.value for s in self.services]))

            return self.src_zones, self.dst_zones, list(s_addrs), list(d_addrs), list(services), self.action

        else:
            raise AttributeError()

    @staticmethod
    def __flatten(l):
        for el in l:
            if isinstance(el, Iterable) and not isinstance(el, basestring) and not isinstance(el, tuple):
                for sub in Policy.__flatten(el):
                    yield sub
            else:
                yield el
