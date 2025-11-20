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
Comprehensive DMI Data Dumper

This script queries and displays ALL available DMI/SMBIOS information from your system.
It can output data in multiple formats and provides complete hardware inventory.

Usage:
    # Basic usage (must be run as root on first run)
    sudo python3 dump_all_dmi.py

    # Output as JSON
    sudo python3 dump_all_dmi.py --format json > hardware.json

    # Output specific sections only
    python3 dump_all_dmi.py --sections bios,system,processor

    # Show debug messages
    python3 dump_all_dmi.py --debug

    # Use existing dump file (no root needed)
    python3 dump_all_dmi.py --dump-file /path/to/dmidata.dump
"""

import dmidecode
import sys
import os
import json
import logging
import argparse
from pprint import pprint

# DMI Type ID to Name mapping (SMBIOS specification)
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
}

# DMI Section names and their included types
DMI_SECTIONS = {
    'bios': (0, 13),
    'system': (1, 12, 15, 23, 32),
    'baseboard': (2, 10),
    'chassis': (3,),
    'processor': (4,),
    'memory': (5, 6, 16, 17),
    'cache': (7,),
    'connector': (8,),
    'slot': (9,),
}


def setup_logging(debug=False):
    """Configure logging based on debug flag"""
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )
    dmidecode.enable_auto_logging(level)


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
    dmidecode.log_messages()


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
        type_name = DMI_TYPES.get(dmi_type, f"Type {dmi_type}")

        print(f"\nHandle: {handle}")
        print(f"Type: {dmi_type} ({type_name})")

        if 'data' in entry and isinstance(entry['data'], dict):
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


def dump_type_text(type_id, data, show_raw=False):
    """Dump a specific DMI type in human-readable text format"""
    type_name = DMI_TYPES.get(type_id, f"Unknown Type {type_id}")

    print("\n" + "=" * 70)
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
        print(f"\n[{count}] Handle: {handle}")

        if 'data' in entry and isinstance(entry['data'], dict):
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

    print(f"\nTotal {type_name} entries: {count}")


def dump_all_sections(output_format='text', sections=None, show_raw=False):
    """Dump all DMI sections"""
    all_data = {}

    if sections is None:
        sections = list(DMI_SECTIONS.keys())

    for section in sections:
        try:
            data = dmidecode.QuerySection(section)
            all_data[section] = data

            if output_format == 'text':
                dump_section_text(section, data, show_raw)

        except Exception as e:
            print(f"Error querying section '{section}': {e}")
            continue

    dmidecode.log_messages()

    if output_format == 'json':
        print(json.dumps(all_data, indent=2, default=str))
    elif output_format == 'python':
        pprint(all_data)

    return all_data


def dump_all_types(output_format='text', show_raw=False):
    """Dump all DMI types individually"""
    all_data = {}

    print("\n" + "=" * 70)
    print("DUMPING ALL DMI TYPES (0-43)")
    print("=" * 70)

    for type_id in range(44):  # DMI types 0-43
        try:
            data = dmidecode.QueryTypeId(type_id)

            # Only process if we got data
            if data:
                all_data[type_id] = data

                if output_format == 'text':
                    dump_type_text(type_id, data, show_raw)

        except Exception as e:
            # Silently skip types that don't exist
            continue

    dmidecode.log_messages()

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
    dmidecode.log_messages()


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

  # Dump all types (0-43) instead of sections
  sudo python3 dump_all_dmi.py --all-types

  # Output as JSON
  sudo python3 dump_all_dmi.py --format json > hardware.json

  # Show debug messages
  sudo python3 dump_all_dmi.py --debug

  # Create dump file for later use
  sudo python3 dump_all_dmi.py --create-dump

  # Use existing dump file
  python3 dump_all_dmi.py --dump-file dmidata.dump

Available sections: bios, system, baseboard, chassis, processor, memory, cache, connector, slot
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
        help='Dump all DMI types (0-43) instead of sections'
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

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

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

    # Dump data
    try:
        if args.all_types:
            dump_all_types(args.format, args.raw)
        else:
            dump_all_sections(args.format, sections, args.raw)

        # Show summary at the end for text format
        if args.format == 'text' and not args.summary:
            print_summary()

        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
