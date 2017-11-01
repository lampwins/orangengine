import orangengine

from getpass import getpass


user = raw_input("Username: ")
password = getpass()

srx = {
    'device_type': '',
    'host': '',
    'username': user,
    'password': password,
}

device = orangengine.dispatch(**srx)
device.refresh()

print device.effective_policy('', match_containing_networks=False).to_table()
