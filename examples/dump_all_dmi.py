#!/usr/bin/env python3
#
#   dump_all_dmi.py
#   Comprehensive DMI data dumper - outputs all available DMI information
#
#   Copyright 2024
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
DMI Data Dumper

This script queries and displays ALL available DMI/SMBIOS information from your system,
including standard SMBIOS types (0-127) and OEM-specific vendor types (128-255).
It can output data in multiple formats and provides complete hardware inventory.

Supported DMI Types:
    0-46    : Standard SMBIOS types (BIOS, System, Processor, Memory, etc.)
    47-127  : Reserved for future SMBIOS specification use
    128-255 : OEM-specific types (vendor-defined, decoded when possible)

Usage:
    # Basic usage (must be run as root on first run)
    sudo python3 dump_all_dmi.py

    # Dump all types including OEM types (128-255)
    sudo python3 dump_all_dmi.py --all-types

    # Dump only OEM-specific types
    sudo python3 dump_all_dmi.py --oem-only

    # Dump specific type IDs (including OEM)
    sudo python3 dump_all_dmi.py --type 0,1,4,130,221

    # List all known DMI type IDs
    python3 dump_all_dmi.py --list-types

    # Output as JSON
    sudo python3 dump_all_dmi.py --format json > hardware.json

    # Output specific sections only
    python3 dump_all_dmi.py --sections bios,system,processor

    # Show debug messages
    python3 dump_all_dmi.py --debug

    # Use existing dump file (no root needed)
    python3 dump_all_dmi.py --dump-file /path/to/dmidata.dump

OEM Type Handling:
    OEM types (128-255) are vendor-specific and may contain:
    - Binary data (displayed as hex dump)
    - Embedded strings (automatically decoded when found)
    - Structured data (displayed with field names when parseable)

    If an OEM type cannot be fully parsed, raw hex values are displayed
    along with any successfully decoded strings.
