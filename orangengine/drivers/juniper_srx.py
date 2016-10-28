
import xml.etree.ElementTree as ET

from orangengine.drivers import BaseDriver
from orangengine.models import Address
from orangengine.models import AddressGroup
from orangengine.models import ADDRESS_TYPES
from orangengine.models import Service
from orangengine.models import ServiceTerm
from orangengine.models import PortRange
from orangengine.models import ServiceGroup
from orangengine.models import Policy


class JuniperSRXDriver(BaseDriver):

    def get_addresses(self):
        """
        retrieve and parse the address objects
        """

        self.config_output['address_book'] = ET.fromstring(self.device_conn.send_command(
            'show configuration security address-book global | display xml').strip())[0][0][0]

        # rpc-reply > configuration > security > address-book
        addresses = self.config_output['address_book']

        for e_address in addresses.findall('address'):
            name = value = a_type = None
            for e in list(e_address):
                if e.tag == 'name':
                    name = e.text
                elif e.tag == 'ip-prefix':
                    value = e.text
                    a_type = ADDRESS_TYPES['ipv4']
                elif e.tag == 'dns-name':
                    value = e.find('name').text
                    a_type = ADDRESS_TYPES['dns']
                else:
                    pass

            address = Address(name, value, a_type)
            self.address_name_lookup[name] = address
            self.address_value_lookup[value].append(address)

        # special case: manually create "any" address
        any_address = Address("any", "any", 1)
        self.address_name_lookup['any'] = any_address
        self.address_value_lookup['any'].append(any_address)

    def get_address_groups(self):
        """
        retrieve and parse the address-set objects
        """

        # rpc-reply > configuration > security > address-book
        address_sets = self.config_output['address_book']

        for e_address_set in address_sets.findall('address-set'):
            name = e_address_set.find('name').text
            address_set = AddressGroup(name)
            for e in e_address_set.findall('address'):
                a = e.find('name').text
                address_set.add(self._address_lookup_by_name(a))
                self.address_group_value_lookup[a].append(address_set)

            self.address_group_name_lookup[name] = address_set

    def get_services(self):
        """
        retrieve and parse services. Both junos-default and user defined applications.

        also handles term based services
        """

        # rpc-reply > configuration > groups > applications
        self.config_output['output_junos_default'] = ET.fromstring(self.device_conn.send_command(
            'show configuration groups junos-defaults applications | display xml').strip())[0][0].find(
            'applications')

        # rpc-reply > configuration > applications
        self.config_output['output_applications'] = ET.fromstring(self.device_conn.send_command(
            'show configuration applications | display xml').strip())[0][0]

        for applications in [self.config_output['output_junos_default'], self.config_output['output_applications']]:
            for e_application in applications.findall('application'):
                s_name = e_application.find('name').text
                port = None
                if e_application.find('term') is not None:
                    # term based application
                    service = Service(s_name)
                    for e_term in e_application.findall('term'):
                        t_name = e_term.find('name').text
                        protocol = e_term.find('protocol').text
                        if e_term.find('destination-port') is not None:
                            port = e_term.find('destination-port').text
                            if '-' in port:
                                port = PortRange(port.split('-')[0], port.split('-')[1])
                        term = ServiceTerm(t_name, protocol, port)
                        service.add_term(term)
                        self.service_value_lookup[(protocol, port)].append(service)
                else:
                    # regular applications
                    protocol = e_application.find('protocol').text
                    if e_application.find('destination-port') is not None:
                        port = e_application.find('destination-port').text
                        if '-' in port:
                            port = PortRange(port.split('-')[0], port.split('-')[1])
                    service = Service(s_name, protocol, port)
                    self.service_value_lookup[(protocol, port)].append(service)

                self.service_name_lookup[s_name] = service

    def get_service_groups(self):
        """
        retrieve and parse service groups (includes junos-defaults and user defined applications)
        """

        # rpc-reply > configuration > applications
        for application_sets in [self.config_output['output_junos_default'], self.config_output['output_applications']]:
            for e_service_set in application_sets.findall('application-set'):
                name = e_service_set.find('name').text
                service_group = ServiceGroup(name)
                for e_application in e_service_set.findall('application'):
                    a = e_application.find('name').text
                    service_group.add(self._service_lookup_by_name(a))
                    self.service_group_value_lookup[a].append(service_group)

                self.service_group_name_lookup[name] = service_group

    def get_polices(self):
        """
        retrieve and parse polices
        """

        output = self.device_conn.send_command('show configuration security policies | display xml')

        # rpc-reply > configuration > security > policies
        policies = ET.fromstring(output.strip())[0][0][0]

        for e_zone_set in policies.findall('policy'):
            from_zone = e_zone_set.find('from-zone-name').text
            to_zone = e_zone_set.find('to-zone-name').text
            action = logging = None
            for e_policy in e_zone_set.findall('policy'):
                name = e_policy.find('name').text
                description = e_policy.find('description')
                if description is not None:
                    description = description.text
                for e_then in list(e_policy.find('then')):
                    if e_then.tag in ['permit', 'deny', 'reject']:
                        action = e_then.tag
                    elif e_then.tag == 'log':
                        logging = e_then[0].tag
                    else:
                        # unhandled element
                        pass
                policy = Policy(name, action, description, logging)
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
