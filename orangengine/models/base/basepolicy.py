# -*- coding: utf-8 -*-
from orangengine.utils import is_ipv4, enum, bidict, flatten
from orangengine.models.base import BaseObject

from collections import defaultdict
from netaddr import IPRange, IPNetwork
from terminaltables import AsciiTable
from functools import partial


class BasePolicy(BaseObject):

    Action = enum('ALLOW', 'DENY', 'REJECT', 'DROP')
    Logging = enum('START', 'END')

    ActionMap = bidict({
        Action.ALLOW: "Allow",
        Action.DENY: "Deny",
        Action.REJECT: "Reject",
        Action.DROP: 'Drop',
    })

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

    def serialize(self):
        """Searialize self to a json acceptable data structure
        """

        s_addrs = list(map(lambda x: x.serialize(), self.src_addresses))
        d_addrs = list(map(lambda x: x.serialize(), self.dst_addresses))
        services = list(map(lambda x: x.serialize(), self._services))

        return {
            'name': self.name,
            'source_zones': self.src_zones,
            'source_addresses': s_addrs,
            'destination_zones': self.dst_zones,
            'destination_addresses': d_addrs,
            'services': services,
            'action': self.ActionMap[self.action],
            'description': self.description,
            'logging': self.logging
        }

    def __getattr__(self, item):
        """
        return a tuple representation of the policy with normalized values
        """

        # s_addrs = set(flatten([a.value for a in self.src_addresses]))
        # d_addrs = set(flatten([a.value for a in self.dst_addresses]))
        # services = set(flatten([s.value for s in self._services]))

        if item == 'value':
            # return self.src_zones, self.dst_zones, list(s_addrs), list(d_addrs), list(services), self.action
            pass

        # for use in policy match element reducing
        elif item == 'source_zones':
            return self.src_zones
        elif item == 'destination_zones':
            return self.dst_zones
        elif item == 'source_addresses':
            return set(flatten([a.value for a in self.src_addresses]))
        elif item == 'destination_addresses':
            return set(flatten([a.value for a in self.dst_addresses]))
        elif item == 'services':
            return set(flatten([s.value for s in self._services]))
        elif item == 'services_objects':
            return self._services

        else:
            raise AttributeError()

    @staticmethod
    def _in_network(value, p_value, exact_match=False):
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
        for a in addresses:
            addr_result = any(a == b or a in b for b in p_addresses)
            if not addr_result:
                return False

        # now match the fqdns
        if exact_match:
            fqdn_result = set(fqdns) == set(p_fqdns)
        else:
            fqdn_result = set(p_fqdns).issubset(set(fqdns))

        return fqdn_result

    def match(self, match_criteria, exact=False, match_containing_networks=True):
        """
        determine if self is a match for the given criteria
        """
        for key, value in match_criteria.iteritems():
            if not value:
                # this key was included but has no value so skip it
                continue

            p_value = getattr(self, key, [])

            if p_value == 'any' and key in ['source_addresses', 'destination_addresses', 'services']:
                # 'any' as address constitutes a match, so move on
                continue
            elif key == 'action':
                # compare against the converted value
                if self.ActionMap[value] != p_value:
                    return False
            elif len(value) > len(p_value):
                # more values in the match than the policy, fail
                return False
            elif match_containing_networks and key in ['source_addresses', 'destination_addresses']:
                if not self._in_network(value, p_value, exact_match=True):
                    return False
            elif exact and not set(p_value) == set(value):
                return False
            elif not exact and not set(value).issubset(set(p_value)):
                return False

        return True

    def candidate_match(self, match_criteria, exact=False, match_containing_networks=True):
        """
        wrap the match method in some extra logic to determine if this is a candidate for policy addition
        """
        unique_key = None
        for key, value in match_criteria.iteritems():
            match = self.match({key: value}, exact, match_containing_networks)
            if not match:
                if unique_key:
                    # the unique key is already set so we fail
                    return False
                else:
                    # found a unique key
                    unique_key = key

        # if we survived, this is a candidate policy so return which key is unique
        return unique_key

    @staticmethod
    def table_address_cell(addresses, with_names=False):
        return "\n".join([a.table_value(with_names) for a in addresses]) + '\n'

    @staticmethod
    def table_service_cell(services, with_names=False):
        return "\n".join([s.table_value(with_names) for s in services]) + '\n'

    @staticmethod
    def table_zone_cell(zones):
        return "\n".join([z for z in zones]) + '\n'

    def table_header(self):
        """Return the table header for the based policy
        """
        return ["Src Zones", "Src Addresses", "Dst Zones", "Dst Addresses", "Services", "Action"]

    def table_row(self, with_names=False):
        """Return the table row for the based policy
        """
        s_zones = self.table_zone_cell(self.src_zones)
        d_zones = self.table_zone_cell(self.dst_zones)
        s_addresses = self.table_address_cell(self.src_addresses, with_names)
        d_addresses = self.table_address_cell(self.dst_addresses, with_names)
        services = self.table_service_cell(self._services, with_names)

        return [s_zones, s_addresses, d_zones, d_addresses, services, self.ActionMap[self.action]]

    def to_table(self, with_names=False):
        """Return the policy as an ascii tables

        Args:
            with_names (bool): Include object names
        """
        table_header = self.table_header()

        table_row = self.table_row(with_names=with_names)

        table = AsciiTable([table_header, table_row])
        table.title = "Policy: " + self.name

        return table.table

    @classmethod
    def from_criteria(cls, criteria):
        """Create an instance from the provided criteria
        """

        logging = []
        logging_criteria = criteria.get('logging', [])

        if 'start' in logging_criteria or 'both' in logging_criteria:
            logging.append(cls.Logging.START)
        if 'end' in logging_criteria or 'both' in logging_criteria:
            logging.append(cls.Logging.END)

        return cls(criteria['name'], cls.ActionMap[criteria['action']], criteria.get('description'), logging)


