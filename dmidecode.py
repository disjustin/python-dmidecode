#
#   dmidecode.py
#   Python module for reading DMI/SMBIOS data with JSON export support.
#
#   Copyright 2009      David Sommerseth <davids@redhat.com>
#   Copyright 2024      Enhanced with JSON/OEM support
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#

"""
Python DMI Decode Module

This module provides a Python interface for reading DMI/SMBIOS data from the system.
It supports:
  - Querying by section (bios, system, processor, memory, etc.)
  - Querying by type ID (0-255, including OEM types 128-255)
  - Export to JSON format
  - Automatic handling of OEM-specific types with raw data fallback

Usage:
    import dmidecode

    # Query by section
    bios_data = dmidecode.QuerySection('bios')

    # Query by type ID
    processor_data = dmidecode.QueryTypeId(4)

    # Get all data as JSON
    json_data = dmidecode.get_all_json()

    # Query OEM types with fallback
    oem_data = dmidecode.query_oem_type(130)

    # Export to JSON file
    dmidecode.export_json('/path/to/output.json')

    # Get hardware summary
    info = dmidecode.get_hardware_info()
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from _dmidecode import *

# Set up module logger
logger = logging.getLogger(__name__)

# =============================================================================
# DMI Type Constants and Mappings (SMBIOS Specification)
# =============================================================================

# Standard SMBIOS types (0-46)
DMI_TYPE_BIOS = 0
DMI_TYPE_SYSTEM = 1
DMI_TYPE_BASEBOARD = 2
DMI_TYPE_CHASSIS = 3
DMI_TYPE_PROCESSOR = 4
DMI_TYPE_MEMORY_CONTROLLER = 5
DMI_TYPE_MEMORY_MODULE = 6
DMI_TYPE_CACHE = 7
DMI_TYPE_PORT_CONNECTOR = 8
DMI_TYPE_SYSTEM_SLOTS = 9
DMI_TYPE_ONBOARD_DEVICES = 10
DMI_TYPE_OEM_STRINGS = 11
DMI_TYPE_SYSTEM_CONFIG = 12
DMI_TYPE_BIOS_LANGUAGE = 13
DMI_TYPE_GROUP_ASSOCIATIONS = 14
DMI_TYPE_SYSTEM_EVENT_LOG = 15
DMI_TYPE_PHYSICAL_MEMORY_ARRAY = 16
DMI_TYPE_MEMORY_DEVICE = 17
DMI_TYPE_MEMORY_ERROR_32BIT = 18
DMI_TYPE_MEMORY_ARRAY_MAPPED = 19
DMI_TYPE_MEMORY_DEVICE_MAPPED = 20
DMI_TYPE_BUILTIN_POINTING = 21
DMI_TYPE_PORTABLE_BATTERY = 22
DMI_TYPE_SYSTEM_RESET = 23
DMI_TYPE_HARDWARE_SECURITY = 24
DMI_TYPE_SYSTEM_POWER = 25
DMI_TYPE_VOLTAGE_PROBE = 26
DMI_TYPE_COOLING_DEVICE = 27
DMI_TYPE_TEMPERATURE_PROBE = 28
DMI_TYPE_ELECTRICAL_PROBE = 29
DMI_TYPE_REMOTE_ACCESS = 30
DMI_TYPE_BOOT_INTEGRITY = 31
DMI_TYPE_SYSTEM_BOOT = 32
DMI_TYPE_MEMORY_ERROR_64BIT = 33
DMI_TYPE_MANAGEMENT_DEVICE = 34
DMI_TYPE_MANAGEMENT_DEVICE_COMPONENT = 35
DMI_TYPE_MANAGEMENT_DEVICE_THRESHOLD = 36
DMI_TYPE_MEMORY_CHANNEL = 37
DMI_TYPE_IPMI_DEVICE = 38
DMI_TYPE_POWER_SUPPLY = 39
DMI_TYPE_ADDITIONAL_INFO = 40
DMI_TYPE_ONBOARD_EXTENDED = 41
DMI_TYPE_MANAGEMENT_CONTROLLER = 42
DMI_TYPE_TPM_DEVICE = 43
DMI_TYPE_PROCESSOR_ADDITIONAL = 44
DMI_TYPE_FIRMWARE_INVENTORY = 45
DMI_TYPE_STRING_PROPERTY = 46
DMI_TYPE_END_OF_TABLE = 127

# DMI type ID to human-readable name mapping
DMI_TYPES = {
    0: "BIOS Information",
    1: "System Information",
    2: "Base Board Information",
    3: "Chassis Information",
    4: "Processor Information",
    5: "Memory Controller Information",
    6: "Memory Module Information",
    7: "Cache Information",
    8: "Port Connector Information",
    9: "System Slots",
    10: "On Board Devices Information",
    11: "OEM Strings",
    12: "System Configuration Options",
    13: "BIOS Language Information",
    14: "Group Associations",
    15: "System Event Log",
    16: "Physical Memory Array",
    17: "Memory Device",
    18: "32-bit Memory Error Information",
    19: "Memory Array Mapped Address",
    20: "Memory Device Mapped Address",
    21: "Built-in Pointing Device",
    22: "Portable Battery",
    23: "System Reset",
    24: "Hardware Security",
    25: "System Power Controls",
    26: "Voltage Probe",
    27: "Cooling Device",
    28: "Temperature Probe",
    29: "Electrical Current Probe",
    30: "Out-of-Band Remote Access",
    31: "Boot Integrity Services",
    32: "System Boot Information",
    33: "64-bit Memory Error Information",
    34: "Management Device",
    35: "Management Device Component",
    36: "Management Device Threshold Data",
    37: "Memory Channel",
    38: "IPMI Device Information",
    39: "System Power Supply",
    40: "Additional Information",
    41: "Onboard Devices Extended Information",
    42: "Management Controller Host Interface",
    43: "TPM Device",
    44: "Processor Additional Information",
    45: "Firmware Inventory Information",
    46: "String Property",
    127: "End Of Table",
}

# Known OEM type mappings (commonly seen vendor-specific types)
OEM_TYPES = {
    130: "OEM Slot Information",
    133: "OEM System Information",
    134: "OEM CPU Information",
    168: "OEM One Touch Activation",
    176: "OEM HP ProLiant Information",
    177: "OEM HP ProLiant Serial",
    188: "OEM HP iLO NIC Information",
    194: "OEM HP System ID",
    199: "OEM HP PCI Bus Information",
    209: "OEM Dell BIOS Information",
    210: "OEM Dell System Information",
    212: "OEM Dell MAC Information",
    215: "OEM Memory Information",
    221: "OEM Firmware Version Information",
    222: "OEM Hardware Features",
}

# DMI Section names and their included types
DMI_SECTIONS = {
    'bios': (0, 13, 45),
    'system': (1, 11, 12, 14, 15, 23, 32),
    'baseboard': (2, 10, 41),
    'chassis': (3,),
    'processor': (4, 44),
    'memory': (5, 6, 16, 17, 18, 19, 20, 33, 37),
    'cache': (7,),
    'connector': (8,),
    'slot': (9,),
}

# DMI type groups for convenience
DMI_GROUP_STANDARD = tuple(range(0, 47))
DMI_GROUP_RESERVED = tuple(range(47, 128))
DMI_GROUP_OEM = tuple(range(128, 256))

# =============================================================================
# Auto-logging Configuration
# =============================================================================

_auto_log_enabled = False


def enable_auto_logging(level: int = logging.WARNING) -> None:
    """
    Enable automatic logging of warnings and debug messages from dmidecode operations.

    Args:
        level: Minimum logging level (default: logging.WARNING)
               Use logging.DEBUG to also log debug messages

    Example:
        import dmidecode
        import logging

        logging.basicConfig(level=logging.DEBUG)
        dmidecode.enable_auto_logging(logging.DEBUG)

        data = dmidecode.QuerySection('bios')
    """
    global _auto_log_enabled
    _auto_log_enabled = True
    if logger.level == logging.NOTSET or logger.level > level:
        logger.setLevel(level)


def disable_auto_logging() -> None:
    """Disable automatic logging of warnings and debug messages."""
    global _auto_log_enabled
    _auto_log_enabled = False


def log_messages() -> None:
    """
    Log any warnings and debug messages from the last dmidecode operation.
    This is called automatically if enable_auto_logging() has been called.
    """
    warnings = get_warnings()
    if warnings:
        for line in warnings.strip().split('\n'):
            if line.strip():
                logger.warning(line.strip())
        clear_warnings()

    debug_msgs = get_debug()
    if debug_msgs:
        for line in debug_msgs.strip().split('\n'):
            if line.strip():
                logger.debug(line.strip())
        clear_debug()


def _auto_log_wrapper(func):
    """Decorator to automatically log messages after function calls if enabled."""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if _auto_log_enabled:
            log_messages()
        return result
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# Store original functions
_QuerySection_orig = QuerySection
_QueryTypeId_orig = QueryTypeId
_dump_orig = dump

# Wrap the main query functions with auto-logging
QuerySection = _auto_log_wrapper(_QuerySection_orig)
QueryTypeId = _auto_log_wrapper(_QueryTypeId_orig)
dump = _auto_log_wrapper(_dump_orig)


# =============================================================================
# Helper Functions
# =============================================================================

def get_type_name(type_id: int) -> str:
    """
    Get the human-readable name for a DMI type ID.

    Args:
        type_id: DMI type ID (0-255)

    Returns:
        Human-readable type name
    """
    if type_id in DMI_TYPES:
        return DMI_TYPES[type_id]
    elif type_id in OEM_TYPES:
        return OEM_TYPES[type_id]
    elif 128 <= type_id <= 255:
        return f"OEM Type {type_id}"
    elif 47 <= type_id <= 127:
        return f"Reserved Type {type_id}"
    else:
        return f"Unknown Type {type_id}"


def is_oem_type(type_id: int) -> bool:
    """
    Check if a type ID is in the OEM range (128-255).

    Args:
        type_id: DMI type ID

    Returns:
        True if type_id is in the OEM range
    """
    return 128 <= type_id <= 255


def is_standard_type(type_id: int) -> bool:
    """
    Check if a type ID is a standard SMBIOS type (0-46).

    Args:
        type_id: DMI type ID

    Returns:
        True if type_id is a standard type
    """
    return 0 <= type_id <= 46


def _decode_bytes(obj: Any) -> Any:
    """Recursively decode byte strings to regular strings."""
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8', errors='replace')
        except Exception:
            return str(obj)
    elif isinstance(obj, dict):
        return {_decode_bytes(k): _decode_bytes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_decode_bytes(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_decode_bytes(item) for item in obj)
    return obj


def _format_hex_dump(data: Union[str, bytes, bytearray], bytes_per_line: int = 16) -> str:
    """
    Format binary data as a hex dump with ASCII representation.

    Args:
        data: Binary data or hex string
        bytes_per_line: Number of bytes per output line

    Returns:
        Formatted hex dump string
    """
    if isinstance(data, str):
        data = data.replace('\n', ' ').replace('\t', ' ').strip()
        hex_parts = [x for x in data.split() if x]
        try:
            data = bytes(int(x, 16) for x in hex_parts)
        except ValueError:
            return f"Invalid hex data: {data[:100]}..."
    elif not isinstance(data, (bytes, bytearray)):
        return str(data)

    lines = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i + bytes_per_line]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"{i:08X}: {hex_part:<47}  {ascii_part}")
    return '\n'.join(lines)


def _extract_strings_from_raw(raw_data: Union[str, bytes]) -> List[str]:
    """
    Extract null-terminated strings from raw DMI data.

    Args:
        raw_data: Raw DMI data (hex string or bytes)

    Returns:
        List of extracted strings
    """
    strings = []
    try:
        if isinstance(raw_data, str):
            raw_data = raw_data.replace(' ', '')
            data_bytes = bytes.fromhex(raw_data)
        else:
            data_bytes = raw_data

        current_string = bytearray()
        in_string_section = False

        for b in data_bytes:
            if in_string_section:
                if b == 0:
                    if current_string:
                        try:
                            strings.append(current_string.decode('utf-8', errors='replace'))
                        except Exception:
                            pass
                        current_string = bytearray()
                    else:
                        break  # Double null terminates string section
                else:
                    current_string.append(b)
            elif 32 <= b < 127:
                in_string_section = True
                current_string.append(b)
    except Exception:
        pass
    return strings


# =============================================================================
# OEM Type Handling
# =============================================================================

def query_oem_type(type_id: int) -> Optional[Dict]:
    """
    Query an OEM type (128-255).

    Args:
        type_id: DMI type ID (should be 128-255 for OEM types)

    Returns:
        Dictionary with DMI data, or None if type doesn't exist
    """
    try:
        data = QueryTypeId(type_id)
        clear_warnings()
        if data:
            return _decode_bytes(data)
    except Exception:
        pass
    return None


def query_type_with_fallback(type_id: int) -> Optional[Dict]:
    """
    Query a DMI type with automatic handling.

    Args:
        type_id: DMI type ID (0-255)

    Returns:
        Dictionary with DMI data, or None if type doesn't exist
    """
    try:
        data = QueryTypeId(type_id)
        if data:
            return _decode_bytes(data)
    except Exception:
        pass
    return None


# =============================================================================
# JSON Export Functions
# =============================================================================

def _make_json_serializable(obj: Any) -> Any:
    """Convert an object to a JSON-serializable format."""
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8', errors='replace')
        except Exception:
            return obj.hex()
    elif isinstance(obj, dict):
        return {str(k): _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return _make_json_serializable(obj.__dict__)
    return obj


def get_section_json(section: str, pretty: bool = False) -> str:
    """
    Get DMI section data as JSON string.

    Args:
        section: Section name ('bios', 'system', 'processor', etc.)
        pretty: Whether to format with indentation

    Returns:
        JSON string
    """
    try:
        data = QuerySection(section)
        data = _make_json_serializable(_decode_bytes(data))
        indent = 2 if pretty else None
        return json.dumps(data, indent=indent, default=str)
    except Exception as e:
        return json.dumps({'error': str(e)})


def get_type_json(type_id: int, pretty: bool = False) -> str:
    """
    Get DMI type data as JSON string.

    Args:
        type_id: DMI type ID (0-255)
        pretty: Whether to format with indentation

    Returns:
        JSON string
    """
    try:
        data = query_type_with_fallback(type_id)
        if data:
            data = _make_json_serializable(data)
            indent = 2 if pretty else None
            return json.dumps(data, indent=indent, default=str)
        return json.dumps({})
    except Exception as e:
        return json.dumps({'error': str(e)})


def get_all_json(include_oem: bool = False, pretty: bool = False) -> str:
    """
    Get all DMI data as JSON string.

    Args:
        include_oem: Whether to include OEM types (128-255)
        pretty: Whether to format with indentation

    Returns:
        JSON string with all DMI data
    """
    all_data = {
        'sections': {},
        'types': {}
    }

    # Get all sections
    for section in DMI_SECTIONS.keys():
        try:
            data = QuerySection(section)
            if data:
                all_data['sections'][section] = _make_json_serializable(_decode_bytes(data))
        except Exception:
            pass

    # Get standard types
    for type_id in range(128):
        try:
            data = QueryTypeId(type_id)
            if data:
                all_data['types'][str(type_id)] = _make_json_serializable(_decode_bytes(data))
        except Exception:
            pass

    # Get OEM types if requested
    if include_oem:
        for type_id in range(128, 256):
            try:
                data = query_oem_type(type_id)
                if data:
                    all_data['types'][str(type_id)] = _make_json_serializable(data)
            except Exception:
                pass

    indent = 2 if pretty else None
    return json.dumps(all_data, indent=indent, default=str)


def export_json(filepath: str, include_oem: bool = False, pretty: bool = True) -> bool:
    """
    Export all DMI data to a JSON file.

    Args:
        filepath: Path to output file
        include_oem: Whether to include OEM types (128-255)
        pretty: Whether to format with indentation

    Returns:
        True if export succeeded
    """
    try:
        json_data = get_all_json(include_oem=include_oem, pretty=pretty)
        with open(filepath, 'w') as f:
            f.write(json_data)
        return True
    except Exception as e:
        logger.error(f"Failed to export JSON: {e}")
        return False


# =============================================================================
# High-Level Query Functions
# =============================================================================

def get_hardware_info() -> Dict[str, Any]:
    """
    Get a summary of key hardware information.

    Returns:
        Dictionary with system, BIOS, processor, and memory information
    """
    info = {
        'system': {},
        'bios': {},
        'processor': {},
        'memory': {}
    }

    # System info
    try:
        system_data = QuerySection('system')
        system_data = _decode_bytes(system_data)
        for entry in system_data.values():
            if isinstance(entry, dict) and entry.get('dmi_type') == 1:
                data = entry.get('data', {})
                info['system'] = {
                    'manufacturer': data.get('Manufacturer', 'Unknown'),
                    'product_name': data.get('Product Name', 'Unknown'),
                    'serial_number': data.get('Serial Number', 'Unknown'),
                    'uuid': data.get('UUID', 'Unknown'),
                }
                break
    except Exception:
        pass

    # BIOS info
    try:
        bios_data = QuerySection('bios')
        bios_data = _decode_bytes(bios_data)
        for entry in bios_data.values():
            if isinstance(entry, dict) and entry.get('dmi_type') == 0:
                data = entry.get('data', {})
                info['bios'] = {
                    'vendor': data.get('Vendor', 'Unknown'),
                    'version': data.get('Version', 'Unknown'),
                    'release_date': data.get('Release Date', 'Unknown'),
                }
                break
    except Exception:
        pass

    # Processor info
    try:
        proc_data = QuerySection('processor')
        proc_data = _decode_bytes(proc_data)
        processors = []
        for entry in proc_data.values():
            if isinstance(entry, dict) and entry.get('dmi_type') == 4:
                data = entry.get('data', {})
                processors.append({
                    'version': data.get('Version', 'Unknown'),
                    'manufacturer': data.get('Manufacturer', 'Unknown'),
                    'max_speed': data.get('Max Speed', 'Unknown'),
                    'current_speed': data.get('Current Speed', 'Unknown'),
                })
        info['processor']['count'] = len(processors)
        if processors:
            info['processor']['details'] = processors
    except Exception:
        pass

    # Memory info
    try:
        mem_data = QuerySection('memory')
        mem_data = _decode_bytes(mem_data)
        total_size_mb = 0
        modules = []
        for entry in mem_data.values():
            if isinstance(entry, dict) and entry.get('dmi_type') == 17:
                data = entry.get('data', {})
                size_str = str(data.get('Size', ''))
                size_mb = 0
                if 'MB' in size_str:
                    try:
                        size_mb = int(size_str.split()[0])
                    except (ValueError, IndexError):
                        pass
                elif 'GB' in size_str:
                    try:
                        size_mb = int(size_str.split()[0]) * 1024
                    except (ValueError, IndexError):
                        pass

                if size_mb > 0:
                    total_size_mb += size_mb
                    modules.append({
                        'size': size_str,
                        'type': data.get('Type', 'Unknown'),
                        'speed': data.get('Speed', 'Unknown'),
                        'manufacturer': data.get('Manufacturer', 'Unknown'),
                    })

        if total_size_mb >= 1024:
            info['memory']['total'] = f"{total_size_mb / 1024:.1f} GB"
        else:
            info['memory']['total'] = f"{total_size_mb} MB"
        info['memory']['module_count'] = len(modules)
        if modules:
            info['memory']['modules'] = modules
    except Exception:
        pass

    return info


def get_oem_types() -> Dict[int, Dict]:
    """
    Get all OEM-specific types (128-255) present on the system.

    Returns:
        Dictionary mapping type IDs to their data
    """
    oem_data = {}
    for type_id in range(128, 256):
        try:
            data = query_oem_type(type_id)
            if data:
                oem_data[type_id] = data
        except Exception:
            pass
    return oem_data


def list_available_types() -> Dict[str, List[int]]:
    """
    List all available DMI types on the system.

    Returns:
        Dictionary with 'standard' and 'oem' lists of type IDs
    """
    available = {
        'standard': [],
        'oem': []
    }

    # Check standard types
    for type_id in range(128):
        try:
            data = QueryTypeId(type_id)
            if data:
                available['standard'].append(type_id)
        except Exception:
            pass

    # Check OEM types
    for type_id in range(128, 256):
        try:
            data = query_oem_type(type_id)
            if data:
                available['oem'].append(type_id)
        except Exception:
            pass

    return available
