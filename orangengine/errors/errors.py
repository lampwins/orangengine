# -*- coding: utf-8 -*-
class ShadowedPolicyError(Exception):
    """
    This exception gets raised when a policy recommendation is requested for a shadowed policy
    """

    def __init__(self, message='Policy is shadowed'):
        # Call the base class constructor with the parameters it needs
        super(Exception, self).__init__(message)


class DuplicatePolicyError(Exception):
    """
    This exception is raised when a policy recommendation is requested and it is determined to me a duplicate
    """

    def __init__(self, message='Policy is a duplicate'):
        # Call the base class constructor with the parameters it needs
        super(Exception, self).__init__(message)


class ConnectionError(Exception):
    """
    This exception is raised when a an underlying connection error is raised or a check on connection state fails
    """

    def __init__(self, message='Connection error'):
        # Call the base class constructor with the parameters it needs
        super(Exception, self).__init__(message)


class BadCandidatePolicyError(Exception):
    """
    This exception is raised when a candidate policy does not meet the requirements to become a policy
    """

    def __init__(self, message='Candidate policy does not meet requirements'):
        # Call the base class constructor with the parameters it needs
        super(Exception, self).__init__(message)


class PolicyImplementationError(Exception):
    """
    This exception is raised when there is a fatal error preventing a policy from being applied/modified on a device
    """

    def __init__(self, message='There is a error preventing this policy from being applied'):
        # Call the base class constructor with the parameters it needs
        super(Exception, self).__init__(message)
