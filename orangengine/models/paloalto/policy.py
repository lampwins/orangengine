
from orangengine.models.base import BasePolicy
from orangengine.utils import bidict


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

        super(PaloAltoPolicy, self).__init__(name=pandevice_object.name, action=pandevice_object.action,
                                             description=pandevice_object.description, logging=logging)
