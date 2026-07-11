"""
API constants for Panasonic IoT TW integration.

This file contains all discovered API endpoints from APK analysis.
- 32 working endpoints verified through testing
- 1 deprecated endpoint removed (404 errors)
- HTTP method requirements documented
- Authentication requirements specified

Updated: 2025-10-03 - Restored DeviceSetCommand endpoint based on live testing.
"""

# API Configuration
BASE_URL = "https://ems2.panasonic.com.tw/api"
APP_TOKEN = "D8CBFF4C-2824-4342-B22D-189166FEF503"
USER_AGENT = "okhttp/4.9.1"

# Request Configuration - Simplified
MIN_SAFETY_DELAY = 2                  # Minimal delay between requests (seconds)
INIT_SAFETY_DELAY = 4                 # Longer delay only during initialization
REQUEST_TIMEOUT = 25                  # Individual request timeout
COMMANDS_PER_REQUEST = 6              # Max commands per batch request

# Rate Limiting Response
RATE_LIMIT_BACKOFF_BASE = 30          # Base delay when rate limited (seconds)
RATE_LIMIT_MAX_DELAY = 300            # Maximum backoff delay (5 minutes)

# API Endpoints
API_ENDPOINTS = {
    # === Core Authentication & Device Management ===
    "login": f"{BASE_URL}/userlogin1",
    "get_devices": f"{BASE_URL}/UserGetRegisteredGwList2",
    "get_device_info": f"{BASE_URL}/DeviceGetInfo",
    "set_command": f"{BASE_URL}/DeviceSetCommand",
    "get_info": f"{BASE_URL}/UserGetInfo",
    "get_device_overview": f"{BASE_URL}/UserGetDeviceStatus",
    "refresh_token": f"{BASE_URL}/RefreshToken1",
    
    # === Extended Device Management ===
    "get_device_flow_types": f"{BASE_URL}/DeviceGetFlowTypeList",
    "get_device_schedule": f"{BASE_URL}/DeviceGetSchedule",
    "get_device_setting": f"{BASE_URL}/DeviceGetSetting",
    "set_device_schedule": f"{BASE_URL}/DeviceSetSchedule",
    "set_device_setting": f"{BASE_URL}/DeviceSetSetting",
    "set_device_info": f"{BASE_URL}/DevicesetInfo",
    
    # === Gateway Management ===
    "gw_factory_reset": f"{BASE_URL}/GwFactoryReset",
    "gw_register1": f"{BASE_URL}/GwRegister1",
    "gw_register2": f"{BASE_URL}/GwRegister2",
    "gw_user_delete": f"{BASE_URL}/GwUserDelete",
    
    # === User Management ===
    "user_copy_gw_list": f"{BASE_URL}/UserCopyGwList",
    "user_get_gw_ip": f"{BASE_URL}/UserGetGWIP",
    "user_get_registered_gw_list1": f"{BASE_URL}/UserGetRegisteredGWList1",
    "user_set_onestep_commands": f"{BASE_URL}/UserSetOneStepCommands",
    "user_set_onestep_group": f"{BASE_URL}/UserSetOneStepGroup",
    "user_set_room": f"{BASE_URL}/UserSetRoom",
    # NOTE: SetRoom endpoint returns 404 - use user_set_room instead
    
    # === Appliance-Specific Features ===
    "wm_get_washing_history": f"{BASE_URL}/WMGetWashingHistory",
    "deh_user_setting": f"{BASE_URL}/DehUserSetting",
    "ref_user_setting": f"{BASE_URL}/RefUserSetting",
    "ref_get_food_ingredients": f"{BASE_URL}/RefGetFoodIngredients",
    
    # === System & Notification ===
    "get_app_edition": f"{BASE_URL}/GetAppEdition",
    "get_official_msg": f"{BASE_URL}/GetOfficialMsg",
    "locate_weather": f"{BASE_URL}/LocateWeather",
    "push_get_customize_msg": f"{BASE_URL}/PushGetCustomizeMsg",
    "push_token_update": f"{BASE_URL}/PushTokenUpdate",
}

# API Method Requirements
API_METHODS = {
    # GET endpoints
    "get_devices": "GET",
    "set_command": "GET",
    "get_device_overview": "GET",
    "user_get_registered_gw_list1": "GET",
    "gw_factory_reset": "GET",
    "ref_get_food_ingredients": "GET",
    "get_app_edition": "GET",
    "get_official_msg": "GET",
    # All other endpoints use POST method
}

# Deprecated/Removed Endpoints (404 Not Found after testing)
DEPRECATED_ENDPOINTS = {
    "set_room": f"{BASE_URL}/SetRoom",  # 404 - use user_set_room instead
}

# Exception Messages
EXCEPTION_MESSAGES = {
    "COMMAND_NOT_FOUND": "Unable to get command through CommandId",
    "DEVICE_OFFLINE": "deviceOffline",
    "DEVICE_NOT_RESPONDING": "deviceNoResponse",
    "DEVICE_JP_INFO": "503:DeviceJPInfo:aStatusCode",
    "DEVICE_JP_FAILED": ":DeviceJPInfo:GetCommandTransResult failed",
    "TOKEN_EXPIRED": "Unable to get related data based on your CPToken and auth",
    "INVALID_REFRESH_TOKEN": "Invalid RefreshToken",
    "CPTOKEN_EXPIRED": "This CPToken has expired",
    "REACH_RATE_LIMIT": "System detected your current excessive usage",
    "APP_TOKEN_ERROR": "AppToken Error",  # New error discovered in testing
}


