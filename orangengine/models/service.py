
class Service(object):

    def __init__(self, name, protocol, port, application=None):
        """init a service"""

        self.name = name
        self.protocol = protocol
        self.port = port
        self.application = application
