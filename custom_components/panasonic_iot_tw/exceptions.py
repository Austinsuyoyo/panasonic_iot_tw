"""Custom exception classes"""

class PanasonicBaseException(Exception):
    """Base class for all Panasonic integration errors."""
    pass

class PanasonicDeviceOffline(PanasonicBaseException):
    """Raised when the appliance is offline."""
    pass

class PanasonicExceedRateLimit(PanasonicBaseException):
    """Raised when the API call rate limit is exceeded."""
    pass

class PanasonicTokenExpired(PanasonicBaseException):
    """Raised when the token has expired."""
    pass

class PanasonicLoginFailed(PanasonicBaseException):
    """Raised when login fails."""
    pass

class PanasonicAPIError(PanasonicBaseException):
    """Raised on a generic API error."""
    pass

class PanasonicAuthError(PanasonicBaseException):
    """Raised on an authentication error."""
    pass

class PanasonicDeviceNotFound(PanasonicBaseException):
    """Raised when the device is not found."""
    pass

class PanasonicInvalidCommand(PanasonicBaseException):
    """Raised on an invalid command."""
    pass

class PanasonicRefreshTokenNotFound(PanasonicBaseException):
    """Raised when the refresh token does not exist."""
    pass
