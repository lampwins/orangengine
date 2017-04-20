# -*- coding: utf-8 -*-
import json


class BaseObject(object):
    """Base class for all (most) objects. This class should almost never be
    instantiated directly. It contains a few methods that are the available to
    all sub classes.
    """

    def serialize(self):
        raise NotImplementedError()

    def to_json(self):
        """Return a json dump of self returned from self.serialize()
        """
        return json.dumps(self.serialize())
