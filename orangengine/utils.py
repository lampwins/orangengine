# -*- coding: utf-8 -*-
"""
utility functions
"""
from collections import Iterable

from netaddr import IPNetwork, IPAddress, IPRange
from lxml import etree as letree

__all__ = ['is_ipv4', 'missing_cidr', 'enum', 'create_element',
           'bidict', ]


def is_ipv4(value):
    """
    return true if value is any kind of ipv4 address.
    address, network, or range
    """
    try:
        if '-' in value:
            # try a range
            addr_range = value.split('-')
            IPRange(addr_range[0], addr_range[1])
        else:
            IPNetwork(value)
    except Exception:
        return False
    return True


def missing_cidr(address):
    """Missing CIDR

    :returns if the address passes in is ipv4 and missing cidr,
        and not a range, return the address with '/32' appended.
        Else return the value passed in.
    """
    if '-' not in address and is_ipv4(address) and '/' not in address:
        return address + '/32'
    return address


# Enumerator type
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


def create_element(tag, text=None, parent=None):
    # create an ambiguous xml element
    if parent is not None:
        e = letree.SubElement(parent, tag)
    else:
        e = letree.Element(tag)
    if text:
        e.text = text
    return e


class bidict(dict):
    """Bidirectional dictionary for two-way lookups

    Thanks to @Basj
    http://stackoverflow.com/questions/3318625/efficient-bidirectional-hash-table-in-python

    Extended to allow blind access to the inverse dict by way of __getitem__
    """
    def __init__(self, *args, **kwargs):
        super(bidict, self).__init__(*args, **kwargs)
        self.inverse = {}
        for key, value in self.iteritems():
            self.inverse.setdefault(value, []).append(key)

    def __setitem__(self, key, value):
        super(bidict, self).__setitem__(key, value)
        self.inverse.setdefault(value, []).append(key)

    def __delitem__(self, key):
        self.inverse.setdefault(self[key], []).remove(key)
        if self[key] in self.inverse and not self.inverse[self[key]]:
            del self.inverse[self[key]]
        super(bidict, self).__delitem__(key)

    def __getitem__(self, item):
        try:
            value = super(bidict, self).__getitem__(item)
        except KeyError:
            value = self.inverse[item]
            if value and len(value) == 1:
                value = value[0]
        return value


def flatten(l):
    """Generate a flatten list of elements from an n-depth nested list
    """
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, basestring) and not isinstance(el, tuple):
            for sub in flatten(el):
                yield sub
        else:
            yield el
