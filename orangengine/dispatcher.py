# -*- coding: utf-8 -*-
from orangengine.drivers import JuniperSRXDriver
from orangengine.drivers import PaloAltoPanoramaDriver


DRIVER_MAPPINGS = {
    'juniper_srx': JuniperSRXDriver,
    'palo_alto_panorama': PaloAltoPanoramaDriver,
}

platforms = list(DRIVER_MAPPINGS.keys())


def dispatch(*args, **kwargs):
    """driver connection factory"""

    if kwargs['device_type'] not in platforms:
        raise ValueError('Platform is not currently supported.')

    Driver = DRIVER_MAPPINGS[kwargs['device_type']]
    return Driver(*args, **kwargs)
