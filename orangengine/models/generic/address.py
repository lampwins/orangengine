
"""address object constants"""
ADDRESS_TYPES = {
    'ipv4': 1,
    'dns': 2,
}


class Address(object):

    def __init__(self, name, value, a_type):
        """init address object"""

        self.name = name
        self.value = value
        self.a_type = a_type
