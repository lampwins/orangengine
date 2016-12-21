import orangengine

from getpass import getpass


user = raw_input("Username: ")
password = getpass()

srx = {
    'device_type': 'juniper_srx',
    'ip': '153.9.252.240',
    'username': user,
    'password': password,
}

device = orangengine.dispatch(**srx)


t = {
    'source_zones': ['untrust'],
    'destination_zones': ['untrust'],
    'source_addresses': ['10.10.10.10/32'],
    'destination_addresses': ['153.9.252.252/32'],
    'services': [('tcp', '80')],
    'action': 'permit'
}

candidate_policy = device.policy_candidate_match(t)

candidate_policy.set_name('the-new-policy')

device.apply_candidate_policy(candidate_policy)

for p in candidate_policy:
    print p.name














