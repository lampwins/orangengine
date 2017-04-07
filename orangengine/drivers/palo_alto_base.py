
from orangengine.drivers import BaseDriver
from orangengine.utils import bidict
from orangengine.models.paloalto import PaloAltoAddress
from orangengine.models.paloalto import PaloAltoAddressGroup
from orangengine.models.paloalto import PaloAltoService
from orangengine.models.paloalto import PaloAltoServiceGroup
from orangengine.models.paloalto import PaloAltoApplication
from orangengine.models.paloalto import PaloAltoApplicationGroup

import abc

from pandevice.base import PanDevice

import pyparsing as pp


class PaloAltoBaseDriver(BaseDriver):
    """Palo Alto Base class
    """

    ALLOWED_POLICY_KEYS = (
        'source_zones',
        'destination_zones',
        'source_addresses',
        'destination_addresses',
        'services',
        'action',
        'logging',
        'applications',
    )

    # in a given namespace there may be two related object types
    # here we map those together with a bidict
    NamespaceSisterTypes = bidict({
        PaloAltoAddress: PaloAltoAddressGroup,
        PaloAltoService: PaloAltoServiceGroup,
        PaloAltoApplication: PaloAltoApplicationGroup,
    })

    def open_connection(self, username, password, host, **kwargs):
        """
        We need additional information for this driver
        """
        # create a pan device object
        self.device = PanDevice.create_from_device(host, api_username=username, api_password=password,
                                                   api_key=kwargs.get('apikey'))

        self._connected = True

    @staticmethod
    def tag_delta(expression, tag_list):
        """Take in a tag expression and a list of tags and give the delta of tags to meet the expression

        :return tuple( list( "required tags" ),  list( "tuple of options" ) )
        """

        required_tags = []
        optional_tags = []

        def parse_and(tokens):
            args = tokens[0][0::2]
            extend_list = filter(lambda x: isinstance(x, str) and x not in tag_list, args)
            required_tags.extend(extend_list)

        def parse_or(tokens):
            args = tokens[0][0::2]
            append_list = filter(lambda x: isinstance(x, str) and x not in tag_list, args)
            if append_list == args:
                optional_tags.append(tuple(append_list))

        identifier = pp.Word(pp.alphanums + "_" + "-" + "'")

        expr = pp.infixNotation(identifier, [
            ("AND", 2, pp.opAssoc.LEFT, parse_and),
            ("OR", 2, pp.opAssoc.LEFT, parse_or),
            ("and", 2, pp.opAssoc.LEFT, parse_and),
            ("or", 2, pp.opAssoc.LEFT, parse_or),
        ])

        expr.parseString(expression)

        return required_tags, optional_tags

    @abc.abstractmethod
    def _get_config(self):

        # base and predefined refresh, this may take some time
        self.device.refresh()
        self.device.predefined.refreshall()

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

    @abc.abstractmethod
    def _parse_applications(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def _parse_application_groups(self):
        raise NotImplementedError()
