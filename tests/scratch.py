import orangengine

srx = {
    'device_type': 'juniper_srx',
    'ip': '192.168.187.5',
    'username': '',
    'password': '',
}

device = orangengine.dispatch(**srx)

for a in device.address_name_lookup.values():
    print a.name

print "start groups"

for a in device.address_group_name_lookup.values():
    print a.name

print "end groups"

print "start services"

for s in device.service_name_lookup.values():
    if len(s.terms) > 0:
        for t in s.terms:
            print s.name, t.name, t.protocol, t.port
    else:
        print s.name, s.protocol, s.port

print "end services"

print "start service groups"

for g in device.service_group_name_lookup.values():
    print g.name

print "end service groups"
