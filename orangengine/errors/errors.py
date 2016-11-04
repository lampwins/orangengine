
class ShadowedPolicyError(Exception):
    """
    This exception gets raised when a policy recommendation is requested for a shadowed policy
    """

    def __init__(self, msg='Policy is shadowed'):
        self.message = msg


class DuplicatePolicyError(Exception):
    """
    This exception is raised when a policy recommendation is requested and it is determined to me a duplicate
    """

    def __init__(self, msg='Policy is a duplicate'):
        self.message = msg
