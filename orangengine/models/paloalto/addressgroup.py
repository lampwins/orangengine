# -*- coding: utf-8 -*-
from orangengine.models.base import BaseAddressGroup


class PaloAltoAddressGroup(BaseAddressGroup):
    """Palo Alto Address Group

    Inherits from BaseAddressGroup and provides access to the underlying pandevice object
    """

    def __init__(self, pandevice_object):

        self.pandevice_object = pandevice_object
        self.dynamic_value = None

        super(PaloAltoAddressGroup, self).__init__(name=pandevice_object.name)
