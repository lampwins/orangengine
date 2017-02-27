
import abc

from collections import defaultdict

from orangengine.errors import ShadowedPolicyError
from orangengine.errors import DuplicatePolicyError
from orangengine.models.generic import CandidatePolicy
from orangengine.utils import is_ipv4, missing_cidr
from orangengine.models.generic import EffectivePolicy

from netaddr import IPNetwork


# our device type is different from netmiko's so we must map it here
NETMIKO_DRIVER_MAPPINGS = {
    'juniper_srx': 'juniper',
    'palo_alto_panorama': 'paloalto_panos',
}

ALLOWED_POLICY_KEYS = (
    'source_zones',
    'destination_zones',
    'source_addresses',
    'destination_addresses',
    'services',
    'action',
    'logging',
)


class BaseDriver(object):

    def __init__(self, refresh=False, *args, **kwargs):

        self._connected = False
        self.device = None

        # connection params
        self._username = kwargs.pop('username')
        self._password = kwargs.pop('password')
        self._host = kwargs.pop('host')
        self._additional_params = kwargs

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
        self.policy_name_lookup = dict()

        # zones mappings
        self.zone_map = dict()

        # share some output between methods
        self.config_output = dict()

        # retrieve, parse, and store objects
        # order matters here as objects have to already
        # exist in the lookup dictionaries
        if refresh:
            self.refresh()

    def refresh(self):
        """Refresh the device

        This method will connect to the device and pull down the config and
        parse all of the objects into the models

        """

        if not self._connected:
            self.open_connection(self._username, self._password, self._host, self._additional_params)

        # first we need to clear all of the current objects

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
        self.policy_name_lookup = dict()

        # zones mappings
        self.zone_map = dict()

        # now we parse the new config

        self._get_config()

        self._parse_addresses()
        self._parse_address_groups()
        self._parse_services()
        self._parse_service_groups()
        self._parse_policies()

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
        self.policy_name_lookup[policy.name] = policy

    @staticmethod
    def _policy_key_check(keys):
        if not all(k in ALLOWED_POLICY_KEYS for k in keys):
            raise ValueError('Invalid key in match criteria.')

    def policy_match(self, match_criteria, match_containing_networks=True, exact=False):
        """
        match policy tuples exactly by match criteria (also a tuple) and return those policies
        """
        self._policy_key_check(match_criteria.keys())

        # silently append /32 to any ipv4 address that is missing cidr
        if 'source_addresses' in match_criteria:
            match_criteria['source_addresses'] = [missing_cidr(a) for a in match_criteria['source_addresses']]

        if 'destination_addresses' in match_criteria:
            match_criteria['destination_addresses'] = [missing_cidr(a) for a in match_criteria['destination_addresses']]

        policies = [p for p in self.policies if p.match(match_criteria, exact=exact,
                                                        match_containing_networks=match_containing_networks)]

        return policies

    def policy_candidate_match(self, match_criteria):
        """
        determine the best policy to append an element from the match criteria to
        return those policies that match and the unique "target" element, or None if no match is found
        """
        self._policy_key_check(match_criteria.keys())

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
            return CandidatePolicy(target_dict=match_criteria, method=CandidatePolicy.NEW_POLICY)
        else:
            # found valid matches
            # the intersection of all match sets is the set of all policies that the target element can to appended to
            matches = set.intersection(*set_list)

            if len(matches) < 1:
                # there actually were no matches after the intersection (rare)
                # threat this as a new policy
                return CandidatePolicy(target_dict=match_criteria, method=CandidatePolicy.NEW_POLICY)

            # now lets pair down to just the unique elements in question
            reduced_target_elements = {}
            for key, value in target_element.iteritems():
                p_element = getattr(list(matches)[0], key, [])
                reduced_target_elements[key] = list(set(value) - set(p_element))

            return CandidatePolicy(target_dict=reduced_target_elements, matched_policies=list(matches),
                                   method=CandidatePolicy.APPEND_POLICY)

    def effective_policy(self, address, match_containing_networks=True):
        """
        Match source and destination rules based on address and return an EffectivePolicy object
        :param match_containing_networks:
        :param address:
        :return: EffectivePolicy object
        """

        source_policies = self.policy_match({'source_addresses': [address]}, match_containing_networks)
        destination_policies = self.policy_match({'destination_addresses': [address]}, match_containing_networks)

        return EffectivePolicy(address=address, source_policies=source_policies,
                               destination_policies=destination_policies)

    @abc.abstractmethod
    def open_connection(self, username, password, host, additional_params):
        raise NotImplementedError()

    @abc.abstractmethod
    def _get_config(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_addresses(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_address_groups(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_services(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_service_groups(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_policies(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def apply_candidate_policy(self, candidate_policy):
        raise NotImplementedError()
