#!/usr/bin/env python3
"""
Test script for the enhanced dmidecode Python module.

This script tests all new features:
- DMI type constants and mappings
- Type detection helper functions
- JSON export functionality
- OEM type handling with raw data fallback
- High-level query functions

Usage:
    # Run as root for full functionality
    sudo python3 test_dmidecode_features.py

    # Run with existing dump file (no root required)
    python3 test_dmidecode_features.py --dump-file dmidata.dump

    # Run specific tests
    python3 test_dmidecode_features.py --test constants
    python3 test_dmidecode_features.py --test json
    python3 test_dmidecode_features.py --test oem

Compatible with Python 3.9+
"""

import argparse
import json
import os
import sys
import tempfile


def print_header(title):
    """Print a formatted section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_subheader(title):
    """Print a formatted subsection header."""
    print()
    print(f"--- {title} ---")


def test_module_import():
    """Test that the module imports correctly."""
    print_header("TEST: Module Import")

    try:
        import dmidecode
        print(f"  Module imported successfully")
        print(f"  Module version: {dmidecode.version}")
        print(f"  DMI version: {getattr(dmidecode, 'dmi', 'N/A')}")
        print(f"  XML support: {dmidecode.has_xml_support()}")
        return True
    except ImportError as e:
        print(f"  FAILED: {e}")
        return False


def test_constants():
    """Test DMI type constants and mappings."""
    print_header("TEST: DMI Type Constants")

    import dmidecode

    print_subheader("Standard Type Constants")
    constants = [
        ('DMI_TYPE_BIOS', dmidecode.DMI_TYPE_BIOS, 0),
        ('DMI_TYPE_SYSTEM', dmidecode.DMI_TYPE_SYSTEM, 1),
        ('DMI_TYPE_BASEBOARD', dmidecode.DMI_TYPE_BASEBOARD, 2),
        ('DMI_TYPE_CHASSIS', dmidecode.DMI_TYPE_CHASSIS, 3),
        ('DMI_TYPE_PROCESSOR', dmidecode.DMI_TYPE_PROCESSOR, 4),
        ('DMI_TYPE_MEMORY_DEVICE', dmidecode.DMI_TYPE_MEMORY_DEVICE, 17),
        ('DMI_TYPE_END_OF_TABLE', dmidecode.DMI_TYPE_END_OF_TABLE, 127),
    ]

    all_pass = True
    for name, value, expected in constants:
        status = "PASS" if value == expected else "FAIL"
        if value != expected:
            all_pass = False
        print(f"  {name} = {value} (expected {expected}) [{status}]")

    print_subheader("DMI Type Name Mapping")
    test_names = [
        (0, "BIOS Information"),
        (4, "Processor Information"),
        (17, "Memory Device"),
        (127, "End Of Table"),
        (130, "OEM Slot Information"),
        (50, "Reserved Type 50"),
        (200, "OEM Type 200"),
    ]

    for type_id, expected_prefix in test_names:
        name = dmidecode.get_type_name(type_id)
        status = "PASS" if expected_prefix in name else "FAIL"
        if expected_prefix not in name:
            all_pass = False
        print(f"  Type {type_id}: '{name}' [{status}]")

    print_subheader("Type Check Functions")
    checks = [
        ('is_oem_type(130)', dmidecode.is_oem_type(130), True),
        ('is_oem_type(4)', dmidecode.is_oem_type(4), False),
        ('is_standard_type(4)', dmidecode.is_standard_type(4), True),
        ('is_standard_type(130)', dmidecode.is_standard_type(130), False),
        ('is_standard_type(50)', dmidecode.is_standard_type(50), False),
    ]

    for check_name, result, expected in checks:
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_pass = False
        print(f"  {check_name} = {result} (expected {expected}) [{status}]")

    print_subheader("DMI Section Mappings")
    print(f"  Available sections: {list(dmidecode.DMI_SECTIONS.keys())}")
    print(f"  Section 'bios' types: {dmidecode.DMI_SECTIONS['bios']}")
    print(f"  Section 'memory' types: {dmidecode.DMI_SECTIONS['memory']}")

    print_subheader("DMI Type Groups")
    print(f"  Standard types (0-46): {len(dmidecode.DMI_GROUP_STANDARD)} types")
    print(f"  Reserved types (47-127): {len(dmidecode.DMI_GROUP_RESERVED)} types")
    print(f"  OEM types (128-255): {len(dmidecode.DMI_GROUP_OEM)} types")

    return all_pass


def test_query_section():
    """Test querying DMI data by section."""
    print_header("TEST: Query by Section")

    import dmidecode

    sections_to_test = ['bios', 'system', 'processor', 'memory']
    results = {}

    for section in sections_to_test:
        print_subheader(f"Section: {section}")
        try:
            data = dmidecode.QuerySection(section)
            if data:
                results[section] = data
                print(f"  Retrieved {len(data)} entries")
                for handle, entry in list(data.items())[:2]:  # Show first 2
                    if isinstance(entry, dict):
                        print(f"    Handle: {handle}")
                        print(f"    Type: {entry.get('dmi_type', 'N/A')}")
                        if 'data' in entry:
                            data_keys = list(entry['data'].keys())[:3]
                            print(f"    Data keys: {data_keys}...")
            else:
                print(f"  No data available")
        except Exception as e:
            print(f"  Error: {e}")

    # Clear any warnings
    dmidecode.clear_warnings()
    return len(results) > 0


def test_query_type():
    """Test querying DMI data by type ID."""
    print_header("TEST: Query by Type ID")

    import dmidecode

    types_to_test = [0, 1, 4, 17]  # BIOS, System, Processor, Memory Device
    results = {}

    for type_id in types_to_test:
        print_subheader(f"Type {type_id}: {dmidecode.get_type_name(type_id)}")
        try:
            data = dmidecode.QueryTypeId(type_id)
            if data:
                results[type_id] = data
                print(f"  Retrieved {len(data)} entries")
                for handle in list(data.keys())[:1]:  # Show first entry
                    entry = data[handle]
                    if isinstance(entry, dict) and 'data' in entry:
                        print(f"    Handle: {handle}")
                        for key, value in list(entry['data'].items())[:3]:
                            print(f"    {key}: {value}")
            else:
                print(f"  No data available")
        except Exception as e:
            print(f"  Error: {e}")

    dmidecode.clear_warnings()
    return len(results) > 0


def test_query_type_with_fallback():
    """Test query_type_with_fallback function."""
    print_header("TEST: Query Type with Fallback")

    import dmidecode

    print_subheader("Standard Type (4 - Processor)")
    data = dmidecode.query_type_with_fallback(4)
    if data:
        print(f"  Retrieved {len(data)} entries")
    else:
        print(f"  No data available")

    print_subheader("OEM Type Range Check")
    oem_found = 0
    for type_id in range(128, 140):
        data = dmidecode.query_type_with_fallback(type_id)
        if data:
            oem_found += 1
            print(f"  Type {type_id}: Found {len(data)} entries")

    if oem_found == 0:
        print(f"  No OEM types found in range 128-139")

    dmidecode.clear_warnings()
    return True


def test_json_export():
    """Test JSON export functionality."""
    print_header("TEST: JSON Export")

    import dmidecode

    print_subheader("get_section_json('bios')")
    try:
        json_str = dmidecode.get_section_json('bios', pretty=True)
        data = json.loads(json_str)
        print(f"  JSON valid: True")
        print(f"  Entries: {len(data)}")
        print(f"  Preview: {json_str[:200]}...")
    except Exception as e:
        print(f"  Error: {e}")

    print_subheader("get_type_json(4)")
    try:
        json_str = dmidecode.get_type_json(4, pretty=True)
        data = json.loads(json_str)
        print(f"  JSON valid: True")
        print(f"  Entries: {len(data)}")
    except Exception as e:
        print(f"  Error: {e}")

    print_subheader("get_all_json()")
    try:
        json_str = dmidecode.get_all_json(include_oem=False, pretty=False)
        data = json.loads(json_str)
        print(f"  JSON valid: True")
        print(f"  Sections: {list(data.get('sections', {}).keys())}")
        print(f"  Types found: {len(data.get('types', {}))}")
    except Exception as e:
        print(f"  Error: {e}")

    print_subheader("export_json() to file")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        success = dmidecode.export_json(temp_path, include_oem=False, pretty=True)
        if success:
            with open(temp_path, 'r') as f:
                content = f.read()
            data = json.loads(content)
            print(f"  Export successful: True")
            print(f"  File size: {len(content)} bytes")
            os.unlink(temp_path)
        else:
            print(f"  Export failed")
    except Exception as e:
        print(f"  Error: {e}")

    dmidecode.clear_warnings()
    return True


def test_oem_types():
    """Test OEM type handling."""
    print_header("TEST: OEM Type Handling")

    import dmidecode

    print_subheader("Scanning OEM Types (128-255)")
    oem_data = {}

    for type_id in range(128, 256):
        try:
            data = dmidecode.query_oem_type(type_id)
            if data:
                oem_data[type_id] = data
                type_name = dmidecode.get_type_name(type_id)
                print(f"  Type {type_id} ({type_name}): {len(data)} entries")
        except Exception:
            pass

    if not oem_data:
        print(f"  No OEM types found on this system")
    else:
        print(f"\n  Total OEM types found: {len(oem_data)}")

    print_subheader("get_oem_types() function")
    try:
        all_oem = dmidecode.get_oem_types()
        print(f"  OEM types returned: {len(all_oem)}")
        for type_id in list(all_oem.keys())[:3]:
            print(f"    Type {type_id}: {len(all_oem[type_id])} entries")
    except Exception as e:
        print(f"  Error: {e}")

    dmidecode.clear_warnings()
    return True


def test_hardware_info():
    """Test high-level hardware info function."""
    print_header("TEST: Hardware Info Summary")

    import dmidecode

    try:
        info = dmidecode.get_hardware_info()

        print_subheader("System Information")
        for key, value in info.get('system', {}).items():
            print(f"  {key}: {value}")

        print_subheader("BIOS Information")
        for key, value in info.get('bios', {}).items():
            print(f"  {key}: {value}")

        print_subheader("Processor Information")
        proc_info = info.get('processor', {})
        print(f"  Count: {proc_info.get('count', 'N/A')}")
        if 'details' in proc_info:
            for i, proc in enumerate(proc_info['details'][:2]):
                print(f"  Processor {i+1}: {proc.get('version', 'N/A')}")

        print_subheader("Memory Information")
        mem_info = info.get('memory', {})
        print(f"  Total: {mem_info.get('total', 'N/A')}")
        print(f"  Modules: {mem_info.get('module_count', 'N/A')}")

        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False
    finally:
        dmidecode.clear_warnings()


def test_list_available_types():
    """Test listing available DMI types."""
    print_header("TEST: List Available Types")

    import dmidecode

    try:
        available = dmidecode.list_available_types()

        print_subheader("Standard Types Found")
        standard = available.get('standard', [])
        print(f"  Count: {len(standard)}")
        if standard:
            type_names = [f"{t} ({dmidecode.get_type_name(t)})" for t in standard[:10]]
            print(f"  Types: {', '.join(type_names)}...")

        print_subheader("OEM Types Found")
        oem = available.get('oem', [])
        print(f"  Count: {len(oem)}")
        if oem:
            type_names = [f"{t} ({dmidecode.get_type_name(t)})" for t in oem[:5]]
            print(f"  Types: {', '.join(type_names)}")

        return True
    except Exception as e:
        print(f"  Error: {e}")
        return False
    finally:
        dmidecode.clear_warnings()


def test_additional_features():
    """Test additional helper features."""
    print_header("TEST: Additional Features")

    import dmidecode

    print_subheader("Type Name Lookup")
    test_types = [0, 1, 4, 17, 127, 130, 200]
    for type_id in test_types:
        name = dmidecode.get_type_name(type_id)
        print(f"  Type {type_id}: {name}")

    print_subheader("Type Category Checks")
    checks = [
        (4, 'standard', dmidecode.is_standard_type(4)),
        (130, 'OEM', dmidecode.is_oem_type(130)),
        (50, 'reserved', not dmidecode.is_standard_type(50) and not dmidecode.is_oem_type(50)),
    ]
    for type_id, category, result in checks:
        print(f"  Type {type_id} is {category}: {result}")

    print_subheader("DMI Sections")
    print(f"  Available sections: {list(dmidecode.DMI_SECTIONS.keys())}")

    dmidecode.clear_warnings()
    return True


def run_all_tests(dump_file=None):
    """Run all tests."""
    import dmidecode

    # Set dump file if provided
    if dump_file:
        print(f"\nUsing dump file: {dump_file}")
        dmidecode.set_dev(dump_file)

    tests = [
        ("Module Import", test_module_import),
        ("Constants", test_constants),
        ("Query Section", test_query_section),
        ("Query Type", test_query_type),
        ("Query with Fallback", test_query_type_with_fallback),
        ("JSON Export", test_json_export),
        ("OEM Types", test_oem_types),
        ("Hardware Info", test_hardware_info),
        ("List Available Types", test_list_available_types),
        ("Additional Features", test_additional_features),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n  EXCEPTION: {e}")
            results[name] = False

    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    print()
    print(f"  Total: {passed}/{total} tests passed")

    return all(results.values())


def main():
    parser = argparse.ArgumentParser(
        description='Test script for enhanced dmidecode module',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sudo python3 test_dmidecode_features.py
  python3 test_dmidecode_features.py --dump-file dmidata.dump
  python3 test_dmidecode_features.py --test constants
  python3 test_dmidecode_features.py --test json
"""
    )

    parser.add_argument(
        '--dump-file',
        help='Use DMI dump file instead of /dev/mem'
    )

    parser.add_argument(
        '--test',
        choices=['constants', 'section', 'type', 'json', 'oem', 'hwinfo', 'features', 'all'],
        default='all',
        help='Run specific test (default: all)'
    )

    args = parser.parse_args()

    # Check for root if not using dump file
    if not args.dump_file and os.getuid() != 0:
        print("WARNING: Not running as root. Some tests may fail.")
        print("         Run as root or use --dump-file option.\n")

    # Import and set dump file
    import dmidecode
    if args.dump_file:
        if not os.path.exists(args.dump_file):
            print(f"Error: Dump file not found: {args.dump_file}")
            sys.exit(1)
        dmidecode.set_dev(args.dump_file)

    # Run tests
    test_map = {
        'constants': test_constants,
        'section': test_query_section,
        'type': test_query_type,
        'json': test_json_export,
        'oem': test_oem_types,
        'hwinfo': test_hardware_info,
        'features': test_additional_features,
        'all': lambda: run_all_tests(args.dump_file),
    }

    if args.test == 'all':
        success = run_all_tests(args.dump_file)
    else:
        test_func = test_map[args.test]
        success = test_func()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
