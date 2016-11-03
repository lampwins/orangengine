
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

    def policy_match(self, source_zones=None, destination_zones=None, source_addresses=None,
                     destination_addresses=None, services=None, action=None):
        """
        match policy tuples exactly by match criteria (also a tuple) and return those policies
        """
        def matcher(pattern):
            def f(data):
                # the tuple we are concerned with is nested in data
                return all(p is None or r == p for r, p in zip(data[0], pattern))
            return f

        tuples = filter(matcher((source_zones, destination_zones, source_addresses,
                                 destination_addresses, services, action)), self.policy_tuple_lookup)

        for t in tuples:
            yield t[1]

    def policy_contains_match(self, source_zones=None, destination_zones=None, source_addresses=None,
                              destination_addresses=None, services=None, action=None):
        """
        match policy tuples that contain match criteria (also a tuple) and return those policies
        does not check ip network containment, only whether or not the elements are in the policy
        """

        def matcher(pattern):
            def f(data):
                # the tuple we are concerned with is nested in data
                return all(p is None or set(r).intersection(set(p)) == set(p) for r, p in zip(data[0], pattern))
            return f

        tuples = filter(matcher((source_zones, destination_zones, source_addresses,
                                 destination_addresses, services, action)), self.policy_tuple_lookup)

        for t in tuples:
            yield t[1]

    def policy_recommendation_match(self, source_zones=None, destination_zones=None, source_addresses=None,
                                    destination_addresses=None, services=None, action=None):
        """
        determine the best policy to append an element from the match criteria to
        """

        set_list = []
        target_elements = {}

        match_elements = locals()
        match_elements.pop('self')

        for key, value in match_elements:
            if value is not None and value:
                me_set = set(self.policy_match(key=value, action=action))

       # #if source_zones is not None and source_zones:
       #     p_set = set(self.policy_match(source_zones=source_zones, action=action))
       #     if len(p_set) > 0:
       #         set_list.append(p_set)
       #     else:
       #         target_elements['source_zones'] = source_zones
#
       # if destination_zones is not None and destination_zones:
       #     d_set = set(self.policy_match(destination_zones=destination_zones, action=action))
       #     if len(d_set) > 0:
       #         set_list.append(d_set)
       #     else:
       #         target_elements['destination_zones'] = destination_zones
#
       # if source_addresses is not None and source_addresses:
       #     set_list.append(set(self.policy_match(source_addresses=source_addresses, action=action)))
#
       # if destination_addresses is not None and destination_addresses:
       #     set_list.append(set(self.policy_match(destination_addresses=destination_addresses, action=action)))
#
       # if services is not None and services:
       #     set_list.append(set(self.policy_match(services=services, action=action)))

        matches = set.intersection(*set_list)

        return matches

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
