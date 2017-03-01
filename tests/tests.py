
from orangengine.models import Policy, Address

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


if __name__ == '__main__':
    unittest.main()
