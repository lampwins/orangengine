
from orangengine.models import Address, AddressGroup, Service, ServiceGroup, Policy, ADDRESS_TYPES

from lxml import etree as letree


def create_element(tag, text=None, parent=None):
    # create an ambiguous element
    if parent is not None:
        e = letree.SubElement(parent, tag)
    else:
        e = letree.Element(tag)
    if text:
        e.text = text
    return e


class AddressMapper(object):
    """
    Map address objects to juniper SRX config tree elements
    """

    @staticmethod
    def map(obj):

        if not isinstance(obj, Address):
            raise ValueError("Object must be an Address, passed {0}".format(type(obj)))

        address_element = create_element('address')
        create_element('name', text=obj.name, parent=address_element)
        if obj.a_type == ADDRESS_TYPES['ipv4']:
            # ipv4
            create_element('ip-prefix', text=obj.value, parent=address_element)
        else:
            # dns
            dns_element = create_element('dns-name', parent=address_element)
            create_element('name', text=obj.value, parent=dns_element)

        return address_element


class AddressGroupMapper(object):
    """
    Map address group objects to juniper SRX config tree elements
    """

    @staticmethod
    def map(obj):

        if not isinstance(obj, AddressGroup):
            raise ValueError("Object must be an AddressGroup, passed {0}".format(type(obj)))

        addressgroup_element = create_element('address-set')
        create_element('name', text=obj.name, parent=addressgroup_element)

        for a in obj.elements:
            if isinstance(a, Address):
                address_element = create_element('address', parent=addressgroup_element)
            else:
                address_element = create_element('address-set', parent=addressgroup_element)
            create_element('name', text=a.name, parent=address_element)

        return addressgroup_element
