
class BasePortRange(object):

    def __init__(self, start, stop):
        """init a port range"""

        self.start = start
        self.stop = stop

    def __str__(self):
        return '{0} {1}'.format(self.start, self.stop)

    def __getattr__(self, item):

        if item == 'value':
            return self.start + "-" + self.stop
        else:
            raise AttributeError


class BaseServiceTerm(object):

    def __init__(self, name, protocol, port=None):
        """init service term object"""

        self.name = name
        self.protocol = protocol if protocol else "unknown"
        self.port = port if port else "unknown"

    def __getattr__(self, item):

        if item == 'value':
            if isinstance(self.port, BasePortRange):
                return self.protocol, self.port.value
            else:
                return self.protocol, self.port
        else:
            raise AttributeError


class BaseService(object):

    def __init__(self, name, protocol=None, port=None):
        """init a service"""

        self.name = name
        self.protocol = protocol if protocol else "unknown"
        if port is not None and '-' in port:
            start = port.split('-')[0]
            stop = port.split('-')[1]
            if start != stop:
                self.port = BasePortRange(start, stop)
            else:
                self.port = start
        else:
            self.port = port if port else "unknown"
        self.terms = list()

    def add_term(self, term):
        """append a service term"""

        self.terms.append(term)

    def __getattr__(self, item):

        if item == 'value':
            if len(self.terms) > 0:
                return [t.value for t in self.terms]
            elif isinstance(self.port, BasePortRange):
                return self.protocol, self.port.value
            else:
                return self.protocol, self.port
        else:
            raise AttributeError

    def table_value(self, with_names):
        if with_names:
            return self.name + " - " + self.value[0] + "/" + self.value[1]
        else:
            if isinstance(self.value, list):
                return "\n".join([s[0] + "/" + s[1] for s in self.value])
            return self.value[0] + "/" + self.value[1]

    @classmethod
    def from_criteria(cls, criteria):
        """Create an instance from the provided criteria
        """

        return cls(criteria['name'], criteria['protocol'], criteria['port'])

