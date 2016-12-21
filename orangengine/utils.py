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
