# -*- coding: utf-8 -*-
from orangengine.models.base import BasePolicy
from orangengine.utils import create_element, bidict


class JuniperSRXPolicy(BasePolicy):
    """Juniper SRX Policy

    Inherits from Base Policy
    """

    ActionMap = bidict({
        BasePolicy.Action.ALLOW: 'permit',
        BasePolicy.Action.DENY: 'deny',
        BasePolicy.Action.REJECT: 'reject',
    })

    LoggingMap = bidict({
        BasePolicy.Logging.START: 'session-init',
        BasePolicy.Logging.END: 'session-close',
    })

    def __init__(self, name, action, description, logging):

        super(JuniperSRXPolicy, self).__init__(name, action, description, logging)

    def to_xml(self):
        """Map Juniper SRX Policy Object into xml config element
        """

        policy_element = create_element('policy')
        create_element('name', text=self.name, parent=policy_element)
        match_element = create_element('match', parent=policy_element)
        for s in self.src_addresses:
            create_element('source-address', text=s.name, parent=match_element)
        for d in self.dst_addresses:
            create_element('destination-address', text=d.name, parent=match_element)
        then_element = create_element('then', parent=policy_element)
        create_element(JuniperSRXPolicy.ActionMap[self.action], parent=then_element)
        log_element = create_element('log', parent=then_element)
        for log_type in self.logging:
            create_element(JuniperSRXPolicy.LoggingMap[log_type], parent=log_element)

        return policy_element
