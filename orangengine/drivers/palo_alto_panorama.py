# -*- coding: utf-8 -*-
from orangengine.drivers.palo_alto_base import PaloAltoBaseDriver
from orangengine.models.paloalto import PaloAltoPolicy
from orangengine.models.paloalto import PaloAltoAddress
from orangengine.models.paloalto import PaloAltoAddressGroup
from orangengine.models.paloalto import PaloAltoService
from orangengine.models.paloalto import PaloAltoServiceGroup
from orangengine.models.paloalto import PaloAltoApplication
from orangengine.models.paloalto import PaloAltoApplicationGroup
from orangengine.models.base import CandidatePolicy
from orangengine.utils import missing_cidr
from orangengine.errors import BadCandidatePolicyError

from pandevice import panorama
from pandevice import objects
from pandevice import policies

from collections import defaultdict
import json


class PaloAltoPanoramaDriver(PaloAltoBaseDriver):

    # TODO shared and dev-group object namespaces are independent (meaning the same name can exist in both)
    # this means that before a policy change is enacted, we must verify the existence of an object or create
    # it within the given namespace, as an assumption is made in the matching stage that may not always hold
    # true. Please remember this later... it took a while to figure this out the first time John...
    # when doing a lookup, start with the local context and go up the tree

    def __init__(self, *args, **kwargs):
        """
        We need additional information for this driver
        """

        # now call the super
        super(PaloAltoPanoramaDriver, self).__init__(*args, **kwargs)

        self.dg_hierarchy = None
        self.dg_context = None

    def set_context(self, device_group=None):
        """Set the device_group context for future operations"""
        self.dg_context = self.dg_hierarchy.get_node(device_group)

    def _get_context(self, device_group_name=None):
        if device_group_name:
            context = self.dg_hierarchy.get_node(device_group_name)
            if not context:
                # use the shared dg context
                return self.dg_hierarchy.root
            else:
                return context
        else:
            return self.dg_context

    def policy_match(self, match_criteria, match_containing_networks=True, exact=False, policies=None,
                     device_group=None, include_parents=True):
        """Policy Match

        Overriden to allow passing an optional device group context which defaults to the shared
        namespace.
        """
        context = self._get_context(device_group)
        if not policies:
            policies = context.get_rulebase(include_parents)

        # now call the super to actually do the work
        matches = super(PaloAltoPanoramaDriver, self).policy_match(match_criteria, match_containing_networks=True,
                                                                   exact=False, policies=policies)
        return matches

    def candidate_policy_match(self, match_criteria, policies=None, device_group=None, include_parents=True,
                               post_rulebase=True):
        """Policy Match

        Overriden to allow passing an optional device group context which defaults to the shared
        namespace.
        """
        context = self._get_context(device_group)
        if not policies:
            policies = context.get_rulebase(include_parents)

        # now call the super to actually do the work
        candidate_policy = super(PaloAltoPanoramaDriver, self).candidate_policy_match(match_criteria, policies)

        zero_key = candidate_policy.policy_criteria.keys()
        if zero_key:
            zero_key = zero_key[0]

        if candidate_policy.method == CandidatePolicy.Method.APPEND and len(candidate_policy.policy_criteria) == 1 and \
                zero_key in ['source_addresses', 'destination_addresses']:

            # determine tagginess
            if zero_key == 'source_addresses':
                address_base = candidate_policy.policy.src_addresses
            else:
                address_base = candidate_policy.policy.dst_addresses

            address_groups = filter(lambda x: isinstance(x, PaloAltoAddressGroup) and x.dynamic_value, address_base)

            tag_options = {}
            address_group_tag_options = {}

            if address_groups:

                for address_group in address_groups:
                    address_group_tag_options[address_group.name] = self.tag_delta(address_group.dynamic_value, [])

                for address in candidate_policy.policy_criteria[zero_key]:
                    tag_options[address] = {}
                    address_objs = context.find_by_value(address, PaloAltoAddress) or []

                    for address_obj in address_objs:
                        tag_options[address][address_obj.name] = {}

                        for address_group in address_groups:
                            tag_delta = self.tag_delta(address_group.dynamic_value, address_obj.pandevice_object.tag)
                            tag_options[address][address_obj.name][address_group.name] = tag_delta

            if address_group_tag_options:
                candidate_policy.tag_options = tag_options
                candidate_policy.address_group_tag_options = address_group_tag_options
                candidate_policy.method = CandidatePolicy.Method.TAG

        if candidate_policy.method in [CandidatePolicy.Method.NEW_POLICY, CandidatePolicy.Method.APPEND]:
            candidate_policy.linked_objects = self.candidate_policy_link_new(candidate_policy.policy_criteria, context)

        candidate_policy.context = context
        candidate_policy.shared_namespace = True
        candidate_policy.post_rulebase = True

        return candidate_policy

    @staticmethod
    def candidate_policy_link_new(policy_criteria, context):
        """Given the policy criteria for a new candidate policy,
        link existing objects
        """

        linked_objects = {}
        interesting_keys = [
            'source_addresses',
            'destination_addresses',
            'services',
            'applications',
        ]

        for key in list(set(policy_criteria.keys()).intersection(set(interesting_keys))):

            linked_objects[key] = {}
            for v in policy_criteria[key]:

                obj = None
                if key in ['source_addresses', 'destination_addresses']:
                    obj = context.find_by_value(missing_cidr(v), PaloAltoAddress)

                elif key == 'services':
                    obj = context.find_by_value(v, PaloAltoService)

                elif key == 'applications':
                    obj = context.find_by_value(v, PaloAltoApplication)

                if obj:
                #    # now we have to figure out object precedence
                #    found_objs = obj
                #    for o in found_objs:
                #        _o = context.find(name=o.name, cls=type(o))
                #        if _o == o:
                #            obj = o
                #            break
                #    if obj == found_objs:
                #        # no object after precedence check
                #        obj = None
                    obj = obj[0]
                linked_objects[key][v] = obj

        return linked_objects

    def _get_config(self):
        """refresh the pandevice object and create the device group hierarchy"""

        # now call the super
        super(PaloAltoPanoramaDriver, self)._get_config()

        dg_xml = self.device.op('<show><dg-hierarchy></dg-hierarchy></show>', cmd_xml=False)
        self.dg_hierarchy = _DeviceGroupHierarchy(self.device, dg_xml)

    def _parse_addresses(self):
        """retrieve all the pandevice.objects.AddressObjects's and parse them and store in the dg node"""

        # create the "any" object
        any_address_pandevice_obj = objects.AddressObject()
        any_address_pandevice_obj.name = 'any'
        any_address_pandevice_obj.type = 'any'
        any_address_pandevice_obj.value = 'any'
        any_address = PaloAltoAddress(any_address_pandevice_obj)

        for dg_node in self.dg_hierarchy.get_all_nodes():
            for a in dg_node.device_group.findall(objects.AddressObject):
                dg_node.insert(PaloAltoAddress(a))

            # add the "any" abject
            dg_node.insert(any_address)

    def _parse_address_groups(self):
        """retrieve all the pandevice.objects.AddressGroup's and parse them and store in the dg node"""
        for dg_node in self.dg_hierarchy.get_all_nodes():
            for ag in dg_node.device_group.findall(objects.AddressGroup):
                address_group = PaloAltoAddressGroup(ag)
                if ag.static_value:
                    for v in ag.static_value:
                        # find and link the actual object
                        address_group.add(dg_node.find(v, PaloAltoAddress))
                else:
                    address_group.dynamic_value = ag.dynamic_value
                dg_node.insert(address_group)

    def _parse_services(self):
        """retrieve all the pandevice.objects.ServiceObject's and parse them and store in the dg node"""

        # create the "any" object
        any_service_pandevice_obj = objects.ServiceObject()
        any_service_pandevice_obj.name = 'any'
        any_service_pandevice_obj.protocol = 'any'
        any_service_pandevice_obj.destination_port = 'any'
        any_service = PaloAltoService(any_service_pandevice_obj)

        # create the "application-default" object
        app_default_service_pan_obj = objects.ServiceObject()
        app_default_service_pan_obj.name = 'application-default'
        app_default_service = PaloAltoService(app_default_service_pan_obj)

        for dg_node in self.dg_hierarchy.get_all_nodes():
            for s in dg_node.device_group.findall(objects.ServiceObject):
                dg_node.insert(PaloAltoService(s))

            # add the "any" object
            dg_node.insert(any_service)

            # add the "application-default" object
            dg_node.insert(app_default_service)

    def _parse_service_groups(self):
        """retrieve all the pandevice.objects.ServiceGroup's and parse them and store in the dg node"""
        for dg_node in self.dg_hierarchy.get_all_nodes():
            for sg in dg_node.device_group.findall(objects.ServiceGroup):
                service_group = PaloAltoServiceGroup(sg)
                for v in sg.value:
                    # find and link the actual object
                    service_group.add(dg_node.find(v, PaloAltoService))
                dg_node.insert(service_group)

    def _parse_applications(self):
        """retrieve all the pandevice.objects.Application's and parse them and store in the dg node"""

        # create the "any" object
        any_application_pandevice_obj = objects.ApplicationObject()
        any_application_pandevice_obj.name = 'any'
        any_applciation = PaloAltoApplication(any_application_pandevice_obj)

        for dg_node in self.dg_hierarchy.get_all_nodes():
            for app in dg_node.device_group.findall(objects.ApplicationObject):
                dg_node.insert(PaloAltoApplication(app))

            # add the "any" object
            dg_node.insert(any_applciation)

        # now load the predefined applications into the shared namespace
        for app in self.device.predefined.application_objects.values():
            self.dg_hierarchy.root.insert(PaloAltoApplication(app))

    def _parse_application_groups(self):
        """retrieve all the pandevice.objects.ApplicationGroups's and parse them and store in the dg node"""
        for dg_node in self.dg_hierarchy.get_all_nodes():

            # grab teh regular groups
            for app_group in dg_node.device_group.findall(objects.ApplicationGroup):
                application_group = PaloAltoApplicationGroup(app_group)
                for app in app_group.value:
                    # find and link the actual object
                    application_group.add(dg_node.find(app, PaloAltoApplication))
                dg_node.insert(application_group)

        # now grab the application containers from the predefined area and store them in the shared namespace
        for app_container in self.device.predefined.application_container_objects.values():
            # app containers are semantically app groups
            application_group = PaloAltoApplicationGroup(app_container)
            for app in app_container.applications:
                # find and link the actual objects from the shared namespace
                application_group.add(self.dg_hierarchy.root.find(app, PaloAltoApplication))
            self.dg_hierarchy.root.insert(application_group)

    def _parse_policies(self):
        """retrieve all the pandevice.policies.SecurityRule's and parse them and store in the dg node"""

        def link_objects(policy, node):
            """given a PaloAltoPolicy and a dg node, find and link all the objects"""

            # zones
            for s_zone in policy.pandevice_object.fromzone:
                policy.add_src_zone(s_zone)
            for d_zone in policy.pandevice_object.tozone:
                policy.add_dst_zone(d_zone)

            # source addresses
            for sa in policy.pandevice_object.source:
                address = node.find(sa, PaloAltoAddress)
                policy.add_src_address(address)

            # destination addresses
            for da in policy.pandevice_object.destination:
                address = node.find(da, PaloAltoAddress)
                policy.add_dst_address(address)

            # applications
            for app in policy.pandevice_object.application:
                application = node.find(app, PaloAltoApplication)
                policy.add_application(application)

            # services
            for s in policy.pandevice_object.service:
                service = node.find(s, PaloAltoService)
                policy.add_service(service)

        # get all the device groups
        for dg_node in self.dg_hierarchy.get_all_nodes():
            # pre rulebase
            for pre_rulebase in dg_node.device_group.findall(policies.PreRulebase):
                for security_rule in pre_rulebase.findall(policies.SecurityRule):
                    palo_alto_policy = PaloAltoPolicy(security_rule)
                    link_objects(palo_alto_policy, dg_node)
                    dg_node.insert(palo_alto_policy)
            # post rulebase
            for post_rulebase in dg_node.device_group.findall(policies.PostRulebase):
                for security_rule in post_rulebase.findall(policies.SecurityRule):
                    palo_alto_policy = PaloAltoPolicy(security_rule)
                    link_objects(palo_alto_policy, dg_node)
                    dg_node.insert(palo_alto_policy)

    def apply_candidate_policy(self, candidate_policy, commit=False):
        """Given a candidate policy, use its method to apply the effect of that policy.

        Candidate policies that originate from this driver contain a few extra (special)
        attributes used to make decisions on how to source and create new objects.
        """

        if isinstance(candidate_policy, dict):
            candidate_policy = self.candidate_policy_from_json(json.dumps(candidate_policy))

        if candidate_policy.policy is None:
            raise BadCandidatePolicyError("Missing a policy object!")

        pandevice_policy_object = candidate_policy.policy.pandevice_object

        if candidate_policy.shared_namespace:
            device_group = self.dg_hierarchy.root.device_group
        else:
            device_group = candidate_policy.context.device_group

        if candidate_policy.method == CandidatePolicy.Method.TAG:

            # TAG method

            if not candidate_policy.tag_choices or len(candidate_policy.tag_choices) != \
               len(candidate_policy.policy_criteria.values()[0]):
                raise BadCandidatePolicyError("Tag choices not set")

            """

            tag_choices = {
                '1.1.1.1/32': [chosen_tags]  # userid tagging
            }

            tag_choices = {
                '1.1.1.1/32': {
                    'chosen_address_object': [chosen_tags]  # object tagging
                }
            }
            """

            for address, value in candidate_policy.tag_choices.iteritems():

                if isinstance(value, list):
                    # this will be an address/tag registration via the userid system

                    tags = value
                    self.device.userid.register(address, tags)

                elif isinstance(value, dict):
                    # this will be adding tags to an object and commiting

                    obj_name = value.keys()[0]
                    tags = value[obj_name]
                    context = candidate_policy.context

                    if candidate_policy.new_objects:
                        for key, _value in candidate_policy.new_objects.iteritems():
                            # create all the new pan device objects on the device group
                            for _obj in _value.values():
                                self._create_object(device_group, _obj)
                                obj = _obj
                    else:
                        obj = context.find(obj_name, PaloAltoAddress)

                    current_tags = obj.pandevice_object.tag
                    if not current_tags:
                        current_tags = []
                    current_tags.extend(tags)
                    obj.pandevice_object.tag = current_tags
                    obj.pandevice_object.apply()

                else:
                    raise BadCandidatePolicyError("No chosen tags present")

        else:

            # either APPEND or NEW_POLICY but we treat them mostly the same

            interesting_keys = [
                'source_addresses',
                'destination_addresses',
                'services',
                'applications'
            ]

            # check objects
            for key, value in candidate_policy.policy_criteria.iteritems():
                if key in interesting_keys:
                    for v in value:
                        if not candidate_policy.linked_objects.get(key, {}).get(v) and \
                           not candidate_policy.new_objects.get(key, {}).get(v):
                            raise BadCandidatePolicyError("Missing object for {0}".format(v))

            # choose the rulebase and check the name
            if candidate_policy.post_rulebase:
                rulebase = candidate_policy.context.device_group.find_or_create(None, policies.PostRulebase)
                if candidate_policy.method == CandidatePolicy.Method.NEW_POLICY and \
                   candidate_policy.context.name_lookup['post_rulebase'].get(candidate_policy.policy.name):
                    raise BadCandidatePolicyError("Policy named '{0}' already exists on the device"
                                                  .format(candidate_policy.policy.name))
            else:
                rulebase = candidate_policy.context.device_group.find_or_create(None, policies.PreRulebase)
                if candidate_policy.method == CandidatePolicy.Method.NEW_POLICY and \
                   candidate_policy.context.name_lookup['pre_rulebase'].get(candidate_policy.policy.name):
                    raise BadCandidatePolicyError("Policy named '{0}' already exists on the device"
                                                  .format(candidate_policy.policy.name))

            for key, value in candidate_policy.new_objects.iteritems():
                # create all the new pan device objects on the device group
                for obj in value.values():
                    self._create_object(device_group, obj.pandevice_object)

            # all objects are now valid, so merge them
            merged_objects = {}
            for key in interesting_keys:
                merged_objects[key] = {}
                linked_key = candidate_policy.linked_objects.get(key)
                if linked_key:
                    merged_objects[key] = linked_key
                new_key = candidate_policy.new_objects.get(key)
                if new_key:
                    merged_objects[key].update(new_key)


            # now link the objects to the policy
            self._link_policy_objects(pandevice_policy_object, merged_objects, candidate_policy.policy_criteria)

            # update the policy
            self._apply_object(rulebase, pandevice_policy_object)

        if commit:
            self.device.commit_all(sync=True, devicegroup=candidate_policy.context.device_group.name)

    def apply_policy(self, policy, commit=False):
        pass

    def candidate_policy_from_json(self, json_data):
        """Construct an instance of CandidatePolicy from a json dump
        """

        data = json.loads(json_data)
        policy_criteria = self._sanitize_match_criteria(data['policy_criteria'])
        method = CandidatePolicy.MethodMap[data['method']]
        context = self.dg_hierarchy.get_node(data['context'])

        matched_policies = []
        for matched_policy in data['matched_policies']:
            matched_policies.append(context.find(matched_policy['name'], PaloAltoPolicy))

        candidate_policy = CandidatePolicy(policy_criteria, matched_policies, method)
        candidate_policy.context = context
        candidate_policy.tag_options = data['tag_options']
        candidate_policy.tag_choices = data['tag_choices']
        candidate_policy.address_group_tag_options = data['address_group_tag_options']
        candidate_policy.shared_namespace = data['shared_namespace']
        candidate_policy.post_rulebase = data['post_rulebase']

        if candidate_policy.method == CandidatePolicy.Method.NEW_POLICY:
            if not data.get('policy'):
                raise BadCandidatePolicyError("No policy object provided to meet new policy requirement")
            else:
                candidate_policy.policy = PaloAltoPolicy.from_criteria(data['policy'])

        elif matched_policies and data.get('policy'):
            if candidate_policy.post_rulebase:
                policy = context.name_lookup['post_rulebase'].get(data['policy']['name'])
            else:
                policy = context.name_lookup['post_rulebase'].get(data['policy']['name'])
            candidate_policy.set_base_policy(policy)

        linked_objects = {}
        for key, values in data['linked_objects'].iteritems():
            linked_objects[key] = {}
            for k, v in values.iteritems():
                if key == 'services' and k != 'any':
                    k = (v['protocol'], v['port'])
                if not v:
                    linked_objects[key][k] = None
                    continue
                if key in ['source_addresses', 'destination_addresses']:
                    cls = PaloAltoAddress
                    value = v['value']
                elif key == 'services':
                    cls = PaloAltoService
                    value = k
                else:
                    cls = PaloAltoApplication
                    value = None  # TODO: figure out a proper 'value' for PaloAltoApplication here
                linked_objects[key][k] = context.find_by_name_value(v['name'], value, cls)
        candidate_policy.linked_objects = linked_objects

        # new objects
        new_objects = {}
        for key, values in data['new_objects'].iteritems():
            new_objects[key] = {}
            for k, v in values.iteritems():
                if key == 'services' and k != 'any':
                    parts = k.split("/")
                    k = tuple(parts)
                if not v:
                    new_objects[key][k] = None
                elif key in ['source_addresses', 'destination_addresses']:
                    new_objects[key][k] = PaloAltoAddress.from_criteria(v)
                elif key == 'services':
                    new_objects[key][k] = PaloAltoService.from_criteria(v)
        candidate_policy.new_objects = new_objects

        return candidate_policy


