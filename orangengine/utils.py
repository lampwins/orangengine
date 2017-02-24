"""
utility functions
"""

from netaddr import IPNetwork, IPAddress, IPRange

__all__ = ['is_ipv4']


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
        return the address with '/32' appended. Else return the
        value passed in.
    """
    if is_ipv4(address) and '/' not in address:
        return address + '/32'
    return address
