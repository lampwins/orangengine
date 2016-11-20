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
    'source_zones': ['trust'],
    'destination_zones': ['untrust'],
    'source_addresses': ['153.9.243.220/32'],
    'destination_addresses': ['10.7.66.90/32'],
    'services': [('tcp', '22'), ('tcp', '3283'), ('tcp', '5900')],
    'action': 'permit'
}

candidate_policy = device.policy_candidate_match(**t)

candidate_policy.set_name('test-policy')
device.apply_candidate_policy(candidate_policy)















