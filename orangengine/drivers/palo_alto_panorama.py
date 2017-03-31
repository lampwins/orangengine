
from orangengine.drivers.palo_alto_base import PaloAltoBaseDriver
from orangengine.models.paloalto import PaloAltoPolicy
from orangengine.models.paloalto import PaloAltoAddress
from orangengine.models.paloalto import PaloAltoAddressGroup
from orangengine.models.paloalto import PaloAltoService
from orangengine.models.paloalto import PaloAltoServiceGroup

from pandevice import panorama
from pandevice import objects
from pandevice import policies

import itertools


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

    def _get_config(self):
        """refresh the pandevice object and create the device group hierarchy"""
        self.device.refresh()
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
                dg_node.objects['addresses'].append(PaloAltoAddress(a))
            # add the "any" abject
            dg_node.objects['addresses'].append(any_address)

    def _parse_address_groups(self):
        """retrieve all the pandevice.objects.AddressGroup's and parse them and store in the dg node"""
        for dg_node in self.dg_hierarchy.get_all_nodes():
            for ag in dg_node.device_group.findall(objects.AddressGroup):
                address_group = PaloAltoAddressGroup(ag)
                if ag.static_value:
                    for v in ag.static_value:
                        # find and link the actual object
                        address_group.add(_DeviceGroupHierarchy.Node.find(dg_node, v, PaloAltoAddress))
                else:
                    address_group.dynamic_value = ag.dynamic_value
                dg_node.objects['address_groups'].append(address_group)

    def _parse_services(self):
        """retrieve all the pandevice.objects.ServiceObject's and parse them and store in the dg node"""
        # create the "any"object
        any_service_pandevice_obj = objects.ServiceObject()
        any_service_pandevice_obj.name = 'any'
        any_service_pandevice_obj.protocol = 'any'
        any_service_pandevice_obj.destination_port = 'any'
        any_service = PaloAltoService(any_service_pandevice_obj)
        for dg_node in self.dg_hierarchy.get_all_nodes():
            for s in dg_node.device_group.findall(objects.ServiceObject):
                dg_node.objects['services'].append(PaloAltoService(s))
            # add the "any" object
            dg_node.objects['services'].append(any_service)

    def _parse_service_groups(self):
        """retrieve all the pandevice.objects.ServiceGroup's and parse them and store in the dg node"""
        for dg_node in self.dg_hierarchy.get_all_nodes():
            for sg in dg_node.device_group.findall(objects.ServiceGroup):
                service_group = PaloAltoServiceGroup(sg)
                for v in sg.value:
                    # find and link the actual object
                    service_group.add(_DeviceGroupHierarchy.Node.find(dg_node, v, PaloAltoService))
                dg_node.objects['service_groups'].append(service_group)

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
                address = _DeviceGroupHierarchy.Node.find(node, sa, PaloAltoAddress)
                if not address:
                    address = _DeviceGroupHierarchy.Node.find(node, sa, PaloAltoAddressGroup)
                policy.add_src_address(address)

            # destination addresses
            for da in policy.pandevice_object.destination:
                address = _DeviceGroupHierarchy.Node.find(node, da, PaloAltoAddress)
                if not address:
                    address = _DeviceGroupHierarchy.Node.find(node, da, PaloAltoAddressGroup)
                policy.add_dst_address(address)

            # services
            for s in policy.pandevice_object.service:
                service = _DeviceGroupHierarchy.Node.find(node, s, PaloAltoService)
                if not service:
                    service = _DeviceGroupHierarchy.Node.find(node, s, PaloAltoServiceGroup)
                policy.add_service(service)

        # get all the device groups
        for dg_node in self.dg_hierarchy.get_all_nodes():
            # pre rulebase
            for pre_rulebase in dg_node.device_group.findall(policies.PreRulebase):
                for security_rule in pre_rulebase.findall(policies.SecurityRule):
                    palo_alto_policy = PaloAltoPolicy(security_rule)
                    link_objects(palo_alto_policy, dg_node)
                    dg_node.objects['pre_rulebase'].append(palo_alto_policy)
            # post rulebase
            for post_rulebase in dg_node.device_group.findall(policies.PostRulebase):
                for security_rule in post_rulebase.findall(policies.SecurityRule):
                    palo_alto_policy = PaloAltoPolicy(security_rule)
                    link_objects(palo_alto_policy, dg_node)
                    dg_node.objects['post_rulebase'].append(palo_alto_policy)

    def apply_candidate_policy(self, candidate_policy):
        pass

    def apply_policy(self, policy, commit=False):
        pass


class _DeviceGroupHierarchy(object):
    """Basically a doubly linked-list to create the device group hierarchy
    """

    class Node(object):
        def __init__(self):
            self.device_group = None
            self.parent = None
            self.children = []
            self.objects = {
                'services': [],
                'service_groups': [],
                'applications': [],
                'addresses': [],
                'address_groups': [],
                'pre_rulebase': [],
                'post_rulebase': []
            }

        @staticmethod
        def find(node, name, cls, include_sister_namespace=True, recursive=True):
            # this filter will either return an empty list or a single member list
            obj = filter(lambda x: (isinstance(x, cls) and x.name == name),
                         list(itertools.chain.from_iterable(node.objects.values())))
            if obj:
                # the object was found
                obj = obj[0]
            elif include_sister_namespace:
                try:
                    # switch namespaces if a sister namespace exists, otherwise do nothing
                    cls = PaloAltoBaseDriver.NamespaceSisterTypes[cls]
                    obj = _DeviceGroupHierarchy.Node.find(node, name, cls, include_sister_namespace=False)
                except KeyError:
                    pass  # ignore, we wont find the object this way anyway
                if not obj and recursive:
                    if node.parent:
                        # recurse up to the parent dg node
                        obj = _DeviceGroupHierarchy.Node.find(node.parent, name, cls)

            if not obj:
                # the object is not in this node
                return None
            return obj

    def __init__(self, panorama_obj, xml_hierarchy):

        self.lookup = {}
        self.root = _DeviceGroupHierarchy.Node()
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
            node = _DeviceGroupHierarchy.Node()
            node.device_group = self.panorama_obj.find(dg.attrib['name'], panorama.DeviceGroup)
            node.parent = parent
            parent.children.append(node)
            self.lookup[node.device_group.name] = node
            for child in dg:
                self._parse_nodes(child, node)

    def get_node(self, device_group_name):
        return self.lookup.get(device_group_name)

    def get_all_nodes(self):
        return self.lookup.values()
