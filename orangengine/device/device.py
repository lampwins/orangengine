
from multi_key_dict import multi_key_dict
from drivers import *


class Device(object):

    def __init__(self, driver):
        """init device"""

        self.driver = driver

        self.addresses = list()
        self.address_groups = list()
        self.services = list()
        self.service_groups = list()
        self.policies = list()

        self.address_lookup = multi_key_dict()

        self.driver.get_device()
