
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

    def __getattr__(self, item):

        if item == 'value':
            return self.value
        else:
            raise AttributeError

    def table_value(self, with_names):
        if with_names:
            return self.name + " - " + self.value
        else:
            return self.value
