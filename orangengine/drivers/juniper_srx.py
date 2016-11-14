
import xml.etree.ElementTree as ET
from lxml import etree as letree

from orangengine.drivers import BaseDriver
from orangengine.models import Address
from orangengine.models import AddressGroup
from orangengine.models import ADDRESS_TYPES
from orangengine.models import Service
from orangengine.models import ServiceTerm
from orangengine.models import PortRange
from orangengine.models import ServiceGroup
from orangengine.models import Policy
from orangengine.errors import ConnectionError
from orangengine.errors import BadCandidatePolicyError

from jnpr.junos import Device
from jnpr.junos.utils.config import Config


# TODO refactor comments
class JuniperSRXDriver(BaseDriver):

    def apply_candidate_policy(self, candidate_policy, merge=True):
        """
        resolve the candidate policy and apply it to the device
        default method is to merge the generated config but 'replace' is used for deletions
        """

        def build_base():
            return letree.Element('configuration').append(
                letree.Element('security').append(letree.Element('policies')))

        def build_zone_pair(from_zone_name, to_zone_name):
            zone_pair_policy = letree.Element('policy')
            from_zone = letree.SubElement(zone_pair_policy, 'from-zone-name')
            from_zone.text = from_zone_name
            to_zone = letree.SubElement(zone_pair_policy, 'to-zone-name')
            to_zone.text = to_zone_name
            return zone_pair_policy

        def build_policy(name, s_addresses, d_addresses, services, action, logging):
            sub_policy_element = letree.Element('policy')
            name_element = letree.SubElement(sub_policy_element, 'name')
            name_element.text = name
            match_element = letree.SubElement(sub_policy_element, 'match')
            for a_type in [s_addresses, d_addresses]:
                for a in a_type:
                    address_element = letree.SubElement(match_element, 'source-address' if a_type is s_addresses else 'destination-address')
                    address_element.text = a
            for s in services:
                service_element = letree.SubElement(match_element, 'application')
                service_element.text = s
            then_element = letree.SubElement(policy_element, 'then')
            then_element.append(letree.Element(action))
            log_element = letree.SubElement(then_element, 'log')
            log_element.append(letree.Element(logging))
            return policy_element

        # 1 - resolve zones
        # 2 - check all elements present (can actually build the policy)
        # 3 - build policy
        # 4 - apply and commit

        if not self._connected:
            raise ConnectionError(msg="Device connection is not open")

        c_policy = candidate_policy.policy

        if c_policy.src_zones is None or c_policy.dst_zones is None or c_policy.src_addresses is None \
           or c_policy.dst_addresses is None or c_policy.services is None or c_policy.action is None \
           or c_policy.name is None:

            # missing elements
            raise BadCandidatePolicyError()

        configuration = build_base()
        policy_element = build_policy(c_policy.name, c_policy.src_addresses, c_policy.dst_addresses,
                                      c_policy.services, c_policy.action, c_policy.logging)

        for s_zone in c_policy.src_zones:
            for d_zone in c_policy.dst_zones:
                configuration[0][0].append(build_zone_pair(s_zone, d_zone).append(policy_element))

        # load the config and commit
        # this is done with a private session
        with Config(self.device, mode='private') as cu:
            cu.load(configuration, format='xml', merge=merge)
            cu.pdiff()
            cu.commit()

    def open_connection(self, *args, **kwargs):
        """
        open the device connection
        """

        # TODO handle connection exceptions correctly
        self.device = Device(host=kwargs['ip'], user=kwargs['username'], passwd=kwargs['password'])
        self.device.open()
        self._connected = True

        # TODO: fix this xml library conversion nonsense
        # get config sections
        self.config_output['policies'] = ET.fromstring(letree.tostring(self.device.rpc.get_config(
            filter_xml=letree.XML('<configuration><security><policies></policies></security></configuration>'))))[0][0]

        self.config_output['address_book'] = ET.fromstring(letree.tostring(self.device.rpc.get_config(
            filter_xml=letree.XML('<configuration><security><address-book><global /></address-book></security></configuration>'))))[0][0]

        self.config_output['output_junos_default'] = ET.fromstring(letree.tostring(self.device.rpc.get_config(
            filter_xml=letree.XML('<configuration><groups><name>junos-defaults</name><applications></applications></groups></configuration>'))))[0].find('applications')

        self.config_output['output_applications'] = ET.fromstring(letree.tostring(self.device.rpc.get_config(
            filter_xml=letree.XML('<configuration><applications></applications></configuration>'))))[0]

    def get_addresses(self):
        """
        retrieve and parse the address objects
        """

        #self.config_output['address_book'] = ET.fromstring(self.device_conn.send_command(
        #    'show configuration security address-book global | display xml').strip())[0][0][0]

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
        #self.config_output['output_junos_default'] = ET.fromstring(self.device_conn.send_command(
        #    'show configuration groups junos-defaults applications | display xml').strip())[0][0].find(
        #    'applications')

        # rpc-reply > configuration > applications
        #self.config_output['output_applications'] = ET.fromstring(self.device_conn.send_command(
        #    'show configuration applications | display xml').strip())[0][0]

        for applications in [self.config_output['output_junos_default'], self.config_output['output_applications']]:
            for e_application in applications.findall('application'):
                s_name = e_application.find('name').text
                if s_name == 'any':
                    # special case: manually build the any object
                    any_service = Service(s_name, 'any', 'any')
                    self.service_value_lookup[('any', 'any')].append(any_service)
                    self.service_name_lookup[s_name] = any_service
                    continue
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
                                start = port.split('-')[0]
                                stop = port.split('-')[1]
                                if start != stop:
                                    port = PortRange(port.split('-')[0], port.split('-')[1])
                                else:
                                    port = start
                        term = ServiceTerm(t_name, protocol, port)
                        service.add_term(term)
                        self.service_value_lookup[(protocol, port)].append(service)
                else:
                    # regular applications
                    protocol = e_application.find('protocol').text
                    if e_application.find('destination-port') is not None:
                        port = e_application.find('destination-port').text
                        if '-' in port:
                            start = port.split('-')[0]
                            stop = port.split('-')[1]
                            if start != stop:
                                port = PortRange(port.split('-')[0], port.split('-')[1])
                            else:
                                port = start
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

    def get_policies(self):
        """
        retrieve and parse polices
        """

        #output = self.device_conn.send_command('show configuration security policies | display xml')

        # rpc-reply > configuration > security > policies
        #policies = ET.fromstring(output.strip())[0][0][0]

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
                        # currently unsupported element
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