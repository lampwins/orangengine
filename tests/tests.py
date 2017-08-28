# -*- coding: utf-8 -*-
from orangengine.models.base import BasePolicy
from orangengine.models.base import BaseAddress
from orangengine.models.base import BaseServiceTerm
from orangengine.models.base import BasePortRange

from orangengine.models.juniper import JuniperSRXPolicy
from orangengine.models.juniper import JuniperSRXAddress
from orangengine.models.juniper import JuniperSRXAddressGroup
from orangengine.models.juniper import JuniperSRXService
from orangengine.models.juniper import JuniperSRXServiceGroup

from orangengine.models.paloalto import PaloAltoPolicy
from orangengine.models.paloalto import PaloAltoApplication
from orangengine.models.paloalto import PaloAltoApplicationGroup
from orangengine.models.paloalto import PaloAltoAddress
from orangengine.models.paloalto import PaloAltoAddressGroup
from orangengine.models.paloalto import PaloAltoService
from orangengine.models.paloalto import PaloAltoServiceGroup

import unittest


class TestPolicyAddressMatching(unittest.TestCase):

    def setUp(self):
        self.policy = BasePolicy(name='test', action='perrmit', description='', logging='both')
        self.policy.add_src_address(
            BaseAddress(name='test-src-address', value='1.1.1.1/32', a_type=1))
        self.policy.add_dst_address(
            BaseAddress(name='test-dst-address', value='2.2.2.2/32', a_type=1))

    def test_source_address_matching(self):
        self.assertEqual(self.policy.match({'source_addresses': ['1.1.1.1/32']}), True)

    def test_destination_address_matching(self):
        self.assertEqual(self.policy.match({'destination_addresses': ['2.2.2.2/32']}), True)


class TestJuniperSRXModelsToXML(unittest.TestCase):

    def setUp(self):
        # address and address groups
        self.ipv4_address = JuniperSRXAddress(name='test-ipv4-address', value='1.1.1.1/32',
                                              a_type=BaseAddress.AddressTypes.IPv4)
        self.dns_address = JuniperSRXAddress(name='test-dns-address', value='www.example.com',
                                             a_type=BaseAddress.AddressTypes.DNS)
        self.address_group = JuniperSRXAddressGroup(name='test-address-group')
        self.address_group.add(self.ipv4_address)
        self.address_group.add(self.dns_address)

        # service and service groups
        self.regular_service = JuniperSRXService('regular-service', protocol='udp', port='666')
        self.term_service = JuniperSRXService('regular-service')
        self.term_service.add_term(BaseServiceTerm('term1', 'tcp', '666'))
        self.term_service.add_term(BaseServiceTerm('term2', 'udp', BasePortRange('300', '400')))
        self.port_range_service = JuniperSRXService('regular-service', protocol='udp', port='666-667')
        self.servicegroup = JuniperSRXServiceGroup('test-group')
        self.servicegroup.add(self.regular_service)
        self.servicegroup.add(self.term_service)
        self.servicegroup.add(self.port_range_service)

    def test_ipv4_address_to_xml(self):
        element = self.ipv4_address.to_xml()
        self.assertEquals(element.find('name').text, 'test-ipv4-address')
        self.assertEquals(element.find('ip-prefix').text, '1.1.1.1/32')

    def test_dns_address_to_xml(self):
        element = self.dns_address.to_xml()
        self.assertEquals(element.find('name').text, 'test-dns-address')
        self.assertEquals(element.find('dns-name').find('name').text, 'www.example.com')

    def test_address_group_to_xml(self):
        element = self.address_group.to_xml()
        self.assertEqual(element.find('name').text, 'test-address-group')
        addresses = [e.find('name').text for e in element.findall('address')]
        self.assertIn('test-ipv4-address', addresses)
        self.assertIn('test-dns-address', addresses)

    def test_service_to_xml(self):
        # regular service
        element = self.regular_service.to_xml()
        self.assertEqual(element.find('name').text, 'regular-service')
        self.assertEqual(element.find('protocol').text, 'udp')
        self.assertEqual(element.find('destination-port').text, '666')

        # term service
        element = self.term_service.to_xml()
        self.assertEqual(len(element.findall('term')), 2)

        # port range service
        element = self.port_range_service.to_xml()
        self.assertEqual(element.find('destination-port').text, '666-667')

    def test_service_group_to_xml(self):
        element = self.servicegroup.to_xml()
        self.assertEqual(element.find('name').text, 'test-group')
        self.assertEqual(len(element.findall('application')), 3)


if __name__ == '__main__':
    unittest.main()
