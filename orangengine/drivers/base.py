
import abc

from netmiko import ConnectHandler
from multi_key_dict import multi_key_dict
from collections import defaultdict


# our device type is different from netmiko's so we must map it here
NETMIKO_DRIVER_MAPPINGS = {
    'juniper_srx': 'juniper',
    'palo_alto_panorama': 'paloalto_panos',
}


class BaseDriver(object):

    def __init__(self, *args, **kwargs):

        # open netmiko connection
        kwargs['device_type'] = NETMIKO_DRIVER_MAPPINGS[kwargs['device_type']]
        self.device_conn = ConnectHandler(**kwargs)

        # share some output between methods
        self.config_output = dict()

        # address
        self.address_name_lookup = dict()
        self.address_value_lookup = defaultdict(list)
        self.address_group_name_lookup = dict()
        self.address_group_value_lookup = defaultdict(list)

        # service
        self.service_name_lookup = dict()
        self.service_value_lookup = defaultdict(list)
        self.service_group_name_lookup = dict()
        self.service_group_value_lookup = defaultdict(list)

        self.get_addresses()
        self.get_address_groups()
        self.get_services()
        self.get_service_groups()

    def _address_lookup_by_name(self, name):
        return self.address_name_lookup[name]

    def _address_set_lookup_by_name(self, name):
        return self.address_group_name_lookup[name]

    def _service_lookup_by_name(self, name):
        return self.service_name_lookup[name]

    def _service_group_lookup_by_name(self, name):
        return self.service_group_name_lookup[name]

    @abc.abstractmethod
    def get_addresses(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_address_groups(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_services(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_service_groups(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_polices(self):
        raise NotImplementedError()
