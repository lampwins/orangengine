
class Policy(object):

    def __init__(self, name, action, description, logging, src_zones=list(),
                 dst_zones=list(), src_addresses=list(), dst_addresses=list(),
                 services=list(), ):
        """init policy"""

        self.name = name
        self.src_zones = src_zones
        self.dst_zones = dst_zones
        self.src_addresses = src_addresses
        self.dst_addresses = dst_addresses
        self.services = services
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