"""

import dmidecode
import sys
import os
import json
import logging
import argparse
import pprint as pprint_module
from pprint import pprint

# Try to import libxml2 for XML API support
try:
    import libxml2
    HAS_LIBXML2 = True
except ImportError:
    HAS_LIBXML2 = False

# Global debug mode flag
DEBUG_MODE = False

# DMI Type ID to Name mapping (SMBIOS specification)
# Types 0-43 are defined by SMBIOS specification
# Types 44-127 are reserved for future use
# Types 128-255 are OEM-specific
DMI_TYPES = {
    0: "BIOS",
    1: "System",
    2: "Base Board",
    3: "Chassis",
    4: "Processor",
    5: "Memory Controller",
    6: "Memory Module",
    7: "Cache",
    8: "Port Connector",
    9: "System Slots",
    10: "On Board Devices",
    11: "OEM Strings",
    12: "System Configuration Options",
    13: "BIOS Language",
    14: "Group Associations",
    15: "System Event Log",
    16: "Physical Memory Array",
    17: "Memory Device",
    18: "32-bit Memory Error",
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
    30: "Out-of-band Remote Access",
    31: "Boot Integrity Services",
    32: "System Boot",
    33: "64-bit Memory Error",
    34: "Management Device",
    35: "Management Device Component",
    36: "Management Device Threshold Data",
    37: "Memory Channel",
    38: "IPMI Device",
    39: "Power Supply",
    40: "Additional Information",
    41: "Onboard Device Extended Information",
    42: "Management Controller Host Interface",
    43: "TPM Device",
    44: "Processor Additional Information",
    45: "Firmware Inventory Information",
    46: "String Property",
    # Types 47-127 are reserved for future SMBIOS specification use
    127: "End Of Table",
}

# OEM-specific type ranges (128-255)
# Common OEM types seen in the wild
OEM_TYPES = {
    130: "OEM Slot Information",
    133: "OEM System Information",
    134: "OEM CPU Information",
    168: "OEM One Touch Activation",
    215: "OEM Memory Information",
    221: "OEM Firmware Version Information",
}

# DMI Section names and their included types
DMI_SECTIONS = {
    'bios': (0, 13, 45),  # BIOS, BIOS Language, Firmware Inventory
    'system': (1, 11, 12, 14, 15, 23, 32),  # System, OEM Strings, Config, Group Assoc, Event Log, Reset, Boot
    'baseboard': (2, 10, 41),  # Base Board, On Board Devices, Onboard Extended
    'chassis': (3,),  # Chassis
    'processor': (4, 44),  # Processor, Processor Additional Info
    'memory': (5, 6, 16, 17, 18, 19, 20, 33, 37),  # Memory Controller/Module/Array/Device/Error/Mapped/Channel
    'cache': (7,),  # Cache
    'connector': (8,),  # Port Connector
    'slot': (9,),  # System Slots
}


def decode_bytes(obj):
    """Recursively decode byte strings to regular strings"""
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8', errors='replace')
        except:
            return str(obj)
    elif isinstance(obj, dict):
        return {decode_bytes(k): decode_bytes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decode_bytes(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(decode_bytes(item) for item in obj)
    else:
        return obj


def get_type_name(type_id):
    """Get the human-readable name for a DMI type ID"""
    if type_id in DMI_TYPES:
        return DMI_TYPES[type_id]
    elif type_id in OEM_TYPES:
        return OEM_TYPES[type_id]
    elif 128 <= type_id <= 255:
        return f"OEM-specific Type {type_id}"
    elif 44 <= type_id <= 127:
        return f"Reserved Type {type_id}"
    else:
        return f"Unknown Type {type_id}"


def is_oem_type(type_id):
    """Check if a type ID is in the OEM range (128-255)"""
    return 128 <= type_id <= 255


def format_hex_dump(data, bytes_per_line=16):
    """Format binary data as a hex dump with ASCII representation"""
    if isinstance(data, str):
        # Clean and convert hex string to bytes
        data = data.replace('\n', ' ').replace('\t', ' ').strip()
        hex_parts = [x for x in data.split() if x]  # Split into hex pairs
        try:
            data = bytes(int(x, 16) for x in hex_parts)
        except ValueError:
            return f"Invalid hex data: {data[:100]}..."  # Fallback for bad data
    elif not isinstance(data, (bytes, bytearray)):
        return str(data)

    lines = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i + bytes_per_line]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"    {i:08X}: {hex_part:<47}  {ascii_part}")
    return '\n'.join(lines)


def parse_raw_dmi_data(raw_data):
    """
    Parse raw DMI data and attempt to extract meaningful information.

    Returns a dict with:
    - 'header': Parsed header info (type, length, handle)
    - 'data_bytes': Raw data bytes as hex
    - 'strings': List of decoded strings if present
    - 'decoded': Dict of decoded fields if parsing succeeded
    """
    result = {
        'header': {},
        'data_bytes': None,
        'strings': [],
        'decoded': {},
        'raw': raw_data
    }

    if isinstance(raw_data, dict):
        # Already parsed by python-dmidecode
        return result

    if isinstance(raw_data, str):
        # Could be a hex string representation
        result['data_bytes'] = raw_data

        # Try to extract strings from the data
        # DMI strings are null-terminated, following the fixed data section
        try:
            data_bytes = bytes.fromhex(raw_data.replace(' ', ''))
            strings = []
            current_string = bytearray()
            in_string_section = False

            for i, b in enumerate(data_bytes):
                if in_string_section:
                    if b == 0:
                        if current_string:
                            try:
                                strings.append(current_string.decode('utf-8', errors='replace'))
                            except:
                                strings.append(current_string.hex())
                            current_string = bytearray()
                        else:
                            # Double null terminates string section
                            break
                    else:
                        current_string.append(b)
                elif b >= 32 and b < 127:
                    # Looks like start of printable text
                    in_string_section = True
                    current_string.append(b)

            if strings:
                result['strings'] = strings
        except:
            pass

    return result


def try_decode_oem_strings(data):
    """
    Attempt to extract strings from OEM-specific data.

    OEM data often contains embedded strings that can be decoded.
    Returns a list of found strings.
    """
    strings = []

    if isinstance(data, dict):
        # Recursively search for string-like values
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 0:
                # Check if it looks like a meaningful string
                printable_ratio = sum(1 for c in value if c.isprintable()) / len(value)
                if printable_ratio > 0.8:
                    strings.append((key, value))
            elif isinstance(value, dict):
                strings.extend(try_decode_oem_strings(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and len(item) > 0:
                        printable_ratio = sum(1 for c in item if c.isprintable()) / len(item)
                        if printable_ratio > 0.8:
                            strings.append((key, item))

    return strings


def format_oem_data(type_id, entry, show_raw=False):
    """Format OEM-specific type data for display"""
    lines = []
    type_name = get_type_name(type_id)

    lines.append(f"  Type: {type_id} ({type_name})")

    if 'data' in entry and isinstance(entry['data'], dict):
        data = entry['data']

        # Handle Header and Data first (raw bytes)
        raw_data_keys = ['Header and Data', 'raw_data', 'Raw Data']
        for raw_key in raw_data_keys:
            if raw_key in data:
                raw_value = data[raw_key]
                lines.append(f"  Header and Data:")
                if isinstance(raw_value, str):
                    # Format as hex dump with proper formatting
                    lines.append(format_hex_dump(raw_value))
                elif isinstance(raw_value, (list, tuple)):
                    # Format bytes as hex
                    hex_str = ' '.join(f'{b:02X}' if isinstance(b, int) else str(b) for b in raw_value)
                    lines.append(f"    {hex_str}")
                else:
                    lines.append(f"    {raw_value}")
                break  # Only show one raw data section

        # Handle Strings
        if 'Strings' in data and data['Strings']:
            lines.append(f"  Strings:")
            strings_data = data['Strings']
            if isinstance(strings_data, dict):
                for idx in sorted(strings_data.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                    lines.append(f"    String {idx}: {strings_data[idx]}")
            elif isinstance(strings_data, list):
                for i, s in enumerate(strings_data, 1):
                    lines.append(f"    String {i}: {s}")

        # Display other structured data
        for key, value in sorted(data.items()):
            if key in ('Header and Data', 'raw_data', 'Raw Data', 'Strings'):
                continue  # Already handled
            if isinstance(value, dict):
                lines.append(f"  {key}:")
                for k, v in value.items():
                    lines.append(f"    {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"  {key}:")
                for item in value:
                    lines.append(f"    - {item}")
            else:
                lines.append(f"  {key}: {value}")

    elif 'data' in entry:
        # Raw data that's not a dict
        lines.append(f"  Raw Data: {entry['data']}")

    if show_raw:
        lines.append("  Full Entry:")
        for line in pprint_module.pformat(entry, indent=4).split('\n'):
            lines.append(f"    {line}")

    return '\n'.join(lines)


def query_type_with_xml_fallback(type_id):
    """
    Query a DMI type, falling back to XML API for types without pymap.xml mappings.

    This is particularly useful for OEM types (128-255) which don't have
    standard mappings defined.

    Returns:
        dict: Dictionary with DMI data, or None if type doesn't exist
    """
    # First try the standard Python API
    try:
        data = dmidecode.QueryTypeId(type_id)
        if data:
            return data
    except Exception:
        pass

    # Fall back to XML API for unmapped types (especially OEM types)
    if HAS_LIBXML2:
        try:
            xml_api = dmidecode.dmidecodeXML()
            xml_api.SetResultType(dmidecode.DMIXML_DOC)
            xml_doc = xml_api.QueryTypeId(type_id)

            if xml_doc:
                # Parse XML to extract data
                data = parse_xml_dmi_data(xml_doc, type_id)
                xml_doc.freeDoc()
                if data:
                    return data
        except Exception as e:
            logging.debug(f"XML API query failed for type {type_id}: {e}")

    return None


def parse_xml_dmi_data(xml_doc, type_id):
    """
    Parse XML DMI data into a Python dictionary.

    This handles raw/OEM types that don't have pymap.xml mappings.
    """
    result = {}

    try:
        # Get root element
        root = xml_doc.getRootElement()
        if root is None:
            return None

        # Find all elements with matching type
        # The XML structure varies, but typically has dmi elements with type attributes
        context = xml_doc.xpathNewContext()

        # Try to find nodes by type attribute
        nodes = context.xpathEval(f"//*[@type='{type_id}']")
        if not nodes:
            # Try decimal format
            nodes = context.xpathEval(f"//*[@type='{type_id}' or @dmitype='{type_id}']")

        for node in nodes:
            handle = node.prop('handle') or f'0x{type_id:04X}'

            entry = {
                'dmi_type': type_id,
                'dmi_handle': handle,
                'dmi_size': int(node.prop('size') or 0),
                'data': {}
            }

            # Extract all child elements as data
            child = node.children
            strings = []
            raw_bytes = []

            while child:
                if child.type == 'element':
                    name = child.name
                    content = child.content

                    if content and content.strip():
                        # Check if it's a string record
                        if name == 'Record' or name == 'String':
                            index = child.prop('index') or str(len(strings) + 1)
                            strings.append(content.strip())
                        elif name == 'RawBytes' or name == 'Data':
                            raw_bytes.append(content.strip())
                        else:
                            entry['data'][name] = content.strip()

                    # Also check for attributes on child elements
                    if child.properties:
                        prop = child.properties
                        while prop:
                            if prop.content:
                                entry['data'][f'{name}_{prop.name}'] = prop.content
                            prop = prop.next

                child = child.next

            # Add strings if found
            if strings:
                entry['data']['Strings'] = {str(i+1): s for i, s in enumerate(strings)}

            # Add raw bytes if found
            if raw_bytes:
                entry['data']['Raw Data'] = ' '.join(raw_bytes)

            result[handle] = entry

        context.xpathFreeContext()

    except Exception as e:
        logging.debug(f"Error parsing XML for type {type_id}: {e}")

    return result if result else None


def query_oem_type_raw(type_id):
    """
    Query an OEM type and return raw data even if no mapping exists.

    This function tries multiple approaches to get OEM data:
    1. Standard QueryTypeId
    2. XML API with parsing
    3. Raw XML content extraction
    """
    # Try standard API first (silently - warnings will come from XML API if needed)
    try:
        data = dmidecode.QueryTypeId(type_id)
        # Clear warnings generated by QueryTypeId for unmapped types
        clear_warnings_if_not_debug()
        if data:
            return decode_bytes(data)
    except Exception:
        pass

    # Try XML API
    if HAS_LIBXML2:
        try:
            xml_api = dmidecode.dmidecodeXML()
            xml_api.SetResultType(dmidecode.DMIXML_DOC)
            xml_doc = xml_api.QueryTypeId(type_id)
            # Clear warnings generated by XML API
            clear_warnings_if_not_debug()

            if xml_doc:
                result = {}
                root = xml_doc.getRootElement()

                if root:
                    # Try to get serialized content
                    xml_str = xml_doc.serialize('utf-8')

                    # Parse the XML string to extract useful data
                    if xml_str and len(xml_str) > 100:  # Has meaningful content
                        result = extract_data_from_xml_string(xml_str, type_id)

                xml_doc.freeDoc()

                if result:
                    return result
        except Exception as e:
            logging.debug(f"OEM type {type_id} XML query failed: {e}")

    return None


def extract_data_from_xml_string(xml_str, type_id):
    """
    Extract data from XML string for OEM types.

    Parses XML string and extracts handle, size, raw bytes (Header and Data), and strings.
    The XML format from dmidecode has:
    - <HeaderAndData><Row index="0">0x020x03...</Row></HeaderAndData>
    - <Strings><String index="1">some string</String></Strings>
    """
    import re
    result = {}

    # Ensure we're working with a string
    if isinstance(xml_str, bytes):
        xml_str = xml_str.decode('utf-8', errors='replace')

    # Find all handles in the XML
    handle_pattern = r'handle="(0x[0-9A-Fa-f]+)"'
    handles = re.findall(handle_pattern, xml_str)

    # Find type and size - look for the OEM-specific structure
    type_pattern = rf'type="{type_id}"[^>]*size="(\d+)"'
    sizes = re.findall(type_pattern, xml_str)

    # Find Row elements inside HeaderAndData - these contain the raw bytes
    # Format is: <Row index="0">0x020x030x04...</Row>
    row_pattern = r'<Row[^>]*>([^<]+)</Row>'
    row_data = re.findall(row_pattern, xml_str)

    # Find String elements inside Strings
    # Format is: <String index="1">some string</String>
    string_pattern = r'<String[^>]*index="(\d+)"[^>]*>([^<]*)</String>'
    strings = re.findall(string_pattern, xml_str)

    # Also check for Record elements (alternative format)
    record_pattern = r'<Record[^>]*index="(\d+)"[^>]*>([^<]+)</Record>'
    records = re.findall(record_pattern, xml_str)
    strings.extend(records)

    for i, handle in enumerate(handles):
        entry = {
            'dmi_type': type_id,
            'dmi_handle': handle,
            'dmi_size': int(sizes[i]) if i < len(sizes) else 0,
            'data': {}
        }

        # Process raw data from Row elements
        if row_data:
            # Combine all rows and format as hex bytes
            all_bytes = []
            for row in row_data:
                # Row data is in format "0x020x030x04..." - extract hex values
                hex_values = re.findall(r'0x([0-9A-Fa-f]{2})', row)
                all_bytes.extend(hex_values)

            if all_bytes:
                # Format as space-separated hex bytes (uppercase)
                entry['data']['Header and Data'] = ' '.join(b.upper() for b in all_bytes)

        # Add strings
        if strings:
            entry['data']['Strings'] = {}
            for idx, val in strings:
                if val.strip():
                    entry['data']['Strings'][idx] = val.strip()

        result[handle] = entry

    return result


def setup_logging(debug=False):
    """Configure logging based on debug flag"""
    global DEBUG_MODE
    DEBUG_MODE = debug
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )
    if debug:
        dmidecode.enable_auto_logging(level)
    else:
        # Disable auto-logging to suppress warnings
        dmidecode.disable_auto_logging()


def clear_warnings_if_not_debug():
    """Clear warnings from dmidecode unless in debug mode"""
    if not DEBUG_MODE:
        dmidecode.clear_warnings()
        dmidecode.clear_debug()


def log_messages_if_debug():
    """Log messages from dmidecode only if in debug mode, otherwise clear them"""
    if DEBUG_MODE:
        warnings = dmidecode.get_warnings()
        if warnings:
            print("\n" + "=" * 70)
            print("DMIDECODE LOG MESSAGES")
            print("=" * 70)
            for msg in warnings:
                print(f"WARNING: {msg}")
            for msg in errors:
                print(f"ERROR: {msg}")
    else:
        dmidecode.clear_warnings()
        dmidecode.clear_debug()


def check_root():
    """Check if running as root and provide helpful message"""
    if os.getuid() != 0:
        print("=" * 70)
        print("WARNING: Not running as root")
        print("=" * 70)
        print()
        print("The first run must be as root to read from /dev/mem.")
        print("However, if a DMI dump file exists, you can use it instead:")
        print()
        print("  1. Create dump as root:")
        print("     sudo python3 dump_all_dmi.py --create-dump")
        print()
        print("  2. Then run without root:")
        print("     python3 dump_all_dmi.py --dump-file dmidata.dump")
        print()
        print("Attempting to continue anyway...")
        print("=" * 70)
        print()
        return False
    return True


def create_dump():
    """Create a DMI data dump file"""
    print("Creating DMI dump file...")
    dmidecode.set_dev("dmidata.dump")
    result = dmidecode.dump()
    print(f"Dump created: {result}")
    print("You can now run this script without root using:")
    print("  python3 dump_all_dmi.py --dump-file dmidata.dump")
    log_messages_if_debug()


def dump_section_text(section_name, data, show_raw=False):
    """Dump a DMI section in human-readable text format"""
    print("\n" + "=" * 70)
    print(f"SECTION: {section_name.upper()}")
    print("=" * 70)

    if not data:
        print("  (No data available)")
        return

    for handle, entry in data.items():
        if not isinstance(entry, dict):
            continue

        dmi_type = entry.get('dmi_type', 'Unknown')
        type_name = get_type_name(dmi_type) if isinstance(dmi_type, int) else f"Type {dmi_type}"
        dmi_size = entry.get('dmi_size', 'Unknown')

        print(f"\nHandle: {handle}")
        print(f"Type: {dmi_type} ({type_name})")
        print(f"Size: {dmi_size} bytes")

        if is_oem_type(dmi_type) if isinstance(dmi_type, int) else False:
            # Use OEM-specific formatting
            print(format_oem_data(dmi_type, entry, show_raw))
        elif 'data' in entry and isinstance(entry['data'], dict):
            print("Data:")
            for key, value in sorted(entry['data'].items()):
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                elif isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")

            if show_raw:
                print("\nRaw Entry:")
                pprint(entry, indent=4)
        elif 'data' in entry:
            print(f"Data: {entry['data']}")
            if show_raw:
                print("\nRaw Entry:")
                pprint(entry, indent=4)
        else:
            # Entry without 'data' key - show all non-metadata
            for key, value in sorted(entry.items()):
                if key.startswith('dmi_'):
                    continue
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                elif isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")

            if show_raw:
                print("\nRaw Entry:")
                pprint(entry, indent=4)


def dump_type_text(type_id, data, show_raw=False):
    """Dump a specific DMI type in human-readable text format"""
    type_name = get_type_name(type_id)
    is_oem = is_oem_type(type_id)

    print("\n" + "=" * 70)
    if is_oem:
        print(f"DMI TYPE {type_id} (0x{type_id:02X}): {type_name}")
    else:
        print(f"DMI TYPE {type_id}: {type_name}")
    print("=" * 70)

    if not data:
        print("  (No data available)")
        return

    count = 0
    for handle, entry in data.items():
        if not isinstance(entry, dict):
            continue

        count += 1
        dmi_size = entry.get('dmi_size', 'Unknown')
        print(f"\n[{count}] Handle: {handle} (Size: {dmi_size} bytes)")

        if is_oem:
            # Use OEM-specific formatting
            print(format_oem_data(type_id, entry, show_raw))
        elif 'data' in entry and isinstance(entry['data'], dict):
            for key, value in sorted(entry['data'].items()):
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                elif isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")

            if show_raw:
                print("\nRaw Entry:")
                pprint(entry, indent=4)
        elif 'data' in entry:
            # Non-dict data (possibly raw bytes or unparsed)
            print(f"  Data: {entry['data']}")
            if show_raw:
                print("\nRaw Entry:")
                pprint(entry, indent=4)
        else:
            # Entry without 'data' key - show what we have
            for key, value in sorted(entry.items()):
                if key.startswith('dmi_'):
                    continue  # Skip metadata
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                elif isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")

            if show_raw:
                print("\nRaw Entry:")
                pprint(entry, indent=4)

    print(f"\nTotal {type_name} entries: {count}")


def dump_all_sections(output_format='text', sections=None, show_raw=False):
    """Dump all DMI sections"""
    all_data = {}

    if sections is None:
        sections = list(DMI_SECTIONS.keys())

    for section in sections:
        try:
            data = dmidecode.QuerySection(section)
            data = decode_bytes(data)  # Decode byte strings to regular strings
            all_data[section] = data

            if output_format == 'text':
                dump_section_text(section, data, show_raw)

        except Exception as e:
            print(f"Error querying section '{section}': {e}")
            continue

    log_messages_if_debug()

    if output_format == 'json':
        print(json.dumps(all_data, indent=2, default=str))
    elif output_format == 'python':
        pprint(all_data)

    return all_data


def dump_all_types(output_format='text', show_raw=False, include_oem=True):
    """
    Dump all DMI types individually.

    Args:
        output_format: Output format ('text', 'json', 'python')
        show_raw: Whether to show raw entry data
        include_oem: Whether to scan OEM types (128-255)
    """
    all_data = {}
    standard_found = 0
    oem_found = 0

    print("\n" + "=" * 70)
    if include_oem:
        print("DUMPING ALL DMI TYPES (0-127) AND OEM TYPES (128-255)")
    else:
        print("DUMPING ALL DMI TYPES (0-127)")
    print("=" * 70)

    # Standard SMBIOS types (0-127)
    # Types 0-46 are defined, 47-127 are reserved but might be used
    for type_id in range(128):
        try:
            data = dmidecode.QueryTypeId(type_id)

            # Only process if we got data
            if data:
                data = decode_bytes(data)  # Decode byte strings to regular strings
                all_data[type_id] = data
                standard_found += 1

                if output_format == 'text':
                    dump_type_text(type_id, data, show_raw)

        except Exception as e:
            # Silently skip types that don't exist or error
            continue

    # OEM-specific types (128-255)
    if include_oem:
        if output_format == 'text':
            print("\n" + "=" * 70)
            print("OEM-SPECIFIC TYPES (128-255)")
            print("=" * 70)

        for type_id in range(128, 256):
            try:
                # Use XML API fallback for OEM types since they don't have pymap.xml mappings
                data = query_oem_type_raw(type_id)

                # Only process if we got data
                if data:
                    data = decode_bytes(data)  # Decode byte strings to regular strings
                    all_data[type_id] = data
                    oem_found += 1

                    if output_format == 'text':
                        dump_type_text(type_id, data, show_raw)

            except Exception as e:
                # Silently skip types that don't exist or error
                logging.debug(f"Error querying OEM type {type_id}: {e}")
                continue

    log_messages_if_debug()

    # Print summary
    if output_format == 'text':
        print("\n" + "=" * 70)
        print("TYPE SUMMARY")
        print("=" * 70)
        print(f"  Standard types found: {standard_found}")
        if include_oem:
            print(f"  OEM types found: {oem_found}")
            if not HAS_LIBXML2 and oem_found == 0:
                print("  Note: libxml2 not available, OEM type parsing limited")
        print(f"  Total types: {standard_found + oem_found}")

    if output_format == 'json':
        print(json.dumps(all_data, indent=2, default=str))
    elif output_format == 'python':
        pprint(all_data)

    return all_data


def dump_oem_types_only(output_format='text', show_raw=False):
    """
    Dump only OEM-specific types (128-255).

    This is useful for quickly seeing what vendor-specific information
    is available on a system.
    """
    all_data = {}
    oem_found = 0

    print("\n" + "=" * 70)
    print("DUMPING OEM-SPECIFIC TYPES (128-255)")
    print("=" * 70)

    if not HAS_LIBXML2:
        print("Note: libxml2 not available - OEM type parsing may be limited")

    for type_id in range(128, 256):
        try:
            # Use XML API fallback for OEM types since they don't have pymap.xml mappings
            data = query_oem_type_raw(type_id)

            # Only process if we got data
            if data:
                data = decode_bytes(data)  # Decode byte strings to regular strings
                all_data[type_id] = data
                oem_found += 1

                if output_format == 'text':
                    dump_type_text(type_id, data, show_raw)

        except Exception as e:
            # Silently skip types that don't exist or error
            logging.debug(f"Error querying OEM type {type_id}: {e}")
            continue

    log_messages_if_debug()

    if output_format == 'text':
        if oem_found == 0:
            print("\n  (No OEM-specific types found)")
            print("  This may indicate:")
            print("    - No OEM types exist on this system")
            print("    - The DMI data source doesn't contain OEM structures")
        else:
            print(f"\n  Total OEM types found: {oem_found}")

    if output_format == 'json':
        print(json.dumps(all_data, indent=2, default=str))
    elif output_format == 'python':
        pprint(all_data)

    return all_data


def print_summary():
    """Print a summary of available DMI information"""
    print("\n" + "=" * 70)
    print("DMI/SMBIOS INFORMATION SUMMARY")
    print("=" * 70)

    summary = {}

    # Get system info
    try:
        system_data = dmidecode.QuerySection('system')
        system_data = decode_bytes(system_data)  # Decode byte strings to regular strings
        for entry in system_data.values():
            if isinstance(entry, dict) and entry.get('dmi_type') == 1:
                data = entry.get('data', {})
                summary['Manufacturer'] = data.get('Manufacturer', 'Unknown')
                summary['Product Name'] = data.get('Product Name', 'Unknown')
                summary['Serial Number'] = data.get('Serial Number', 'Unknown')
                summary['UUID'] = data.get('UUID', 'Unknown')
                break
    except:
        pass

    # Get BIOS info
    try:
        bios_data = dmidecode.QuerySection('bios')
        bios_data = decode_bytes(bios_data)  # Decode byte strings to regular strings
        for entry in bios_data.values():
            if isinstance(entry, dict) and entry.get('dmi_type') == 0:
                data = entry.get('data', {})
                summary['BIOS Vendor'] = data.get('Vendor', 'Unknown')
                summary['BIOS Version'] = data.get('Version', 'Unknown')
                summary['BIOS Date'] = data.get('Release Date', 'Unknown')
                break
    except:
        pass

    # Get processor info
    try:
        proc_data = dmidecode.QuerySection('processor')
        proc_data = decode_bytes(proc_data)  # Decode byte strings to regular strings
        proc_count = 0
        for entry in proc_data.values():
            if isinstance(entry, dict) and entry.get('dmi_type') == 4:
                if proc_count == 0:
                    data = entry.get('data', {})
                    summary['Processor'] = data.get('Version', 'Unknown')
                proc_count += 1
        summary['Processor Count'] = proc_count
    except:
        pass

    # Get memory info
    try:
        mem_data = dmidecode.QuerySection('memory')
        mem_data = decode_bytes(mem_data)  # Decode byte strings to regular strings
        total_size = 0
        module_count = 0
        for entry in mem_data.values():
            if isinstance(entry, dict) and entry.get('dmi_type') == 17:
                data = entry.get('data', {})
                size_str = data.get('Size', '')
                if 'MB' in str(size_str):
                    try:
                        size_mb = int(str(size_str).split()[0])
                        total_size += size_mb
                        module_count += 1
                    except:
                        pass
                elif 'GB' in str(size_str):
                    try:
                        size_gb = int(str(size_str).split()[0])
                        total_size += size_gb * 1024
                        module_count += 1
                    except:
                        pass

        if total_size > 0:
            if total_size >= 1024:
                summary['Total Memory'] = f"{total_size / 1024:.1f} GB ({module_count} modules)"
            else:
                summary['Total Memory'] = f"{total_size} MB ({module_count} modules)"
    except:
        pass

    # Print summary
    for key, value in summary.items():
        print(f"  {key:20s}: {value}")

    print("=" * 70)
    log_messages_if_debug()


def main():
    parser = argparse.ArgumentParser(
        description='Dump all DMI/SMBIOS information from the system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dump all sections in text format
  sudo python3 dump_all_dmi.py

  # Dump specific sections only
  python3 dump_all_dmi.py --sections bios,system,processor

  # Dump all types (0-127 and OEM 128-255) instead of sections
  sudo python3 dump_all_dmi.py --all-types

  # Dump only OEM-specific types (128-255)
  sudo python3 dump_all_dmi.py --oem-only

  # Dump specific type IDs (including OEM types)
  sudo python3 dump_all_dmi.py --type 0,1,4,130,221

  # Dump all types but skip OEM types
  sudo python3 dump_all_dmi.py --all-types --no-oem

  # Output as JSON
  sudo python3 dump_all_dmi.py --format json > hardware.json

  # Show debug messages
  sudo python3 dump_all_dmi.py --debug

  # Create dump file for later use
  sudo python3 dump_all_dmi.py --create-dump

  # Use existing dump file
  python3 dump_all_dmi.py --dump-file dmidata.dump

Available sections: bios, system, baseboard, chassis, processor, memory, cache, connector, slot, power, security, management

DMI Type Ranges:
  0-46    : Standard SMBIOS types (defined by specification)
  47-127  : Reserved for future SMBIOS use
  128-255 : OEM-specific types (vendor-defined)
        """
    )

    parser.add_argument(
        '--format',
        choices=['text', 'json', 'python'],
        default='text',
        help='Output format (default: text)'
    )

    parser.add_argument(
        '--sections',
        help='Comma-separated list of sections to dump (default: all)'
    )

    parser.add_argument(
        '--all-types',
        action='store_true',
        help='Dump all DMI types (0-127 and OEM 128-255) instead of sections'
    )

    parser.add_argument(
        '--oem-only',
        action='store_true',
        help='Dump only OEM-specific types (128-255)'
    )

    parser.add_argument(
        '--no-oem',
        action='store_true',
        help='Exclude OEM types when using --all-types'
    )

    parser.add_argument(
        '--type',
        metavar='TYPE_IDS',
        help='Comma-separated list of specific type IDs to dump (e.g., 0,1,4,17,130)'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary of key hardware information'
    )

    parser.add_argument(
        '--raw',
        action='store_true',
        help='Show raw entry data (verbose)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show debug messages including SMBIOS version info'
    )

    parser.add_argument(
        '--dump-file',
        metavar='FILE',
        help='Use DMI dump file instead of reading from /dev/mem'
    )

    parser.add_argument(
        '--create-dump',
        action='store_true',
        help='Create a DMI dump file (dmidata.dump) and exit'
    )

    parser.add_argument(
        '--list-types',
        action='store_true',
        help='List all known DMI type IDs and names'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    # Handle --list-types first (doesn't need root or dump file)
    if args.list_types:
        print("\n" + "=" * 70)
        print("KNOWN DMI TYPE IDS")
        print("=" * 70)
        print("\nStandard SMBIOS Types (0-46):")
        for type_id in sorted(DMI_TYPES.keys()):
            if type_id <= 46:
                print(f"  {type_id:3d} (0x{type_id:02X}): {DMI_TYPES[type_id]}")
        print("\nSpecial Types:")
        for type_id in sorted(DMI_TYPES.keys()):
            if type_id > 46:
                print(f"  {type_id:3d} (0x{type_id:02X}): {DMI_TYPES[type_id]}")
        print("\nKnown OEM Types (128-255):")
        for type_id in sorted(OEM_TYPES.keys()):
            print(f"  {type_id:3d} (0x{type_id:02X}): {OEM_TYPES[type_id]}")
        print("\nNote: Types 47-127 are reserved for future SMBIOS use.")
        print("      Types 128-255 are OEM-specific and vary by vendor.")
        return 0

    # Handle dump file
    if args.dump_file:
        print(f"Using DMI dump file: {args.dump_file}")
        dmidecode.set_dev(args.dump_file)
    else:
        is_root = check_root()

    # Create dump and exit if requested
    if args.create_dump:
        if not args.dump_file:
            if os.getuid() != 0:
                print("ERROR: Must be root to create dump from /dev/mem")
                return 1
        create_dump()
        return 0

    # Show summary if requested
    if args.summary:
        print_summary()
        return 0

    # Parse sections
    sections = None
    if args.sections:
        sections = [s.strip() for s in args.sections.split(',')]
        # Validate sections
        invalid = [s for s in sections if s not in DMI_SECTIONS]
        if invalid:
            print(f"ERROR: Invalid sections: {', '.join(invalid)}")
            print(f"Valid sections: {', '.join(DMI_SECTIONS.keys())}")
            return 1

    # Parse specific type IDs if provided
    specific_types = None
    if args.type:
        try:
            specific_types = [int(t.strip()) for t in args.type.split(',')]
            # Validate type IDs
            invalid = [t for t in specific_types if t < 0 or t > 255]
            if invalid:
                print(f"ERROR: Invalid type IDs: {invalid}")
                print("Type IDs must be between 0 and 255")
                return 1
        except ValueError as e:
            print(f"ERROR: Invalid type ID format: {e}")
            print("Use comma-separated integers (e.g., 0,1,4,17,130)")
            return 1

    # Dump data
    try:
        if specific_types:
            # Dump specific type IDs
            all_data = {}
            print("\n" + "=" * 70)
            print(f"DUMPING SPECIFIC DMI TYPES: {specific_types}")
            print("=" * 70)

            for type_id in specific_types:
                try:
                    # Use XML fallback for OEM types (128-255)
                    if is_oem_type(type_id):
                        data = query_oem_type_raw(type_id)
                    else:
                        data = dmidecode.QueryTypeId(type_id)

                    if data:
                        data = decode_bytes(data)
                        all_data[type_id] = data
                        if args.format == 'text':
                            dump_type_text(type_id, data, args.raw)
                except Exception as e:
                    if args.debug:
                        print(f"  (Type {type_id} not available: {e})")
                    continue

            log_messages_if_debug()

            if args.format == 'json':
                print(json.dumps(all_data, indent=2, default=str))
            elif args.format == 'python':
                pprint(all_data)

        elif args.oem_only:
            # Dump only OEM types
            dump_oem_types_only(args.format, args.raw)

        elif args.all_types:
            # Dump all types (optionally excluding OEM)
            include_oem = not args.no_oem
            dump_all_types(args.format, args.raw, include_oem)

        else:
            # Dump by sections (default behavior)
            dump_all_sections(args.format, sections, args.raw)

        # Show summary at the end for text format
        if args.format == 'text' and not args.summary and not args.oem_only:
            print_summary()

        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())