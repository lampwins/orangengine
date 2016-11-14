
import abc

from netmiko import ConnectHandler
from multi_key_dict import multi_key_dict
from collections import defaultdict

from orangengine.errors import ShadowedPolicyError
from orangengine.errors import DuplicatePolicyError


# our device type is different from netmiko's so we must map it here
NETMIKO_DRIVER_MAPPINGS = {
    'juniper_srx': 'juniper',
    'palo_alto_panorama': 'paloalto_panos',
}


class BaseDriver(object):

    def __init__(self, *args, **kwargs):

        self._connected = False
        self.device = None

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
        self.open_connection(**kwargs)
        self.get_addresses()
        self.get_address_groups()
        self.get_services()
        self.get_service_groups()
        self.get_policies()

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
                return all(p is None or set(r) == set(p) for r, p in zip(data[0], pattern))
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
        return those policies that match and the unique "target" element, or None if no match is found
        """

        # must be first
        match_element_keys = locals()
        match_element_keys = set(match_element_keys) - {'self', 'match_element_keys'}
        _locals = locals()

        set_list = []
        target_element = {}

        param_dict = {_key: _locals[_key] for _key in match_element_keys}

        # duplicate policy check
        duplicate_policies = set(self.policy_match(**param_dict))
        if len(duplicate_policies) != 0:
            raise DuplicatePolicyError

        # shadow policy check
        shadow_policies = list(self.policy_contains_match(**param_dict))
        if len(shadow_policies) != 0:
            # this is a shadowed policy
            raise ShadowedPolicyError

        # we now know there is something unique about this policy
        # for each of the named parameters, find policy matches for those parameters
        for key in match_element_keys:
            # ignore those parameters which were not passed in, i.e. defaulted to None
            if _locals[key]:
                # if a match(s) is found, this element is unique
                me_set = set(self.policy_match(**{_key: _locals[_key] for _key in match_element_keys
                                                  if _key is not key}))
                if len(me_set) != 0:
                    # this is a unique element, thus our target element to append to policy x
                    target_element[key] = _locals[key]
                    # add the match set to the match set list
                    set_list.append(me_set)

        if len(set_list) == 0 or len(target_element) > 1:
            # no valid matches or more than one target element identified (meaning this will have to be a new policy)
            return None
        else:
            # found valid matches
            # the intersection of all match sets is the set of all policies that the target element can to appended to
            matches = set.intersection(*set_list)

            return matches, target_element

    @abc.abstractmethod
    def open_connection(self, *args, **kwargs):
        raise NotImplementedError()

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
    def get_policies(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def apply_candidate_policy(self, candidate_policy):
        raise NotImplementedError()
