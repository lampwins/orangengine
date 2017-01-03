import orangengine

from getpass import getpass


user = raw_input("Username: ")
password = getpass()

srx = {
    'device_type': 'juniper_srx',
    'ip': '192.168.187.5',
    'username': user,
    'password': password,
}

device = orangengine.dispatch(**srx)


t = {
    'source_zones': ['campus'],
    'destination_zones': ['eDMZ'],
    'source_addresses': ['10.169.1.0/24', '153.9.88.91/32'],
    'destination_addresses': ['10.7.130.253/32'],
    'action': 'permit'
}

candidate_policy = device.policy_match(t, match_containing_networks=True, exact=False)

for p in candidate_policy:
    print p.name
