# -*- coding: utf-8 -*-
from orangengine.models.base import BaseServiceGroup


class PaloAltoServiceGroup(BaseServiceGroup):
    """Palo Alto ServiceGroup

    Inherits from BaseServiceGRoup and provides access to the underlying pandevice object
    """

    def __init__(self, pandevice_object):

        self.pandevice_object = pandevice_object

        super(PaloAltoServiceGroup, self).__init__(name=pandevice_object.name)
