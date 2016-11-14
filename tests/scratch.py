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

#for a in device.address_name_lookup.values():
#    print a.name
#
#print "start groups"
#
#for a in device.address_group_name_lookup.values():
#    print a.name
#
#print "end groups"
#
#print "start services"
#
#for s in device.service_name_lookup.values():
#    if len(s.terms) > 0:
#        for t in s.terms:
#            print s.name, t.name, t.protocol, t.port
#    else:
#        print s.name, s.protocol, s.port
#
#print "end services"
#
#print "start service groups"
#
#for g in device.service_group_name_lookup.values():
#    print g.name
#
#print "end service groups"
#

#for p in device.policy_name_lookup.values():
#    print p.name
#    print "\tsrc zones:"
#    for z in p.src_zones:
#        print "\t\t" + z
#    print "\tsrc addrs:"
#    for a in p.src_addresses:
#        print "\t\t" + a.name
#    print "\tdst zones:"
#    for z in p.dst_zones:
#        print "\t\t" + z
#    print "\tdst addrs:"
#    for a in p.dst_addresses:
#        print "\t\t" + a.name
#    print "\tservices:"
#    for s in p.services:
#        print "\t\t" + s.name
#


# (self.src_zones, self.dst_zones, s_addrs, d_addrs, services, self.action)

t = {
    'source_zones': ['trust'],
    'destination_zones': ['untrust'],
    'source_addresses': ['153.9.243.220/32'],
    'destination_addresses': ['10.7.66.90/32'],
    'services': [('tcp', '22'), ('tcp', '3283'), ('tcp', '5900')],
    'action': 'permit'
}

policies = device.policy_recommendation_match(**t)

if policies:
    for p in policies[0]:
        print p.name














