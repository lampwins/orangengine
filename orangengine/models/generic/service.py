
class PortRange(object):

    def __init__(self, start, stop):
        """init a port range"""

        self.start = start
        self.stop = stop

    def __str__(self):
        return '{0} {1}'.format(self.start, self.stop)


class ServiceTerm(object):

    def __init__(self, name, protocol, port=None):
        """init service term object"""

        self.name = name
        self.protocol = protocol
        self.port = port


class Service(object):

    def __init__(self, name, protocol=None, port=None, application=None):
        """init a service"""

        self.name = name
        self.protocol = protocol
        self.port = port
        self.application = application
        self.terms = list()

    def add_term(self, term):
        """append a service term"""

        self.terms.append(term)
