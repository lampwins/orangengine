# -*- coding: utf-8 -*-
from orangengine.drivers import BaseDriver
from orangengine.utils import bidict
from orangengine.models.paloalto import PaloAltoAddress
from orangengine.models.paloalto import PaloAltoAddressGroup
from orangengine.models.paloalto import PaloAltoService
from orangengine.models.paloalto import PaloAltoServiceGroup
from orangengine.models.paloalto import PaloAltoApplication
from orangengine.models.paloalto import PaloAltoApplicationGroup
from orangengine.models.paloalto import PaloAltoPolicy

import abc

from pandevice.base import PanDevice

import pyparsing as pp


class PaloAltoBaseDriver(BaseDriver):
    """Palo Alto Base class
    """

    PolicyClass = PaloAltoPolicy

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

        if tag_list is None:
            tag_list = []

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

        if expression and not required_tags and expression not in tag_list:
            # single tag in the expression
            required_tags.append(expression)

        return required_tags, optional_tags

    @staticmethod
    def _apply_object(_panobject, pandevice_object):
        """Apply (destructive) the given pandevice_object on the given pandevice
        """
        _panobject.add(pandevice_object)
        pandevice_object.apply()

    @staticmethod
    def _create_object(_panobject, pandevice_object):
        """Create (non-destructive) the given pandevice_object on the given pandevice
        """
        _panobject.add(pandevice_object)
        pandevice_object.create()

    @staticmethod
    def _link_policy_objects(pandevice_policy, objs, string_values):
        """Link the objects to the policy
        """

        def _transform(l, v):
            transformed_value = l
            if v != 'any':
                # temporary fix until fixed in pandevice
                if l == ['any']:
                    l = 'any'
                if isinstance(l, str):
                    if l == 'any':
                        transformed_value = []
                    else:
                        transformed_value = [l]
                    transformed_value.append(v)
                elif v not in l:
                    transformed_value.append(v)
            else:
                transformed_value = v
            return transformed_value

        for key, value in objs.iteritems():
            for obj in value.values():
                if key == 'source_addresses':
                    pandevice_policy.source = _transform(pandevice_policy.source, obj.name)
                elif key == 'destination_addresses':
                    pandevice_policy.destination = _transform(pandevice_policy.destination, obj.name)
                elif key == 'applications':
                    pandevice_policy.application = _transform(pandevice_policy.application, obj.name)
                elif key == 'services':
                    pandevice_policy.service = _transform(pandevice_policy.service, obj.name)

        for key, value in string_values.iteritems():
            if isinstance(value, list):
                # these keys are guaranteed to ne list values
                for lv in value:
                    if key == 'source_zones':
                        pandevice_policy.fromzone = _transform(pandevice_policy.fromzone, lv)
                    elif key == 'destination_zones':
                        pandevice_policy.tozone = _transform(pandevice_policy.tozone, lv)
            elif key == 'action':
                pandevice_policy.action = value
            elif key == 'name':
                pandevice_policy.name = value
            elif key == 'description':
                pandevice_policy.description = pandevice_policy.description + '\n' + value
            elif key == 'logging':
                if value == 'start' or value == 'both':
                    pandevice_policy.log_start = True
                if value == 'end' or value == 'both':
                    pandevice_policy.log_end = True

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
    def apply_candidate_policy(self, candidate_policy, commit=False):
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