class _DeviceGroupNode(object):
    def __init__(self):
        self.device_group = None
        self.parent = None
        self.children = []
        self.objects = {
            'services': [],
            'service_groups': [],
            'applications': [],
            'application_groups': [],
            'addresses': [],
            'address_groups': [],
            'pre_rulebase': [],
            'post_rulebase': []
        }
        self.name_lookup = {  # factors in sister namespaces
            'services': dict(),
            'addresses': dict(),
            'applications': dict(),
            'pre_rulebase': dict(),
            'post_rulebase': dict(),
        }
        self.value_lookup = {
            'services': defaultdict(list),
            'addresses': defaultdict(list),
            'applications': defaultdict(list),
        }

    def insert(self, obj):
        """insert a object into the necasary data stores"""

        cls = type(obj)

        if cls == PaloAltoAddress or cls == PaloAltoAddressGroup:
            if cls == PaloAltoAddress:
                self.objects['addresses'].append(obj)
                self.value_lookup['addresses'][missing_cidr(obj.value)].append(obj)
            else:
                self.objects['address_groups'].append(obj)
            self.name_lookup['addresses'][obj.name] = obj

        elif cls == PaloAltoService or cls == PaloAltoServiceGroup:
            if cls == PaloAltoService:
                self.objects['services'].append(obj)
                self.value_lookup['services'][obj.value].append(obj)
            else:
                self.objects['service_groups'].append(obj)
            self.name_lookup['services'][obj.name] = obj

        elif cls == PaloAltoApplication or cls == PaloAltoApplicationGroup:
            if cls == PaloAltoApplication:
                self.objects['applications'].append(obj)
            else:
                self.objects['application_groups'].append(obj)
            self.name_lookup['applications'][obj.name] = obj
            self.value_lookup['applications'][obj.name].append(obj)  # special case to include predefined containers

        elif cls == PaloAltoPolicy:
            rule_base_type = type(obj.pandevice_object.parent)
            if rule_base_type == policies.PreRulebase:
                self.objects['pre_rulebase'].append(obj)
                self.name_lookup['pre_rulebase'][obj.name] = obj
            else:
                self.objects['post_rulebase'].append(obj)
                self.name_lookup['post_rulebase'][obj.name] = obj

        else:
            raise TypeError("Object of this type ({0}) cannot be insert".format(cls))

    def get_rulebase(self, include_parents=True):
        """return a single list containing all policies from pre and post rulebases"""
        rulebase = []
        rulebase.extend(self.objects['pre_rulebase'])
        rulebase.extend(self.objects['post_rulebase'])
        if include_parents and self.parent:
            rulebase.extend(self.parent.get_rulebase())
        return rulebase

    def find(self, name, cls, recursive=True):
        """find an object by name"""

        obj = None

        if cls == PaloAltoAddress or cls == PaloAltoAddressGroup:
            obj = self.name_lookup['addresses'].get(name)

        elif cls == PaloAltoService or cls == PaloAltoServiceGroup:
            obj = self.name_lookup['services'].get(name)

        elif cls == PaloAltoApplication or cls == PaloAltoApplicationGroup:
            obj = self.name_lookup['applications'].get(name)

        elif cls == PaloAltoPolicy:
            obj = self.name_lookup['pre_rulebase'].get(name)
            if not obj:
                obj = self.name_lookup['post_rulebase'].get(name)

        if not obj and recursive and self.parent:
            obj = self.parent.find(name, cls, recursive)

        return obj

    def find_by_value(self, value, cls, recursive=True):
        """find objects by value"""

        objs = None

        if cls == PaloAltoAddress or cls == PaloAltoAddressGroup:
            objs = self.value_lookup['addresses'].get(missing_cidr(value))

        elif cls == PaloAltoService or cls == PaloAltoServiceGroup:
            objs = self.value_lookup['services'].get(value)

        elif cls == PaloAltoApplication or cls == PaloAltoApplicationGroup:
            objs = self.value_lookup['applications'].get(value)

        if not objs and recursive and self.parent:
            objs = self.parent.find_by_value(value, cls, recursive)

        return objs

    def find_by_name_value(self, name, value, cls, recursive=True):
        """find an object by both name AND value together"""

        obj = None

        if cls == PaloAltoAddress or cls == PaloAltoAddressGroup:
            _obj = self.name_lookup['addresses'].get(name)
            if _obj and _obj.value == value:
                obj = _obj

        elif cls == PaloAltoService or cls == PaloAltoServiceGroup:
            _obj = self.name_lookup['services'].get(name)
            if _obj and _obj.value == value:
                obj = _obj

        elif cls == PaloAltoApplication or cls == PaloAltoApplicationGroup:
            obj = self.name_lookup['applications'].get(name)

        if not obj and recursive and self.parent:
            obj = self.parent.find_by_name_value(name, value, cls, recursive)

        return obj


class _DeviceGroupHierarchy(object):
    """Basically a doubly linked-list to create the device group hierarchy
    """

    def __init__(self, panorama_obj, xml_hierarchy):

        self.lookup = {}
        self.root = _DeviceGroupNode()
        self.root.device_group = panorama_obj.shared
        self.panorama_obj = panorama_obj
        self.lookup['shared'] = self.root

        xml_hierarchy = xml_hierarchy.find('result/dg-hierarchy')
        self._parse_nodes(xml_hierarchy, self.root)

    def _parse_nodes(self, xml, parent):
        if xml.tag == 'dg':
            # this is a single element
            xml = [xml]
        for dg in xml:
            node = _DeviceGroupNode()
            node.device_group = self.panorama_obj.find(dg.attrib['name'], panorama.DeviceGroup)
            node.parent = parent
            parent.children.append(node)
            self.lookup[node.device_group.name] = node
            for child in dg:
                self._parse_nodes(child, node)

    def get_node(self, device_group_name):
        if device_group_name:
            node = self.lookup.get(device_group_name)
            if not node:
                raise LookupError('Device group could not be found')
        else:
            node = None

        return node

    def get_all_nodes(self):
        return self.lookup.values()
