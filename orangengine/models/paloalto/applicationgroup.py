
class PaloAltoApplicationGroup(object):
    """Palo Alto Application Group

    Covers pandevice ApplicationGroups and ApplicationContainers.
    """

    def __init__(self, pandevice_object):

        self.pandevice_object = pandevice_object
        self.name = self.pandevice_object.name
        self.elements = []

    def add(self, obj):
        self.elements.append(obj)

    def __getattr__(self, item):
        """
        yield the values of the underlying objects
        """

        if item == 'value':
            return [a.value for a in self.elements]
        else:
            raise AttributeError

    def table_value(self):
        value = "Group: " + self.name + "\n"
        for a in self.elements:
            value = value + "   " + a.table_value() + "\n"
        return value.rstrip('\n')  # remove the last new line
