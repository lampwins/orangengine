
class Policy(object):

    def __init__(self, name, src_zones, dst_zones, src_addresses, dst_addresses, services, action):
        """init policy"""

        self.name = name
        self.src_zones = src_zones
        self.dst_zones = dst_zones
        self.src_addresses = src_addresses
        self.dst_addresses = dst_addresses
        self.services = services
        self.action = action

