# Panasonic IoT TW - Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](https://github.com/austinsuyoyo/panasonic_iot_tw/releases)
[![License](https://img.shields.io/github/license/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg?style=flat-square)](https://github.com/hacs/integration)

A comprehensive Home Assistant custom integration for controlling Panasonic smart appliances through the Panasonic IoT TW API. This integration features a modern architecture with factory pattern device management and comprehensive entity support.

## 🚀 Features

### Supported Devices

| Device Type | Entity Count | Supported Features |
|-------------|--------------|-------------------|
| **Air Conditioner** | 18+ entities | Temperature control, fan speed, modes, timers, nanoeX, ECONAVI |
| **Refrigerator** | 15 entities | Temperature control/monitoring, ECO mode, nanoe, defrosting, ice making |
| **Washing Machine** | 13 entities | Status monitoring, cycle control, remaining time, bitwise status |
| **Dryer** | 11 entities | Cycle control, status monitoring, remaining time, bitwise status |
| **Dehumidifier** | 14+ entities | Humidity control, fan speed, timers, tank status |
| **Air Purifier** | 4+ entities | Fan control, PM2.5 monitoring, nanoeX |
| **ERV** | 3+ entities | Operation modes, fan control |
| **Smart Switch** | 1 entity | On/off control |

### Advanced Features

- 🏭 **Factory Pattern Architecture** - Modern device creation and management
- 🔄 **Real-time Status Updates** - Automatic device state synchronization  
- 🎛️ **Comprehensive Control** - Full access to device features and settings
- 🌡️ **Multiple Sensors** - Temperature, humidity, PM2.5, and more
- ⏱️ **Formatted Time Display** - Smart time formatting (e.g., "2小時5分鐘")
- 🔢 **Bitwise Status** - Individual binary sensors for engineering information
- 🌐 **Bilingual Support** - English and Traditional Chinese labels
- 🛡️ **Robust Error Handling** - Comprehensive rate limiting and retry mechanisms

## 📋 Requirements

- **Home Assistant** 2023.1 or later
- **Python** 3.10 or later
- **Panasonic IoT TW Account** - Active account with registered devices
- **Network Access** - Internet connection to Panasonic servers (`https://ems2.panasonic.com.tw/api`)

## 🔧 Installation

### Method 1: HACS (Recommended)

1. **Install HACS** if not already installed
2. **Add Custom Repository**:
   - Go to HACS → Integrations → ⋮ → Custom repositories
   - Add `https://github.com/austinsuyoyo/panasonic_iot_tw`
   - Select category: "Integration"
3. **Install Integration**:
   - Search for "Panasonic IoT TW"
   - Click "Install"
4. **Restart Home Assistant**

### Method 2: Manual Installation

1. **Download Files**:
   ```bash
   cd /config/custom_components/
   git clone https://github.com/austinsuyoyo/panasonic_iot_tw.git
   ```

2. **Copy Integration**:
   ```bash
   cp -r panasonic_iot_tw/custom_components/panasonic_iot_tw ./
   ```

3. **Restart Home Assistant**

## ⚙️ Configuration

### Basic Setup

1. **Add Integration**:
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "Panasonic IoT TW"

2. **Enter Credentials**:
   - **Username**: Your Panasonic IoT TW email
   - **Password**: Your Panasonic IoT TW password
   - **Proxy** (optional): HTTP proxy if needed

3. **Configure Options**:
   - **Update Interval**: Device status refresh rate (default: 180 seconds)

## 🏠 Device Integration

### Refrigerator (15 Entities)

**Temperature Sensors (3):**
- Freezer temperature display (-40~40°C)
- Refrigerator temperature display (-39~40°C)  
- Partial freezing temperature display (-39~40°C)

**Mode Sensors (4):**
- Fresh freezing mode (通常/冷卻/急冷/急凍)
- Winter mode (未啟動/啟動中/可啟動)
- Shopping mode (未啟動/啟動中/可啟動)
- Vacation mode (未啟動/啟動中/可啟動)

**Binary Sensors (3):**
- ECO status (通常/運作中)
- Defrosting status (通常/除霜中)
- nanoe status (通常/運作中)

**Switch Controls (2):**
- Ice making stop control (停止/啟動)
- Quick ice making control (停止/啟動)

**Temperature Settings (3):**
- Freezer temperature setting (弱/中/強)
- Refrigerator temperature setting (弱/中/強)
- Partial freezing temperature setting (弱/中/強)

### Washing Machine (13 Entities)

**Time Sensors (2):**
- Washing remaining time (formatted: "2小時5分鐘")
- Schedule remaining time (formatted hours)

**Status Sensors (2):**
- Operation status (待機中/動作中/預約中/終了/異常)
- Cycle message (標準/快洗/大件行程/etc.)

**Bitwise Binary Sensors (8):**
- Engineering info 0x34: Prewash(128), Washing(64), Rinsing(32), Spinning(16)
- Engineering info 0x64: Prewash(1024), Washing(64), Rinsing(32), Spinning(16)

**Control Binary Sensor (1):**
- Remote control allowance (不允許/允許)

### Dryer (11 Entities)

**Time Sensors (2):**
- Drying remaining time (formatted: "2小時5分鐘")
- Schedule remaining time (formatted hours)

**Status Sensors (2):**
- Operation status (待機中/動作中/預約中/終了/異常)
- Cycle message (20+ professional programs)

**Bitwise Binary Sensors (6):**
- Engineering info 0x34: Drying(8), Air flow(4), Soft cooling(2)
- Drying mode params 0x64: Drying(8), Air flow(4), Soft cooling(2)

**Control Binary Sensor (1):**
- Remote control allowance (不允許/允許)

## 🏗️ Architecture

### Modern Factory Pattern

The integration uses a factory pattern with device-specific entity creation:

```
panasonic_iot_tw/
├── base/                    # Base infrastructure
│   ├── device_base.py      # BaseDevice abstract class
│   └── status_reader.py    # Status reading functionality
├── devices/                # Device implementations
│   ├── device_factory.py  # DeviceFactory pattern
│   ├── refrigerator.py     # 15 entities
│   ├── washing_machine.py  # 13 entities
│   ├── dryer.py           # 11 entities
│   └── ...
├── services/               # Core business logic
│   ├── smart_app.py       # Main service coordinator
│   ├── api_client.py      # HTTP API communication
│   └── ...
└── platforms/              # Home Assistant platforms
    ├── sensor.py          # PanasonicTimeSensor, PanasonicStatusSensor
    ├── binary_sensor.py   # PanasonicBitwiseBinarySensor
    └── ...
```

### Key Components

- **DeviceFactory**: Creates device instances using factory pattern
- **BaseDevice**: Abstract base with entity creation interfaces
- **Custom Sensors**: Time formatting, status mapping, bitwise operations
- **Service Layer**: API communication with rate limiting

## 🔧 Troubleshooting

### Common Issues

#### Device Creation Errors
```
ERROR: property 'device_data' of 'Device' object has no setter
```
**Solution**: Ensure you're using the latest version with BaseDevice property setters.

#### No Entities Created
```
INFO: Integration loaded but no entities appear
```
**Solutions:**
- Check device compatibility in supported devices list
- Verify devices are online in Panasonic IoT TW app
- Check logs for device type errors
- Restart Home Assistant integration

#### API Rate Limiting
```
WARNING: API request rate limit exceeded  
```
**Solutions:**
- Increase update interval to 300+ seconds
- Wait for rate limit to reset (5-10 minutes)

### Debug Logging

Enable detailed logging in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.panasonic_iot_tw: debug
```

## 🤝 Contributing

### Contributors & Acknowledgments

This project builds upon the excellent work of:

- **[PhantasWeng](https://github.com/PhantasWeng/panasonic_smart_app)** - Original Panasonic Smart App integration foundation
- **[osk2](https://github.com/osk2/panasonic_smart_app)** - Additional improvements and device support

Special thanks to these pioneers who made this comprehensive integration possible.

## 🔗 Similar Projects

Here are some other Panasonic integrations for Home Assistant that you might find useful:

- **[PhantasWeng/panasonic_smart_app](https://github.com/PhantasWeng/panasonic_smart_app)** - Original Panasonic Smart App integration with basic device support
- **[osk2/panasonic_smart_app](https://github.com/osk2/panasonic_smart_app)** - Enhanced version with additional device types and features
- **[tsunglung/panasonic_ems2](https://github.com/tsunglung/panasonic_ems2)** - Alternative Panasonic EMS2 integration approach

### Development

1. **Clone Repository**:
   ```bash
   git clone https://github.com/austinsuyoyo/panasonic_iot_tw.git
   cd panasonic_iot_tw
   ```

2. **Set Up Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

3. **Run Tests**:
   ```bash
   python -m pytest tests/ -v
   ```

### Code Standards

- **Python 3.10+** compatibility required
- **Type hints** for all public functions
- **English comments** throughout codebase
- **Factory pattern** for device creation
- **Entity-focused architecture** for platform separation

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/austinsuyoyo/panasonic_iot_tw/issues)
- **Discussions**: [GitHub Discussions](https://github.com/austinsuyoyo/panasonic_iot_tw/discussions)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)

### Reporting Bugs

When reporting bugs, please include:

1. **Home Assistant version**
2. **Integration version**  
3. **Device model and type**
4. **Error logs** (with personal info redacted)
5. **Steps to reproduce**

---

## ⚠️ Disclaimer

This is an **unofficial** integration. Panasonic and related logos are registered trademarks of Panasonic Corporation. This project is not officially affiliated with or endorsed by Panasonic Corporation.

This project is provided as-is without any warranties. Users assume all risks associated with using this integration.

---

**Made with ❤️ for the Home Assistant community**