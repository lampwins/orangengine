# -*- coding: utf-8 -*-
from orangengine.models.base import BaseObject


class BaseServiceGroup(BaseObject):

    def __init__(self, name):
        """init a service group"""

        self.name = name
        self.elements = list()

    def add(self, service):
        """add a service"""

        self.elements.append(service)

    def __getattr__(self, item):
        """
        yield the values of the underlying objects
        """

        if item == 'value':
            return [s.value for s in self.elements]
        else:
            raise AttributeError

    def table_value(self, with_names):
        value = "Group: " + self.name + "\n"
        for s in self.elements:
            value = value + "   " + s.table_value(with_names) + "\n"
        return value.rstrip('\n')  # remove the last new line

    def serialize(self):
        """Searialize self to a json acceptable data structure
        """

        elements = []
        for e in self.elements:
            elements.append(e.serialize())

        return {
            'name': self.name,
            'elements': elements
        }