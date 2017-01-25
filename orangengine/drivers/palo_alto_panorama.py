
from orangengine.drivers.base import BaseDriver
from orangengine.models.paloalto import PaloAltoPolicy
from orangengine.models.paloalto import PaloAltoAddress
from orangengine.models import Address as GenericAddress

from pandevice import base
from pandevice import panorama
from pandevice import policies
from pandevice import objects
from pandevice import firewall


class PaloAltoPanoramaDriver(BaseDriver):

    # TODO shared and dev-group object namespaces are independent (meaning the same name can exist in both)
    # this means that before a policy change is enacted, we must verify the existence of an object or create
    # it within the given namespace, as an assumption is made in the matching stage that may not always hold
    # true. Please remember this later... it took a while to figure this out the first time John...
    # when doing a lookup, start with the local context and go up the tree

    def __init__(self, *args, **kwargs):
        """
        We need additional information for this driver
        """
        # create a panorama object
        self.pano = panorama.Panorama(kwargs['ip'], kwargs['username'], kwargs['password'])

        self.dev_group = None
        self.dev_group_post_rulebase = None
        self.dev_group_pre_rulebase = None
        self.pano_post_rulebase = None
        self.pano_pre_rulebase = None

        # now call the super
        super(PaloAltoPanoramaDriver, self).__init__(*args, **kwargs)

    def get_address_with_context(self, name, context=None):
        """
        because we have both shared and dev-group namespaces, we must intelligently search these namespaces
        """
        if context is None:
            # default to shared namespace
            context = self.pano

        address = context.find(name, objects.AddressObject)
        if address is None:
            address = context(name, objects.AddressGroup)
        if address is None and context is not self.pano:
            return self.get_address_with_context(name, self.pano)
        return address

    def open_connection(self, *args, **kwargs):

        # now pull down the config
        self.pano.refresh()

        # link our dev-group object
        self.dev_group = self.pano.find(kwargs['device-group'], panorama.DeviceGroup)

    def get_policies(self):
        # dev-group rulebases
        self.dev_group_post_rulebase = self.dev_group.find_or_create(None, policies.PostRulebase)
        self.dev_group_pre_rulebase = self.dev_group.find_or_create(None, policies.PreRulebase)

        # panorama rule bases
        self.pano_post_rulebase = self.pano.find_or_create(None, policies.PostRulebase)
        self.pano_pre_rulebase = self.pano.find_or_create(None, policies.PreRulebase)

        # aggregate of all actual rules
        rules = []
        rules.extend(self.dev_group_post_rulebase.findall(policies.SecurityRule))
        rules.extend(self.dev_group_pre_rulebase.findall(policies.SecurityRule))
        rules.extend(self.pano_post_rulebase.findall(policies.SecurityRule))
        rules.extend(self.pano_pre_rulebase.findall(policies.SecurityRule))

        #for rule in rules:
        #    policy = PaloAltoPolicy(rule)
        #    for a in
        #
        #    self.policies.append(rule)

    def get_addresses(self):

        # address objects
        addresses = []
        addresses.extend(self.pano.findall(objects.AddressObject))
        addresses.extend(self.dev_group.findall(objects.AddressObject))

        for address in addresses:
            a_obj = PaloAltoAddress(address)
            self.address_name_lookup[a_obj.name] = a_obj
            self.address_value_lookup[a_obj.value].append(a_obj)

        # special case: manually create "any" address
        any_address = GenericAddress("any", "any", 1)
        self.address_name_lookup['any'] = any_address
        self.address_value_lookup['any'].append(any_address)

    def get_services(self):

        # service objects
        services = []
        services.extend(self.pano.findall(objects.AddressObject))
        services.extend(self.dev_group.findall(objects.AddressObject))

        for service in services:
            s_obj = PaloAltoAddress(service)
            self.service_name_lookup[s_obj.name] = s_obj
            self.service_value_lookup[s_obj.value].append(s_obj)

        # special case: manually create "any" service
        any_service = GenericAddress("any", "any", 1)
        self.service_name_lookup['any'] = any_service
        self.service_value_lookup['any'].append(any_service)

        # special case: manually create "application-default" service
        any_service = GenericAddress("application-default", "application-default", 1)
        self.service_name_lookup['application-default'] = any_service
        self.service_value_lookup['application-default'].append(any_service)








