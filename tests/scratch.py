import orangengine

from getpass import getpass


user = raw_input("Username: ")
password = getpass()

srx = {
    'device_type': 'palo_alto_panorama',
    'host': '153.9.252.248',
    'username': user,
    'password': password,
}

device = orangengine.dispatch(**srx)
device.refresh()


t = {
    'source_addresses': ['any'],
    'destination_addresses': ['any'],
    'action': 'allow',
}

c_policy = device.candidate_policy_match(t, device_group='lab2')
a = c_policy.to_json()
print a

b = device.candidate_policy_from_json(a)
print b.to_json()

print c_policy.to_json()
