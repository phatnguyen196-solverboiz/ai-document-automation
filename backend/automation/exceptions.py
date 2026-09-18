class PortalAutomationError(Exception):
    pass


class PortalTimeoutError(PortalAutomationError):
    pass


class PortalFormError(PortalAutomationError):
    pass


class PortalUnavailableError(PortalAutomationError):
    pass
