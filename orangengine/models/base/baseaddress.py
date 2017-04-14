
from orangengine.utils import enum


class BaseAddress(object):

    AddressTypes = enum('IPv4', 'DNS', 'RANGE', 'ANY')

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

    @classmethod
    def from_criteria(cls, criteria):
        """Create an instance from the provided criteria
        """

        return cls(criteria['name'], criteria['value'], criteria['a_type'])
