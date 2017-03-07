
from orangengine.models import Policy, Address, AddressGroup
from orangengine.mappers.juniper_srx import AddressMapper as JAM, AddressGroupMapper as JAGM

import unittest


class TestPolicyAddressMatching(unittest.TestCase):

    def setUp(self):
        self.policy = Policy(name='test', action='perrmit', logging='both', description='')
        self.policy.add_src_address(Address(a_type=1, name='test-src-address', value='1.1.1.1/32'))
        self.policy.add_dst_address(Address(a_type=1, name='test-dst-address', value='2.2.2.2/32'))

    def test_source_address_matching(self):
        self.assertEqual(self.policy.match({'source_addresses': ['1.1.1.1/32']}), True)

    def test_destination_address_matching(self):
        self.assertEqual(self.policy.match({'destination_addresses': ['2.2.2.2/32']}), True)


class TestJuniperSRXMappers(unittest.TestCase):

    def setUp(self):
        self.ipv4_address = Address(a_type=1, name='test-ipv4-address', value='1.1.1.1/32')
        self.dns_address = Address(a_type=2, name='test-dns-address', value='www.example.com')
        self.address_group = AddressGroup(name='test-address-group')
        self.address_group.add(self.ipv4_address)
        self.address_group.add(self.dns_address)

    def test_ipv4_address_mapper(self):
        element = JAM.map(self.ipv4_address)
        self.assertEquals(element.find('name').text, 'test-ipv4-address')
        self.assertEquals(element.find('ip-prefix').text, '1.1.1.1/32')

    def test_dns_address_mapper(self):
        element = JAM.map(self.dns_address)
        self.assertEquals(element.find('name').text, 'test-dns-address')
        self.assertEquals(element.find('dns-name').find('name').text, 'www.example.com')

    def test_address_group_mapper(self):
        element = JAGM.map(self.address_group)
        self.assertEqual(element.find('name').text, 'test-address-group')
        addresses = [e.find('name').text for e in element.findall('address')]
        self.assertIn('test-ipv4-address', addresses)
        self.assertIn('test-dns-address', addresses)


if __name__ == '__main__':
    unittest.main()
