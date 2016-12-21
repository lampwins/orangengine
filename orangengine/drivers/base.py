
import abc

from collections import defaultdict

from orangengine.errors import ShadowedPolicyError
from orangengine.errors import DuplicatePolicyError
from orangengine.models.generic import CandidatePolicy
from orangengine.utils import is_ipv4

from netaddr import IPNetwork


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

        # zones mappings
        self.zone_map = dict()

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

    def get_address_object_by_value(self, value):
        """
        return a single address object if there is a value stored in dict(address_value_lookup)
        """
        if value in self.address_value_lookup.keys():
            return self.address_value_lookup[value][0]
        else:
            return None

    def get_service_object_by_value(self, value):
        """
        return a single service object if there is a value stored in dict(service_value_lookup)
        """
        if value in self.service_value_lookup.keys():
            return self.service_value_lookup[value][0]
        else:
            return None

    def _add_policy(self, policy):
        self.policies.append(policy)
        # self.policy_tuple_lookup.append((policy.value, policy))

    def policy_match(self, match_criteria, match_containing_networks=True, exact=False, policy_list=None):
        """
        match policy tuples exactly by match criteria (also a tuple) and return those policies
        """
        policies = [p for p in self.policies if p.match(match_criteria, exact=exact,
                                                        match_containing_networks=match_containing_networks)]

        return policies

    def policy_candidate_match(self, match_criteria):
        """
        determine the best policy to append an element from the match criteria to
        return those policies that match and the unique "target" element, or None if no match is found
        """

        set_list = []
        target_element = {}

        # shadow policy check (shadow implicitly includes duplicates)
        shadow_policies = list(self.policy_match(match_criteria))
        if len(shadow_policies) != 0:
            # this is a shadowed policy
            raise ShadowedPolicyError

        # we now know there is something unique about this policy
        # for each of the named parameters, find policy matches for those parameters
        for key, value in match_criteria.iteritems():
            # ignore those parameters which were not passed in, i.e. defaulted to None
            if value is None:
                continue

            # if a match(s) is found, this element is unique
            me_set = set(self.policy_match({_key: match_criteria[_key] for _key in match_criteria.keys()
                                            if _key is not key}))
            if len(me_set) != 0:
                # this is a unique element, thus our target element to append to policy x
                target_element[key] = match_criteria[key]
                # add the match set to the match set list
                set_list.append(me_set)

        if len(set_list) == 0 or len(target_element) > 1:
            # no valid matches or more than one target element identified (meaning this will have to be a new policy)
            return CandidatePolicy(target_dict=match_criteria, new_policy=True)
        else:
            # found valid matches
            # the intersection of all match sets is the set of all policies that the target element can to appended to
            matches = set.intersection(*set_list)

            if len(matches) < 1:
                # there actually were no matches after the intersection (rare)
                # threat this as a new policy
                return CandidatePolicy(target_dict=match_criteria, new_policy=True)

            # now lets pair down to just the unique elements in question
            reduced_target_elements = {}
            for key, value in target_element.iteritems():
                p_element = getattr(list(matches)[0], key, [])
                reduced_target_elements[key] = list(set(value) - set(p_element))

            return CandidatePolicy(target_dict=reduced_target_elements, matched_policies=list(matches))

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
