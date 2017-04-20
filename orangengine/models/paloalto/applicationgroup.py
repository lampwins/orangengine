# -*- coding: utf-8 -*-
from orangengine.models.base import BaseObject

from pandevice.objects import ApplicationContainer


class PaloAltoApplicationGroup(BaseObject):
    """Palo Alto Application Group

    Covers pandevice ApplicationGroups and ApplicationContainers.
    """

    def __init__(self, pandevice_object):

        self.pandevice_object = pandevice_object
        self.name = self.pandevice_object.name
        self.elements = []

    def add(self, obj):
        self.elements.append(obj)

    def __getattr__(self, item):
        """
        yield the values of the underlying objects
        """

        if item == 'value':
            if isinstance(self.pandevice_object, ApplicationContainer):
                # we treat app containers like regular apps for the purposes of their value
                return self.name
            else:
                return [a.value for a in self.elements]
        else:
            raise AttributeError

    def table_value(self):
        value = "Group: " + self.name + "\n"
        for a in self.elements:
            value = value + "   " + a.table_value() + "\n"
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
