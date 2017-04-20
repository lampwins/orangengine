# -*- coding: utf-8 -*-
from lxml import etree as letree
from orangengine.utils import is_ipv4


"""
juniper driver specific utility functions
"""


# --- begin xml generation functions


def create_new_address(a_value):
    if isinstance(a_value, list):
        raise ValueError("Creating new address groups is not currently supported")
    address_element = create_element('address')
    if is_ipv4(a_value):
        # ip
        # TODO figure out naming convention
        name_element_text = 'oe-address-{0}'.format(a_value.split('/')[0])
        name_element = create_element('name', text=name_element_text, parent=address_element)
        create_element('ip-prefix', text=a_value, parent=address_element)
    else:
        # dns
        # TODO figure out naming convention
        name_element_text = 'oe-fqdn-{0}'.format(a_value)
        name_element = create_element('name', text=name_element_text, parent=address_element)
        dns_element = create_element('dns-name', parent=address_element)
        create_element('name', text=a_value, parent=dns_element)
    return address_element, name_element.text


def create_new_service(s_value):
    if isinstance(s_value, list):
        raise ValueError("Creating new service groups/termed services is not currently supported")
    service_element = create_element('application')
    # TODO figure out naming convention
    name_element_text = 'oe-service-{0}-{1}'.format(s_value[0], s_value[1])
    name_element = create_element('name', text=name_element_text, parent=service_element)
    create_element('protocol', text=s_value[0], parent=service_element)
    create_element('source-port', text='1-65535', parent=service_element)
    create_element('destination-port', text=s_value[1], parent=service_element)
    return service_element, name_element.text


def build_base():
    configuration_element = create_element('configuration')
    security_element = create_element('security', parent=configuration_element)
    create_element('policies', parent=security_element)
    return configuration_element


def build_zone_pair(from_zone_name, to_zone_name):
    zone_pair_policy = create_element('policy')
    create_element('from-zone-name', text=from_zone_name, parent=zone_pair_policy)
    create_element('to-zone-name', text=to_zone_name, parent=zone_pair_policy)
    return zone_pair_policy


def create_element(tag, text=None, parent=None):
    # create an ambiguous element
    if parent is not None:
        e = letree.SubElement(parent, tag)
    else:
        e = letree.Element(tag)
    if text:
        e.text = text
    return e

# --- end xml generation functions
