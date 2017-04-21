# -*- coding: utf-8 -*-
from orangengine.models.base import BasePolicy
from orangengine.utils import bidict, flatten

from pandevice import policies


class PaloAltoPolicy(BasePolicy):

    ActionMap = bidict({
        BasePolicy.Action.ALLOW: 'allow',
        BasePolicy.Action.DROP: 'drop',
        BasePolicy.Action.DENY: 'deny'
    })

    def __init__(self, pandevice_object=None):

        # this is the actual object provided by the 'pandevice' library
        self.pandevice_object = pandevice_object

        logging = []
        if pandevice_object.log_start:
            logging.append(BasePolicy.Logging.START)
        if pandevice_object.log_end:
            logging.append(BasePolicy.Logging.END)

        self._applications = []

        super(PaloAltoPolicy, self).__init__(name=pandevice_object.name, action=self.ActionMap[pandevice_object.action],
                                             description=pandevice_object.description, logging=logging)

    def add_application(self, app):
        self._applications.append(app)

    def serialize(self):
        """Searialize self to a json acceptable data structure
        """

        # we need only update the super with local applications

        super_dict = super(PaloAltoPolicy, self).serialize()
        super_dict.update({
            'applications': list(map(lambda x: x.serialize(), self._applications))
        })

        return super_dict

    def __getattr__(self, item):
        """add applications access or call super"""

        if item == 'applications':
            return set(flatten([a.value for a in self._applications]))
        else:
            return super(PaloAltoPolicy, self).__getattr__(item)

    @staticmethod
    def table_service_cell(services, with_names=False):
        """handle the application-default case"""
        if services[0].name == "application-default":
            return "application-default\n"
        else:
            return super(PaloAltoPolicy, PaloAltoPolicy).table_service_cell(services, with_names=with_names)

    def table_application_cell(self):
        return "\n".join([a.table_value() for a in self._applications]) + '\n'

    def table_header(self):
        """Return the table header for the policy
        """
        return ["Src Zones", "Src Addresses", "Dst Zones", "Dst Addresses", "Applications", "Services", "Action"]

    def table_row(self, with_names=False):
        """Return the table row for the based policy
        """
        s_zones = self.table_zone_cell(self.src_zones)
        d_zones = self.table_zone_cell(self.dst_zones)
        s_addresses = self.table_address_cell(self.src_addresses, with_names)
        d_addresses = self.table_address_cell(self.dst_addresses, with_names)
        services = self.table_service_cell(self._services, with_names)
        applications = self.table_application_cell()

        return [s_zones, s_addresses, d_zones, d_addresses, applications, services, self.ActionMap[self.action]]

    @classmethod
    def from_criteria(cls, criteria):
        """Create an instance from the provided criteria
        """

        logging_criteria = criteria.get('logging', [])

        pandevice_object = policies.SecurityRule()
        pandevice_object.name = criteria['name']
        pandevice_object.description = criteria.get('description', '')
        pandevice_object.action = criteria['action']  # we expect it to be human readable at this point, map it later

        if 'start' in logging_criteria or 'both' in logging_criteria:
            pandevice_object.log_start = True
        if 'end' in logging_criteria or 'both' in logging_criteria:
            pandevice_object.log_end = True

        return cls(pandevice_object)
