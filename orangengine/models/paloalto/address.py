
from orangengine.models import Address as GenericAddress, ADDRESS_TYPES


class PaloAltoAddress(GenericAddress):

    def __init__(self, pandevice_object):

        self.pandevice_object = pandevice_object

        super(PaloAltoAddress, self).__init__(name=pandevice_object.name,
                                              value=pandevice_object.value,
                                              a_type=ADDRESS_TYPES['dns'] if pandevice_object.type is 'fqdn'
                                              else ADDRESS_TYPES['ipv4'])
