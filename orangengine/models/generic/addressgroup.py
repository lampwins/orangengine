
class AddressGroup(object):

    def __init__(self, name, elements=list()):
        """init a address group object"""

        self.name = name
        self.elements = elements

    def add(self, address):
        """add an address(group) object to the elements list"""

        self.elements.append(address)
