
class BaseAddressGroup(object):

    def __init__(self, name):
        """init a address group object"""

        self.name = name
        self.elements = list()

    def add(self, address):
        """add an address(group) object to the elements list"""

        self.elements.append(address)

    def __getattr__(self, item):
        """
        yeild the values of the underlying objects
        """
        if item == 'value':
            return [a.value for a in self.elements]
        else:
            raise AttributeError

    def table_value(self, with_names):
        value = "Group: " + self.name + "\n"
        for a in self.elements:
            value = value + "   " + a.table_value(with_names) + "\n"
        return value.rstrip('\n')  # remove the last new line
