
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


class ConnectionError(Exception):
    """
    This exception is raised when a an underlying connection error is raised or a check on connection state fails
    """

    def __init__(self, msg='Connection error'):
        self.message = msg


class BadCandidatePolicyError(Exception):
    """
    This exception is raised when a candidate policy does not meet the requirements to become a policy
    """

    def __init__(self, msg='Candidate policy does not meet requirements'):
        self.message = msg