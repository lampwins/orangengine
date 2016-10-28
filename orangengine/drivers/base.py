
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

        # address lookup dictionaries
        self.address_name_lookup = dict()
        self.address_value_lookup = defaultdict(list)
        self.address_group_name_lookup = dict()
        self.address_group_value_lookup = defaultdict(list)

        # service lookup dictionaries
        self.service_name_lookup = dict()
        self.service_value_lookup = defaultdict(list)
        self.service_group_name_lookup = dict()
        self.service_group_value_lookup = defaultdict(list)

        # policies
        self.policies = list()
        self.policy_tuple_lookup = list()

        # retrieve, parse, and store objects
        # order matters here as objects have to already
        # exist in the lookup dictionaries
        self.get_addresses()
        self.get_address_groups()
        self.get_services()
        self.get_service_groups()
        self.get_polices()

    def _address_lookup_by_name(self, name):
        return self.address_name_lookup[name]

    def _address_group_lookup_by_name(self, name):
        return self.address_group_name_lookup[name]

    def _service_lookup_by_name(self, name):
        return self.service_name_lookup[name]

    def _service_group_lookup_by_name(self, name):
        return self.service_group_name_lookup[name]

    def get_address_object_by_name(self, name):
        """
        public function to get address object by name
        either single object or group
        """
        if name in self.address_name_lookup.keys():
            return self._address_lookup_by_name(name)
        elif name in self.address_group_name_lookup.keys():
            return self._address_group_lookup_by_name(name)
        else:
            return None

    def get_service_object_by_name(self, name):
        """
        public function to get address object by name
        either single object or group
        """
        if name in self.service_name_lookup.keys():
            return self._service_lookup_by_name(name)
        elif name in self.service_group_name_lookup.keys():
            return self._service_group_lookup_by_name(name)
        else:
            return None

    def _add_policy(self, policy):
        self.policies.append(policy)
        self.policy_tuple_lookup.append((policy.value, policy))

    def policy_match(self, match_tuple):
        """
        match policy tuples by match criteria (also a tuple) and return those policies
        """
        def matcher(pattern):
            def f(data):
                return all(p is None or r == p for r, p in zip(data, pattern))
            return f

        tuples = filter(matcher(match_tuple), self.policy_tuple_lookup)
        for t in tuples:
            yield t[1]

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