class CandidatePolicy(BaseObject):
    """
    candidate policy stores the target element(s) or new policy and a list of the best matched policies
    that can be appended to.
    """

    # implementation methods
    Method = enum('NEW_POLICY', 'APPEND', 'TAG')
    MethodMap = bidict({
        Method.NEW_POLICY: 'NEW_POLICY',
        Method.APPEND: 'APPEND',
        Method.TAG: 'TAG',
    })

    def __init__(self, policy_criteria, matched_policies=None, method=Method.NEW_POLICY):

        self.policy_criteria = policy_criteria
        self.matched_policies = matched_policies or []
        self.policy = None
        self.method = method
        self.tag_options = {}
        self.tag_choices = {}
        self.linked_objects = {}
        self.new_objects = {}

        # Palo Alto/Panorama specific params
        self.address_group_tag_options = {}
        self.shared_namespace = True
        self.context = None
        self.post_rulebase = True

        if self.method != self.Method.NEW_POLICY:
            # this will be an addendum to an existing policy default to the first policy
            self.set_base_policy(matched_policies[0])

    def set_base_policy(self, policy):
        """Set or change the base policy"""
        if policy in self.matched_policies:
            self.policy = policy
        else:
            raise ValueError("Policy is not valid for this candidate policy")

    def serialize(self):
        """Serialize self into json compatible data structures
        """

        linked_objects = {}
        for key, value in self.linked_objects.iteritems():
            linked_objects[key] = {}
            for k, v in value.iteritems():
                if key == 'services' and k != 'any':
                    k = k[0] + "/" + k[1]
                if hasattr(v, 'serialize'):
                    linked_objects[key][k] = v.serialize()
                else:
                    linked_objects[key][k] = v

        new_objects = {}
        for key, value in self.new_objects.iteritems():
            new_objects[key] = {}
            for k, v in value.iteritems():
                if key == 'services' and k != 'any':
                    k = k[0] + "/" + k[1]
                if hasattr(v, 'serialize'):
                    new_objects[key][k] = v.serialize()
                else:
                    new_objects[key][k] = v

        if self.context:
            context = self.context.device_group.name
        else:
            context = None

        if self.matched_policies:
            matched_policies = list(map(lambda x: x.serialize(), self.matched_policies))
        else:
            matched_policies = []

        if self.policy:
            policy = self.policy.serialize()
        else:
            policy = None

        return {
            'policy_criteria': self.policy_criteria,
            'matched_policies': matched_policies,
            'policy': policy,
            'method': self.MethodMap[self.method],
            'tag_options': self.tag_options,
            'tag_choices': self.tag_choices,
            'linked_objects': linked_objects,
            'new_objects': new_objects,
            'context': context,
            'address_group_tag_options': self.address_group_tag_options,
            'shared_namespace': self.shared_namespace,
            'post_rulebase': self.post_rulebase
        }


