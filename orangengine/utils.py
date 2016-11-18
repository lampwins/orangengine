"""
utility functions
"""

import ipaddress

__all__ = ['is_ipv4']


def is_ipv4(value):
    try:
        ipaddress.ip_network(value)
    except Exception:
        return False
    return True
