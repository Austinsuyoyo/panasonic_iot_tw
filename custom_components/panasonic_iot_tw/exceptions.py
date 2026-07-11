"""自定義異常類別"""

class PanasonicBaseException(Exception):
    """Panasonic 基礎異常類別"""
    pass

class PanasonicDeviceOffline(PanasonicBaseException):
    """設備離線異常"""
    pass

class PanasonicExceedRateLimit(PanasonicBaseException):
    """超過 API 調用頻率限制"""
    pass

class PanasonicTokenExpired(PanasonicBaseException):
    """Token 過期異常"""
    pass

class PanasonicLoginFailed(PanasonicBaseException):
    """登入失敗異常"""
    pass

class PanasonicAPIError(PanasonicBaseException):
    """API 錯誤異常"""
    pass

class PanasonicAuthError(PanasonicBaseException):
    """認證錯誤異常"""
    pass

class PanasonicDeviceNotFound(PanasonicBaseException):
    """設備未找到異常"""
    pass

class PanasonicInvalidCommand(PanasonicBaseException):
    """無效命令異常"""
    pass

class PanasonicRefreshTokenNotFound(PanasonicBaseException):
    """Refresh Token 不存在異常"""
    pass