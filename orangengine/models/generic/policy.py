
from orangengine.errors import BadCandidatePolicyError
from orangengine.utils import is_ipv4

from collections import Iterable
import re
from netaddr import IPRange, IPNetwork


class Policy(object):

    def __init__(self, name, action, description, logging):
        """init policy"""

        self.name = name
        self.src_zones = list()
        self.dst_zones = list()
        self.src_addresses = list()
        self.dst_addresses = list()
        self._services = list()
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
        self._services.append(service)

    def __getattr__(self, item):
        """
        return a tuple representation of the policy with normalized values
        """

        s_addrs = set(Policy.__flatten([a.value for a in self.src_addresses]))
        d_addrs = set(Policy.__flatten([a.value for a in self.dst_addresses]))
        services = set(Policy.__flatten([s.value for s in self._services]))

        if item == 'value':
            return self.src_zones, self.dst_zones, list(s_addrs), list(d_addrs), list(services), self.action

        # for use in policy match element reducing
        elif item == 'source_zones':
            return self.src_zones
        elif item == 'destination_zones':
            return self.dst_zones
        elif item == 'source_addresses':
            return s_addrs
        elif item == 'destination_addresses':
            return d_addrs
        elif item == 'services':
            return services

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

    @staticmethod
    def __in_network(value, p_value, exact_match=False):
        """

        """

        # 'any' address is an automatic match if we are exact
        if exact_match and 'any' in p_value:
            return True

        addresses = [IPRange(a.split('-')[0], a.split('-')[1]) if '-' in a else IPNetwork(a)
                     for a in value if is_ipv4(a)]
        fqdns = [a for a in value if not is_ipv4(a)]
        p_addresses = [IPRange(a.split('-')[0], a.split('-')[1]) if '-' in a else IPNetwork(a)
                       for a in p_value if is_ipv4(a)]
        p_fqdns = [a for a in p_value if not is_ipv4(a)]

        # network containment implies exact match... i think?
        addr_result = any(a == b or a in b for a in addresses for b in p_addresses)

        # now match the fqdns
        if exact_match:
            fqdn_result = set(fqdns) == set(p_fqdns)
        else:
            fqdn_result = set(p_fqdns).issubset(set(fqdns))

        return addr_result and fqdn_result

    def match(self, match_criteria, exact=False, match_containing_networks=True):
        """
        determine if self is a match for the given criteria
        """
        for key, value in match_criteria.iteritems():
            if value is None:
                # this key was included but the value is None, so skip it
                continue

            p_value = getattr(self, key, [])

            if match_containing_networks and key in ['source_addresses', 'destination_addresses']:
                if not self.__in_network(value, p_value, exact_match=True):
                    return False
            elif exact and not set(p_value) == set(value):
                return False
            elif not exact and not set(p_value).issubset(set(value)):
                return False

        return True


CANDIDATE_POLICY_METHOD = {
    'new_policy': 1,
    'append': 2,
    'tag': 3,
}


class CandidatePolicy(object):
    """
    candidate policy stores the target element(s) or new policy and a list of the best matched policies
    that can be appended to.
    """

    # method constants
    NEW_POLICY = 1
    APPEND_POLICY = 2
    TAG_OBJECT = 3

    def __init__(self, target_dict, matched_policies=None, method=NEW_POLICY):

        self.target_dict = target_dict
        self.matched_policies = matched_policies
        self.policy = None
        self.method = method

        if matched_policies and len(matched_policies) == 1:
            # this will be an addendum to an existing policy and there was only one match
            self.set_base_policy(matched_policies[0])
        else:
            self.set_base_policy()

    def set_base_policy(self, matched_policy=None):

        if self.method is self.NEW_POLICY or self.matched_policies is None:
            # this will be a new policy
            # TODO figure out logging default?
            self.policy = Policy(name=None,
                                 action=self.target_dict.get('action'),
                                 description=self.target_dict.get('description'),
                                 logging=self.target_dict.get('logging', "session-close")
                                 )
            self.policy.src_zones = self.target_dict.get('source_zones')
            self.policy.dst_zones = self.target_dict.get('destination_zones')
            self.policy.src_addresses = self.target_dict.get('source_addresses')
            self.policy.dst_addresses = self.target_dict.get('destination_addresses')
            self.policy.services = self.target_dict.get('services')

            self.method = self.NEW_POLICY

        elif isinstance(matched_policy, Policy):
            self.policy = matched_policy
        else:
            self.policy = matched_policy[0]

    def set_name(self, name):

        # if this is a new policy, set the name otherwise do nothing
        if self.method is self.NEW_POLICY:
            pattern = re.compile("^([A-Za-z0-9-_]+)+$")
            if not pattern.match(name):
                raise BadCandidatePolicyError('Name contains invalid character(s)')
            else:
                self.policy.name = name
