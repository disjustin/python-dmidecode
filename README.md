# dmidecode

Python module for reading DMI/SMBIOS data with JSON export support.

## Table of Contents

- [dmidecode](#dmidecode)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Features](#features)
  - [Requirements](#requirements)
    - [Build Requirements](#build-requirements)
    - [Runtime Requirements](#runtime-requirements)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [From Source](#from-source)
    - [Building with Specific Python Version](#building-with-specific-python-version)
    - [Uninstall](#uninstall)
  - [Usage](#usage)
    - [Basic Usage](#basic-usage)
    - [Query by DMI Type ID](#query-by-dmi-type-id)
    - [JSON Export](#json-export)
    - [High-Level Hardware Info](#high-level-hardware-info)
    - [OEM Type Support](#oem-type-support)
    - [DMI Type Constants](#dmi-type-constants)
    - [Creating and Using DMI Dumps](#creating-and-using-dmi-dumps)
    - [Available Sections](#available-sections)
  - [API Reference](#api-reference)
    - [Core Functions](#core-functions)
      - [`QuerySection(section_name)`](#querysectionsection_name)
      - [`QueryTypeId(type_id)`](#querytypeidtype_id)
      - [`dump()`](#dump)
      - [`set_dev(device)` / `get_dev()`](#set_devdevice--get_dev)
    - [JSON Functions](#json-functions)
      - [`get_section_json(section, pretty=False)`](#get_section_jsonsection-prettyfalse)
      - [`get_type_json(type_id, pretty=False)`](#get_type_jsontype_id-prettyfalse)
      - [`get_all_json(include_oem=False, pretty=False)`](#get_all_jsoninclude_oemfalse-prettyfalse)
      - [`export_json(filepath, include_oem=False, pretty=True)`](#export_jsonfilepath-include_oemfalse-prettytrue)
    - [High-Level Functions](#high-level-functions)
      - [`get_hardware_info()`](#get_hardware_info)
      - [`get_oem_types()`](#get_oem_types)
      - [`list_available_types()`](#list_available_types)
    - [Helper Functions](#helper-functions)
      - [`get_type_name(type_id)`](#get_type_nametype_id)
      - [`is_oem_type(type_id)` / `is_standard_type(type_id)`](#is_oem_typetype_id--is_standard_typetype_id)
    - [Logging](#logging)
      - [`enable_auto_logging(level=logging.WARNING)`](#enable_auto_logginglevelloggingwarning)
      - [`disable_auto_logging()`](#disable_auto_logging)
      - [`get_warnings()` / `clear_warnings()`](#get_warnings--clear_warnings)
      - [`get_debug()` / `clear_debug()`](#get_debug--clear_debug)
  - [Examples](#examples)
  - [Troubleshooting](#troubleshooting)
    - [Permission Denied](#permission-denied)
    - [Module Not Found](#module-not-found)
    - [No SMBIOS Entry Point](#no-smbios-entry-point)
  - [License](#license)
  - [Authors](#authors)
  - [Contributing](#contributing)
  - [Links](#links)
  - [Version](#version)


## Description

dmidecode is a Python module that provides access to Desktop Management Interface (DMI) and System Management BIOS (SMBIOS) data. DMI/SMBIOS is a standard mechanism for system hardware and firmware to communicate their characteristics to system management software. This module allows Python scripts to query detailed hardware information and export it to JSON format.

## Features

- **Direct DMI/SMBIOS Access**: Read hardware information directly from /dev/mem or from dump files
- **Multiple Query Methods**: Query by section name or DMI type ID (0-255, including OEM types)
- **JSON Export**: Export all DMI data to JSON format
- **DMI Type Constants**: Comprehensive constants for all standard SMBIOS types
- **OEM Type Support**: Query vendor-specific types (128-255) with automatic handling
- **High-Level API**: Convenience functions like `get_hardware_info()` for common tasks
- **DMI Data Dumping**: Create dump files for offline analysis or testing
- **Root and Non-Root Support**: First run as root to create dump, subsequent runs can be non-root
- **Python 3.9+ Compatible**: Works with Python 3.9.19 (Rocky Linux 9.5) and later

## Requirements

### Build Requirements

- Python 3.9+ development headers
- GCC or compatible C compiler
- libxml2 development headers (required for C extension build)
- make

### Runtime Requirements

- Python 3.9+
- Root privileges (for initial DMI data access from /dev/mem)

## Installation

### Prerequisites

**Rocky Linux / RHEL / CentOS / Fedora:**

```bash
sudo dnf install -y python3-devel libxml2-devel gcc make
```

**Ubuntu / Debian:**

```bash
sudo apt-get install -y python3-dev libxml2-dev gcc make
```

### From Source

1. Clone or download the repository:

```bash
git clone https://github.com/disjustin/python-dmidecode.git
cd python-dmidecode
```

1. Build the module:

```bash
make clean
make
```

1. Install (requires root):

```bash
sudo make install
```

1. Verify installation:

```bash
python3 -c "import dmidecode; print(dmidecode.version)"
```

### Building with Specific Python Version

```bash
make PY_BIN=python3.9
```

### Uninstall

```bash
sudo make uninstall
```

## Usage

### Basic Usage

**Important**: The first run must be executed as root to access /dev/mem:

```python
#!/usr/bin/env python3
import dmidecode

# Query by section (returns dictionary)
bios_info = dmidecode.QuerySection('bios')
system_info = dmidecode.QuerySection('system')
processor_info = dmidecode.QuerySection('processor')
memory_info = dmidecode.QuerySection('memory')

# Print system information
for key, value in system_info.items():
    if isinstance(value, dict) and value.get('dmi_type') == 1:
        print(f"Manufacturer: {value['data']['Manufacturer']}")
        print(f"Product Name: {value['data']['Product Name']}")
        print(f"Serial Number: {value['data']['Serial Number']}")
```

### Query by DMI Type ID

```python
import dmidecode

# Query by type ID (0-255)
bios = dmidecode.QueryTypeId(0)           # BIOS Information
system = dmidecode.QueryTypeId(1)         # System Information
processor = dmidecode.QueryTypeId(4)      # Processor Information
memory = dmidecode.QueryTypeId(17)        # Memory Device

# Using type constants
processor = dmidecode.QueryTypeId(dmidecode.DMI_TYPE_PROCESSOR)
memory = dmidecode.QueryTypeId(dmidecode.DMI_TYPE_MEMORY_DEVICE)
```

### JSON Export

```python
import dmidecode

# Get section as JSON
bios_json = dmidecode.get_section_json('bios', pretty=True)
print(bios_json)

# Get specific type as JSON
processor_json = dmidecode.get_type_json(4, pretty=True)

# Get all DMI data as JSON
all_json = dmidecode.get_all_json(include_oem=True, pretty=True)

# Export to file
dmidecode.export_json('dmidecode-1.json', include_oem=True)
```

### High-Level Hardware Info

```python
import dmidecode

# Get hardware summary
info = dmidecode.get_hardware_info()

print(f"System: {info['system']['manufacturer']} {info['system']['product_name']}")
print(f"BIOS: {info['bios']['vendor']} {info['bios']['version']}")
print(f"Processors: {info['processor']['count']}")
print(f"Memory: {info['memory']['total']}")
```

### OEM Type Support

```python
import dmidecode

# Query specific OEM type
oem_data = dmidecode.query_oem_type(130)

# Get all OEM types present on system
all_oem = dmidecode.get_oem_types()
for type_id, data in all_oem.items():
    print(f"OEM Type {type_id}: {dmidecode.get_type_name(type_id)}")

# List all available types
available = dmidecode.list_available_types()
print(f"Standard types: {available['standard']}")
print(f"OEM types: {available['oem']}")
```

### DMI Type Constants

```python
import dmidecode

# Standard type constants
dmidecode.DMI_TYPE_BIOS                    # 0
dmidecode.DMI_TYPE_SYSTEM                  # 1
dmidecode.DMI_TYPE_BASEBOARD               # 2
dmidecode.DMI_TYPE_CHASSIS                 # 3
dmidecode.DMI_TYPE_PROCESSOR               # 4
dmidecode.DMI_TYPE_MEMORY_DEVICE           # 17
# ... and more (0-46)

# Get human-readable type name
name = dmidecode.get_type_name(4)  # "Processor Information"
name = dmidecode.get_type_name(130)  # "OEM Slot Information" or "OEM Type 130"

# Check type category
dmidecode.is_standard_type(4)   # True
dmidecode.is_oem_type(130)      # True

# Type groups
dmidecode.DMI_GROUP_STANDARD    # (0, 1, 2, ... 46)
dmidecode.DMI_GROUP_OEM         # (128, 129, ... 255)
```

### Creating and Using DMI Dumps

```python
import dmidecode

# Set dump file location
dmidecode.set_dev('my_hardware.dump')

# Create dump (requires root privileges)
dmidecode.dump()

# Now you can query from the dump file (no root needed)
bios = dmidecode.QuerySection('bios')
```

### Available Sections

| Section Name | DMI Types | Information |
|-------------|-----------|-------------|
| bios | 0, 13, 45 | BIOS information, language, firmware |
| system | 1, 11, 12, 14, 15, 23, 32 | System information, OEM strings, event log |
| baseboard | 2, 10, 41 | Base board and onboard devices |
| chassis | 3 | Chassis information |
| processor | 4, 44 | Processor information |
| memory | 5, 6, 16, 17, 18, 19, 20, 33, 37 | Memory arrays and devices |
| cache | 7 | Cache information |
| connector | 8 | Port connectors |
| slot | 9 | System slots |

## API Reference

### Core Functions

#### `QuerySection(section_name)`

Query DMI data by section name.

- **Parameters**: section_name (str) - 'all', 'bios', 'system', 'baseboard', 'chassis', 'processor', 'memory', 'cache', 'connector', 'slot'
- **Returns**: Dictionary containing DMI data

#### `QueryTypeId(type_id)`

Query DMI data by type ID.

- **Parameters**: type_id (int) - DMI type ID (0-255)
- **Returns**: Dictionary containing DMI data

#### `dump()`

Create a dump of DMI data to file.

- **Returns**: Status string
- **Requires**: Root privileges

#### `set_dev(device)` / `get_dev()`

Set/get the device or dump file path.

### JSON Functions

#### `get_section_json(section, pretty=False)`

Get section data as JSON string.

#### `get_type_json(type_id, pretty=False)`

Get type data as JSON string.

#### `get_all_json(include_oem=False, pretty=False)`

Get all DMI data as JSON string.

#### `export_json(filepath, include_oem=False, pretty=True)`

Export all DMI data to a JSON file.

### High-Level Functions

#### `get_hardware_info()`

Get summary of system, BIOS, processor, and memory information.

#### `get_oem_types()`

Get all OEM types (128-255) present on the system.

#### `list_available_types()`

List all available DMI types on the system.

### Helper Functions

#### `get_type_name(type_id)`

Get human-readable name for a DMI type ID.

#### `is_oem_type(type_id)` / `is_standard_type(type_id)`

Check if type ID is OEM (128-255) or standard (0-46).

### Logging

#### `enable_auto_logging(level=logging.WARNING)`

Enable automatic logging of warnings and debug messages.

#### `disable_auto_logging()`

Disable automatic logging.

#### `get_warnings()` / `clear_warnings()`

Get/clear warning messages.

#### `get_debug()` / `clear_debug()`

Get/clear debug messages.

## Examples

See the `examples/` directory:

- `test_dmidecode_features.py` - Comprehensive test script for all features
- `dmidump.py` - Basic usage example
- `dump_all_dmi.py` - Full DMI data dumper with multiple output formats

```bash
# Run test script
sudo python3 examples/test_dmidecode_features.py

# With dump file (no root needed after dump creation)
python3 examples/test_dmidecode_features.py --dump-file dmidata.dump
```

## Troubleshooting

### Permission Denied

Run as root or create a dump file first:

```bash
sudo python3 -c "import dmidecode; dmidecode.dump()"
python3 your_script.py  # Now works without root
```

### Module Not Found

Ensure the module is installed:

```bash
sudo make install
python3 -c "import dmidecode; print('OK')"
```

### No SMBIOS Entry Point

Your system may not have DMI/SMBIOS support, or you're running in a VM that doesn't expose it.

## License

GNU General Public License version 2 (GPLv2)

See the LICENSE file for details.

## Authors

- Nima Talebi - Original author
- David Sommerseth - Maintainer
- See doc/AUTHORS for complete list of contributors

## Contributing

Contributions are welcome! Please ensure:

1. Code follows existing style
2. All tests pass
3. New features include tests
4. Documentation is updated

Join the discussion mailing list:
<http://lists.nongnu.org/mailman/listinfo/dmidecode-devel>

## Links

- Project Page: <http://projects.autonomy.net.au/python-dmidecode/>
- Upstream dmidecode: <http://www.nongnu.org/dmidecode/>
- Bug Reports: Use GitHub issues or contact maintainers

## Version

Current version: 3.12.3

See doc/changelog for detailed version history.
