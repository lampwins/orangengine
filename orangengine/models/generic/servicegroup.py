
class ServiceGroup(object):

    def __init__(self, name):
        """init a service group"""

        self.name = name
        self.elements = list()

    def add(self, service):
        """add a service"""

        self.elements.append(service)

    def __getattr__(self, item):
        """
        yield the values of the underlying objects
        """

        if item == 'value':
            return [s.value for s in self.elements]
        else:
            raise AttributeError