class EffectivePolicy(object):
    """
    effective policy of an address target. Stores source and destination rules
    and provides table methods
    """

    class _TargetLookupObject(object):

        def __init__(self, policies, source):
            self.policy_lookup = dict()
            self.actions = set()

            for p in policies:
                self.policy_lookup[p.name] = p
                self.actions.add(p.action)

            self.actions_lookup = defaultdict(partial(defaultdict, partial(defaultdict, list)))

            for a in self.actions:
                for name, policy in self.policy_lookup.iteritems():
                    for s in policy.services_objects:
                        self.actions_lookup[a]['service_lookup'][s].append(policy)
                    if source:
                        addresses = policy.dst_addresses
                    else:
                        addresses = policy.src_addresses
                    for addr in addresses:
                        self.actions_lookup[a]['address_lookup'][addr].append(policy)

    def __init__(self, address, source_policies, destination_policies):

        self.source_lookup_object = self._TargetLookupObject(source_policies, source=True)
        self.destination_lookup_object = self._TargetLookupObject(destination_policies, source=False)
        self.target = address

    def source_table(self, service_focus=True):

        table_header = ["Dst Zones", "Dst Addresses", "Services", "Action"]
        table_data = [table_header] + self._table_rows(self.source_lookup_object, True, service_focus)
        table = AsciiTable(table_data)
        table.title = "Effective Policy: " + self.target + " as source"

        return table.table

    def destination_table(self, service_focus=True):

        table_header = ["Src Zones", "Src Addresses", "Services", "Action"]
        table_data = [table_header] + self._table_rows(self.destination_lookup_object, False, service_focus)
        table = AsciiTable(table_data)
        table.title = "Effective Policy: " + self.target + " as destination"

        return table.table

    def to_table(self, service_focus=True):

        return self.source_table(service_focus) + '\n\n' + self.destination_table(service_focus)

    @staticmethod
    def _table_rows(lookup_table, source, service_focus=True):

        if service_focus:
            focus_key = 'service_lookup'
        else:
            focus_key = 'address_lookup'

        table_rows = []
        for action in lookup_table.actions_lookup.keys():
            for focus_target in lookup_table.actions_lookup[action][focus_key]:
                for policy in lookup_table.actions_lookup[action][focus_key][focus_target]:

                    if source:
                        _p_zones = policy.dst_zones
                        _p_addresses = policy.dst_addresses
                    else:
                        _p_zones = policy.src_zones
                        _p_addresses = policy.src_addresses

                    zones = BasePolicy.table_zone_cell(_p_zones)

                    if service_focus:
                        addresses = BasePolicy.table_address_cell(_p_addresses)
                        services = focus_target.table_value(with_names=False)
                    else:
                        addresses = focus_target.table_value(with_names=False)
                        services = BasePolicy.table_service_cell(policy.services_objects)

                    table_rows.append([zones, addresses, services, policy.ActionMap[policy.action]])

        return table_rows
