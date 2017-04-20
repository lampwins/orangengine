# -*- coding: utf-8 -*-
import abc

from collections import defaultdict

from orangengine.errors import ShadowedPolicyError
from orangengine.errors import DuplicatePolicyError
from orangengine.models.base import CandidatePolicy, BasePolicy
from orangengine.utils import is_ipv4, missing_cidr
from orangengine.models.base import EffectivePolicy

from netaddr import IPNetwork


# our device type is different from netmiko's so we must map it here
NETMIKO_DRIVER_MAPPINGS = {
    'juniper_srx': 'juniper',
    'palo_alto_panorama': 'paloalto_panos',
}


class BaseDriver(object):

    PolicyClass = BasePolicy

    ALLOWED_POLICY_KEYS = (
        'source_zones',
        'destination_zones',
        'source_addresses',
        'destination_addresses',
        'services',
        'action',
        'logging',
    )

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
            self.open_connection(self._username, self._password, self._host, **self._additional_params)

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
        self._parse_applications()
        self._parse_application_groups()
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
    @abc.abstractmethod
    def tag_delta(expression, tag_list):
        raise NotImplementedError()

    def _policy_key_check(self, keys):
        if not all(k in self.ALLOWED_POLICY_KEYS for k in keys):
            raise ValueError('Invalid key in match criteria.')

    @staticmethod
    def _sanitize_match_criteria(match_criteria):
        """this TEMPORARY method cleans the match criteria"""
        services = []
        for service in match_criteria.get('services', []):
            if service == 'any':
                services.append(service)
            else:
                services.append(tuple([str(x) for x in service]))
        if services:
            match_criteria['services'] = services

        if match_criteria.get('action'):
            match_criteria['action'] = match_criteria['action'].lower()

        return match_criteria

    def policy_match(self, match_criteria, match_containing_networks=True, exact=False, policies=None):
        """
        match policy tuples exactly by match criteria (also a tuple) and return those policies
        """
        if not policies:
            policies = self.policies

        self._policy_key_check(match_criteria.keys())
        match_criteria = self._sanitize_match_criteria(match_criteria)

        # silently append /32 to any ipv4 address that is missing cidr
        if 'source_addresses' in match_criteria:
            match_criteria['source_addresses'] = [missing_cidr(a) for a in match_criteria['source_addresses']]

        if 'destination_addresses' in match_criteria:
            match_criteria['destination_addresses'] = [missing_cidr(a) for a in match_criteria['destination_addresses']]

        matches = [p for p in policies if p.match(match_criteria, exact=exact,
                                                  match_containing_networks=match_containing_networks)]

        return matches

    def candidate_policy_match(self, match_criteria, policies=None):
        """
        determine the best policy to append an element from the match criteria to
        return those policies that match and the unique "target" element, or None if no match is found
        """
        if not policies:
            policies = self.policies

        self._policy_key_check(match_criteria.keys())

        # shadow policy check (shadow implicitly includes duplicates)
        shadow_policies = list(self.policy_match(match_criteria, policies=policies))
        if len(shadow_policies) != 0:
            # this is a shadowed policy
            raise ShadowedPolicyError(message="Candidate is shadowed by {0}".format(shadow_policies[0].name))

        # now we find all candidate policies
        candidate_match = tuple([(p, p.candidate_match(match_criteria, match_containing_networks=True, exact=True))
                                for p in policies])
        # filter out tuples that are false (not a candidate match)
        candidate_tuples = list(filter((lambda x: x[1]), candidate_match))

        if candidate_tuples:
            target_element_key = candidate_tuples[0][1]
        else:
            target_element_key = None

        if len(candidate_tuples) == 0 and all(target_element_key == ct[1] for ct in candidate_tuples):
            # no valid matches or more than one target element identified (meaning this will have to be a new policy)
            return CandidatePolicy(policy_criteria=match_criteria, method=CandidatePolicy.Method.NEW_POLICY)
        else:

            matches = [ct[0] for ct in candidate_tuples]

            return CandidatePolicy(policy_criteria={target_element_key: match_criteria[target_element_key]},
                                   matched_policies=matches,
                                   method=CandidatePolicy.Method.APPEND)

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
    def open_connection(self, username, password, host, **additional_params):
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
    def _parse_applications(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_application_groups(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def apply_candidate_policy(self, candidate_policy, commit=False):
        raise NotImplementedError()

    @abc.abstractmethod
    def apply_policy(self, policy, commit=False):
        raise NotImplementedError()
