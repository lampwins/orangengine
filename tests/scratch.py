import orangengine

from getpass import getpass


user = raw_input("Username: ")
password = getpass()

srx = {
    'device_type': 'juniper_srx',
    'ip': '',
    'username': user,
    'password': password,
}

device = orangengine.dispatch(**srx)


t = {
    'destination_addresses': [''],
    'action': 'permit',
}

c_policy = device.policy_match(t, match_containing_networks=False)
for p in c_policy:
    print p.table()
