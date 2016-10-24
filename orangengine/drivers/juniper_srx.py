
from drivers import generic


class JuniperSRX(generic.GenericDriver):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.get_device()

    def get_device(self):
        pass













"""devel"""

import netmiko
import xml.etree.ElementTree as ET

device = {
    'device_type': 'juniper',
    'ip': '',
    'username': '',
    'password': '',
}


SSHClass = netmiko.ssh_dispatcher(device_type=device['device_type'])
device_conn = SSHClass(**device)
output = device_conn.send_command('show configuration security policies | display xml')

print output.strip()

# rpc-reply > configuration > security > policies
policies = ET.fromstring(output.strip())[0][0][0]

print policies

for zone_set in policies.findall('policy'):

    from_zone = zone_set.find('from-zone-name').text
    to_zone = zone_set.find('to-zone-name').text

    for policy in zone_set.findall('policy'):