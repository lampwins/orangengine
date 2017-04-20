# -*- coding: utf-8 -*-
from orangengine.dispatcher import dispatch
from orangengine import utils

import logging


__all__ = ['dispatch', 'utils']


# Set default logging handler to avoid "No handler found" warnings.
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
