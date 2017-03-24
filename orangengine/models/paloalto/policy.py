
from orangengine.models.base import BasePolicy as GenericPolicy


class PaloAltoPolicy(GenericPolicy):

    def __init__(self, pandevice_object=None):

        # this is the actual object provided by the 'pandevice' library
        self.pandevice_object = pandevice_object

        if pandevice_object.log_start and pandevice_object.log_end:
            logging = 'both'
        elif pandevice_object.log_start:
            logging = 'session-start'
        else:
            logging = 'session-end'

        super(PaloAltoPolicy, self).__init__(name=pandevice_object.name,
                                             action=pandevice_object.action,
                                             logging=logging,
                                             description=pandevice_object.description)




