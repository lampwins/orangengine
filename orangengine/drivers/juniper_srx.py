# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from lxml import etree as letree

from orangengine.drivers import BaseDriver
from orangengine.models.base import BasePortRange, BaseServiceTerm
from orangengine.models.juniper import JuniperSRXAddress
from orangengine.models.juniper import JuniperSRXAddressGroup
from orangengine.models.juniper import JuniperSRXService
from orangengine.models.juniper import JuniperSRXServiceGroup
from orangengine.models import CandidatePolicy
from orangengine.models.juniper import JuniperSRXPolicy
from orangengine.errors import ConnectionError
from orangengine.errors import BadCandidatePolicyError
from orangengine.errors import PolicyImplementationError
from _juniper_utils import build_base, create_element, build_zone_pair, create_new_address, create_new_service

from jnpr.junos import Device
from jnpr.junos.utils.config import Config


# TODO refactor comments
class JuniperSRXDriver(BaseDriver):

    PolicyClass = JuniperSRXPolicy

    def apply_policy(self, policy, commit=False):
        pass

    def apply_candidate_policy(self, candidate_policy, merge=True):
        """
        resolve the candidate policy and apply it to the device
        default method is to merge the generated config but 'replace' is used for deletions
        """

        def get_or_create_address_element(address):
            a_obj = self.get_address_object_by_value(address)
            if a_obj is None:
                # need to create a new one
                address_book_element, address_book_element_name = create_new_address(address)
                # transparently append the new entry to the list
                address_book.append(address_book_element)
                return address_book_element_name
            else:
                return a_obj.name

        def get_or_create_service_element(service):
            s_obj = self.get_service_object_by_value(service)
            if s_obj is None:
                # need to create a new one
                service_book_element, service_book_element_name = create_new_service(service)
                # transparently append the new entry to the list
                service_book.append(service_book_element)
                return service_book_element_name
            else:
                return s_obj.name

        def build_policy(name, s_addresses, d_addresses, services, action, logging):
            # base elements
            sub_policy_element = create_element('policy')
            create_element('name', text=name, parent=sub_policy_element)
            p_match_element = create_element('match', parent=sub_policy_element)

            # address elements
            for a_type in [s_addresses, d_addresses]:
                for _a in a_type:
                    __a_type = 'source-address' if a_type is s_addresses else 'destination-address'
                    create_element(__a_type, text=get_or_create_address_element(_a), parent=p_match_element)

            # service elements
            for _s in services:
                create_element('application', text=get_or_create_service_element(_s), parent=p_match_element)

            # action and logging
            then_element = create_element('then', parent=sub_policy_element)
            create_element(action, parent=then_element)
            log_element = create_element('log', parent=then_element)
            create_element(logging, parent=log_element)

            return sub_policy_element

        # 1 - resolve zones - TODO is this really needed or can we enforce this as a requirement?
        # 2 - check all elements present (can actually build the policy)
        # 3 - build policy
        # 4 - apply and commit

        if not self._connected:
            raise ConnectionError("Device connection is not open")

        c_policy = candidate_policy.policy

        configuration = build_base()
        address_book = []
        service_book = []

        if candidate_policy.method is CandidatePolicy.NEW_POLICY:
            # this will be a new policy

            # check if we have a valid new policy
            if c_policy.src_zones is None or c_policy.dst_zones is None or c_policy.src_addresses is None \
                    or c_policy.dst_addresses is None or c_policy.services is None or c_policy.action is None \
                    or c_policy.name is None:
                # missing elements
                raise BadCandidatePolicyError()

            policy_element = build_policy(c_policy.name, c_policy.src_addresses, c_policy.dst_addresses,
                                          c_policy.services, c_policy.action, c_policy.logging)
        else:
            # we are adding new element(s) to an existing policy

            # base elements
            policy_element = create_element('policy')
            create_element('name', text=c_policy.name, parent=policy_element)
            match_element = create_element('match', parent=policy_element)

            # TODO currently only address and service additions are supported
            for k, v in candidate_policy.target_dict.iteritems():
                if k == 'source-addresses' or k == 'destination-address':
                    for a in v:
                        _a_type = 'source-address' if k is 'source-addresses' else 'destination-address'
                        create_element(_a_type, text=get_or_create_address_element(a), parent=match_element)
                elif k == 'services':
                    for s in v:
                        create_element('application', text=get_or_create_service_element(s), parent=match_element)
                else:
                    raise PolicyImplementationError('Currently only address and service additions are supported.')

        # put the tree together
        for s_zone in c_policy.src_zones:
            for d_zone in c_policy.dst_zones:
                # security policy section
                zone_pair_element = build_zone_pair(s_zone, d_zone)
                zone_pair_element.append(policy_element)
                configuration[0][0].append(zone_pair_element)
                # services
                if service_book:
                    config_service_element = letree.Element('applications')
                    for s_el in service_book:
                        config_service_element.append(s_el)
                    configuration.append(config_service_element)
                # addresses
                if address_book:
                    config_address_book_element = letree.Element('address-book')
                    global_book_element = letree.SubElement(config_address_book_element, 'name')
                    global_book_element.text = 'global'
                    for a_el in address_book:
                        config_address_book_element.append(a_el)
                    # append within the security element
                    configuration[0].append(config_address_book_element)

        # load the config and commit
        # this is done with a private session, meaning if there are uncommitted
        # changes on the box, this load will fail
        # print letree.tostring(configuration, pretty_print=True)
        with Config(self.device, mode='private') as cu:
            cu.load(configuration, format='xml', merge=merge)
            cu.pdiff()
            cu.commit()
        # print letree.tostring(configuration, pretty_print=True)

    def open_connection(self, username, password, host, **additional_params):
        """
        open the device connection
        """

        # TODO handle connection exceptions correctly
        self.device = Device(host=host, user=username, passwd=password)
        self.device.open()
        self._connected = True

    def _get_config(self):
        """
        get the config from the device and store it
        """
        # TODO: fix this xml library conversion nonsense
        # get config sections

        # TODO: needs xml refactoring
        self.config_output['policies'] = ET.fromstring(letree.tostring(self.device.rpc.get_config(
            filter_xml=letree.XML('<configuration><security><policies></policies></security></configuration>'))))[0][0]

        # TODO: needs xml refactoring
        self.config_output['address_book'] = ET.fromstring(letree.tostring(self.device.rpc.get_config(
            filter_xml=letree.XML(
                '<configuration><security><address-book><global /></address-book></security></configuration>'))))[0][0]

        # TODO: needs xml refactoring
        self.config_output['output_junos_default'] = ET.fromstring(letree.tostring(self.device.rpc.get_config(
            filter_xml=letree.XML(
                '<configuration><groups><name>junos-defaults</name><applications></applications></groups></configuration>'))))[
            0].find('applications')

        # TODO: needs xml refactoring
        self.config_output['output_applications'] = ET.fromstring(letree.tostring(self.device.rpc.get_config(
            filter_xml=letree.XML('<configuration><applications></applications></configuration>'))))[0]

    def _parse_addresses(self):
        """
        retrieve and parse the address objects
        """

        # rpc-reply > configuration > security > address-book
        addresses = self.config_output['address_book']

        for e_address in addresses.findall('address'):
            name = value = a_type = None
            for e in list(e_address):
                if e.tag == 'name':
                    name = e.text
                elif e.tag == 'ip-prefix':
                    value = e.text
                    a_type = JuniperSRXAddress.AddressTypes.IPv4
                elif e.tag == 'dns-name':
                    value = e.find('name').text
                    a_type = JuniperSRXAddress.AddressTypes.DNS
                else:
                    pass

            address = JuniperSRXAddress(name, value, a_type)
            self.address_name_lookup[name] = address
            self.address_value_lookup[value].append(address)

        # special case: manually create "any" address
        any_address = JuniperSRXAddress("any", "any", 1)
        self.address_name_lookup['any'] = any_address
        self.address_value_lookup['any'].append(any_address)

    def _parse_address_groups(self):
        """
        retrieve and parse the address-set objects
        """

        # rpc-reply > configuration > security > address-book
        address_sets = self.config_output['address_book']

        for e_address_set in address_sets.findall('address-set'):
            name = e_address_set.find('name').text
            address_set = JuniperSRXAddressGroup(name)
            value_lookup_list = []
            for e in e_address_set.findall('address'):
                a = e.find('name').text
                a_obj = self._address_lookup_by_name(a)
                address_set.add(a_obj)
                value_lookup_list.append(a_obj)
                # self.address_group_value_lookup[a].append(address_set)

            # set the address value lookup to the value of all addresses in the group
            # self.address_value_lookup[[a.value for a in value_lookup_list]].append(address_set)

            # set he address group name lookup
            self.address_group_name_lookup[name] = address_set

    def _parse_services(self):
        """
        retrieve and parse services. Both junos-default and user defined applications.

        also handles term based services
        """

        for applications in [self.config_output['output_junos_default'], self.config_output['output_applications']]:
            for e_application in applications.findall('application'):
                s_name = e_application.find('name').text
                if s_name == 'any':
                    # special case: manually build the any object
                    any_service = JuniperSRXService(s_name, 'any', 'any')
                    self.service_value_lookup[('any', 'any')].append(any_service)
                    self.service_name_lookup[s_name] = any_service
                    continue
                port = None
                if e_application.find('term') is not None:
                    # term based application
                    service = JuniperSRXService(s_name)
                    value_lookup_list = []
                    for e_term in e_application.findall('term'):
                        t_name = e_term.find('name').text
                        protocol = e_term.find('protocol').text
                        if protocol == 'icmp':
                            icmp_type = icmp_code = 'unknown'
                            if e_term.find('icmp-type') is not None:
                                icmp_type = e_term.find('icmp-type').text
                            if e_term.find('icmp-code') is not None:
                                icmp_code = e_term.find('icmp-code').text
                            port = ",".join([icmp_type, icmp_code])
                        elif e_term.find('destination-port') is not None:
                            port = e_term.find('destination-port').text
                        term = BaseServiceTerm(t_name, protocol, port)
                        service.add_term(term)
                        if isinstance(port, BasePortRange):
                            # reset the port value to insert into the lookup dictionary
                            port = port.value
                        value_lookup_list.append((protocol, port))
                    # set the lookup value to the list of all actual services
                    # self.service_value_lookup[value_lookup_list].append(service)
                else:
                    # regular application
                    protocol = e_application.find('protocol').text
                    if protocol == 'icmp':
                        icmp_type = icmp_code = 'unknown'
                        if e_term.find('icmp-type') is not None:
                            icmp_type = e_term.find('icmp-type').text
                        if e_term.find('icmp-code') is not None:
                            icmp_code = e_term.find('icmp-code').text
                        port = ",".join([icmp_type, icmp_code])
                    if e_application.find('destination-port') is not None:
                        port = e_application.find('destination-port').text
                    service = JuniperSRXService(s_name, protocol, port)
                    self.service_value_lookup[(protocol, port)].append(service)

                self.service_name_lookup[s_name] = service

    def _parse_service_groups(self):
        """
        retrieve and parse service groups (includes junos-defaults and user defined applications)
        """

        # rpc-reply > configuration > applications
        for application_sets in [self.config_output['output_junos_default'], self.config_output['output_applications']]:
            for e_service_set in application_sets.findall('application-set'):
                name = e_service_set.find('name').text
                service_group = JuniperSRXServiceGroup(name)
                value_lookup_list = []
                for e_application in e_service_set.findall('application'):
                    s = e_application.find('name').text
                    s_obj = self._service_lookup_by_name(s)
                    service_group.add(s_obj)
                    value_lookup_list.append(s_obj)
                    # self.service_group_value_lookup[a].append(service_group)

                # set the service object lookup value to the value of all containing services
                # self.service_value_lookup[[s.value for s in value_lookup_list]].append(service_group)

                # service group name lookup
                self.service_group_name_lookup[name] = service_group

    def _parse_policies(self):
        """
        retrieve and parse polices
        """

        for e_zone_set in list(self.config_output['policies']):
            if e_zone_set.tag == 'policy':
                # regular policy zone set
                from_zone = e_zone_set.find('from-zone-name').text
                to_zone = e_zone_set.find('to-zone-name').text
            elif e_zone_set.tag == 'global':
                # global policies
                from_zone = to_zone = 'global'
            else:
                # not a policy type element
                continue
            action = None
            logging = []
            for e_policy in e_zone_set.findall('policy'):
                name = e_policy.find('name').text
                description = e_policy.find('description')
                if description is not None:
                    description = description.text
                for e_then in list(e_policy.find('then')):
                    if e_then.tag in ['permit', 'deny', 'reject']:
                        action = JuniperSRXPolicy.ActionMap[e_then.tag]
                    elif e_then.tag == 'log':
                        for e_log in e_then:
                            logging.append(JuniperSRXPolicy.LoggingMap[e_log.tag])
                    else:
                        # currently unsupported element
                        pass
                policy = JuniperSRXPolicy(name, action, description, logging)
                policy.add_src_zone(from_zone)
                policy.add_dst_zone(to_zone)
                e_match = e_policy.find('match')
                for e_type in ['source-address', 'destination-address', 'application']:
                    for e in e_match.findall(e_type):
                        if e_type == 'source-address':
                            policy.add_src_address(self.get_address_object_by_name(e.text))
                        elif e_type == 'destination-address':
                            policy.add_dst_address(self.get_address_object_by_name(e.text))
                        elif e_type == 'application':
                            policy.add_service(self.get_service_object_by_name(e.text))

                self._add_policy(policy)

    def _parse_applications(self):
        # we don't do applications for SRX
        pass

    def _parse_application_groups(self):
        # we don't do application groups for SRX
        pass
