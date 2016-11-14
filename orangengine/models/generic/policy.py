
from orangengine.errors import BadCandidatePolicyError

from collections import Iterable
import re


class Policy(object):

    def __init__(self, name, action, description, logging):
        """init policy"""

        self.name = name
        self.src_zones = list()
        self.dst_zones = list()
        self.src_addresses = list()
        self.dst_addresses = list()
        self.services = list()
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

    def __getattr__(self, item):
        """
        return a tuple representation of the policy with normalized values
        """

        if item == 'value':
            s_addrs = set(Policy.__flatten([a.value for a in self.src_addresses]))
            d_addrs = set(Policy.__flatten([a.value for a in self.dst_addresses]))
            services = set(Policy.__flatten([s.value for s in self.services]))

            return self.src_zones, self.dst_zones, list(s_addrs), list(d_addrs), list(services), self.action

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


class CandidatePolicy(object):
    """
    candidate policy stores the target element(s) or new policy and a list of the best matched policies
    that can be appended to.
    """

    def __init__(self, target_dict, matched_policies=None):

        self.target_dict = target_dict
        self.matched_policies = matched_policies
        self.policy = None
        self.new_policy = False

        if len(matched_policies) == 1:
            # this will be an addendum to an existing policy and there was only one match
            self.set_base_policy(matched_policies[0])
        else:
            self.set_base_policy()

    def set_base_policy(self, matched_policy=None):

        if matched_policy is None:
            # this will be a new policy
            # TODO figure out logging default?
            self.policy = Policy(name=None,
                                 action=self.target_dict.get('action'),
                                 description=self.target_dict.get('description'),
                                 logging=self.target_dict.get('logging', "session-end")
                                 )
            self.policy.src_zones = self.target_dict.get('source_zones')
            self.policy.dst_zones = self.target_dict.get('destination_zones')
            self.policy.src_addresses = self.target_dict.get('source_addresses')
            self.policy.dst_addresses = self.target_dict.get('destination_addresses')
            self.policy.services = self.target_dict.get('services')

            self.new_policy = True
        else:
            self.policy = matched_policy

    def set_name(self, name):

        if self.new_policy:
            pattern = re.compile("^([A-Za-z0-9-_]+)+$")
            if not pattern.match(name):
                raise BadCandidatePolicyError('Name contains invalid character(s)')
            else:
                self.policy.name = name
