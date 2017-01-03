from lxml import etree as letree
from orangengine.utils import is_ipv4


"""
juniper driver specific utility functions
"""


# --- begin xml generation functions


def create_new_address(value):
    if isinstance(value, list):
        raise ValueError("Creating new address groups is not currently supported")
    address_element = letree.Element('address')
    name_element = letree.SubElement(address_element, 'name')
    if is_ipv4(value):
        # ip
        # TODO figure out naming convention
        name_element.text = 'oe-address-{0}'.format(value.split('/')[0])
        value_element = letree.SubElement(address_element, 'ip-prefix')
    else:
        # dns
        # TODO figure out naming convention
        name_element.text = 'oe-fqdn-{0}'.format(value)
        dns_element = letree.SubElement(address_element, 'dns-name')
        value_element = letree.SubElement(dns_element, 'name')
    value_element.text = value
    return address_element, name_element.text


def create_new_service(value):
    if isinstance(value, list):
        raise ValueError("Creating new service groups/termed services is not currently supported")
    service_element = letree.Element('application')
    name_element = letree.SubElement(service_element, 'name')
    # TODO figure out naming convention
    name_element.text = 'oe-service-{0}-{1}'.format(value[0], value[1])
    protocol_element = letree.SubElement(service_element, 'protocol')
    protocol_element.text = value[0]
    source_port_element = letree.SubElement(service_element, 'source-port')
    source_port_element.text = '1-65535'
    destination_port_element = letree.SubElement(service_element, 'destination-port')
    destination_port_element.text = value[1]
    return service_element, name_element.text


def build_base():
    configuration_element = letree.Element('configuration')
    security_element = letree.SubElement(configuration_element, 'security')
    security_element.append(letree.Element('policies'))
    return configuration_element


def build_zone_pair(from_zone_name, to_zone_name):
    zone_pair_policy = letree.Element('policy')
    from_zone = letree.SubElement(zone_pair_policy, 'from-zone-name')
    from_zone.text = from_zone_name
    to_zone = letree.SubElement(zone_pair_policy, 'to-zone-name')
    to_zone.text = to_zone_name
    return zone_pair_policy


# --- end xml generation functions
