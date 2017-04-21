# -*- coding: utf-8 -*-
from orangengine.utils import enum, bidict
from orangengine.models.base import BaseObject


class BaseAddress(BaseObject):

    AddressTypes = enum('IPv4', 'DNS', 'RANGE', 'ANY')
    TypeMap = bidict({
        AddressTypes.IPv4: 'ipv4',
        AddressTypes.DNS: 'dns',
        AddressTypes.RANGE: 'range',
        AddressTypes.ANY: 'any',
    })

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

        return cls(criteria['name'], criteria['value'], cls.TypeMap[criteria['type']])

    def serialize(self):
        """Searialize self to a json acceptable data structure
        """
        return {
            'name': self.name,
            'type': self.TypeMap[self.a_type],
            'value': self.value,
        }
