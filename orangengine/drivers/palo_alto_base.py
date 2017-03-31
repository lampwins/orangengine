
from orangengine.drivers import BaseDriver
from orangengine.utils import bidict
from orangengine.models.paloalto import PaloAltoAddress
from orangengine.models.paloalto import PaloAltoAddressGroup
from orangengine.models.paloalto import PaloAltoService
from orangengine.models.paloalto import PaloAltoServiceGroup

import abc

from pandevice.base import PanDevice


class PaloAltoBaseDriver(BaseDriver):
    """Palo Alto Base class
    """

    # in a given namespace there may be two related object types
    # here we map those together with a bidict
    NamespaceSisterTypes = bidict({
        PaloAltoAddress: PaloAltoAddressGroup,
        PaloAltoService: PaloAltoServiceGroup
    })

    def open_connection(self, username, password, host, **kwargs):
        """
        We need additional information for this driver
        """
        # create a pan device object
        self.device = PanDevice.create_from_device(host, api_username=username, api_password=password,
                                                   api_key=kwargs.get('apikey'))

        self._connected = True

    @abc.abstractmethod
    def _get_config(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_addresses(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_address_groups(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_services(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_service_groups(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_policies(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def apply_candidate_policy(self, candidate_policy):
        raise NotImplementedError()

    @abc.abstractmethod
    def apply_policy(self, policy, commit=False):
        raise NotImplementedError()
