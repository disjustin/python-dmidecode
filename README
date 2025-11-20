# python-dmidecode

Python extension module for extracting hardware information from DMI/SMBIOS data structures.

## Description

python-dmidecode is a Python extension module that provides access to Desktop Management Interface (DMI) and System Management BIOS (SMBIOS) data. DMI/SMBIOS is a standard mechanism for system hardware and firmware to communicate their characteristics to system management software. This module allows Python scripts to query detailed hardware information without needing to parse the output of command-line tools.

The module provides both a Python dictionary-based API and an XML-based API using libxml2, giving developers flexibility in how they process hardware information. Data can be queried by DMI section names (bios, system, baseboard, chassis, processor, memory, cache, connector, slot) or by specific DMI type IDs (0-43).

## Features

- **Direct DMI/SMBIOS Access**: Read hardware information directly from /dev/mem or from dump files
- **Multiple Query Methods**: Query by section name or DMI type ID
- **Dual API Support**:
  - Python dictionary API for easy native Python processing
  - XML API (libxml2) for structured data export and XPath queries
- **DMI Data Dumping**: Create dump files for offline analysis or testing
- **Comprehensive Hardware Coverage**: Access BIOS, system, baseboard, chassis, processor, memory, cache, and more
- **Root and Non-Root Support**: First run as root to create dump, subsequent runs can be non-root
- **Cross-Platform**: Works on Linux and has been reported to work on FreeBSD, NetBSD, OpenBSD, Solaris

## Requirements

### Build Requirements
- Python 3.x (Python 2.7+ also supported)
- GCC or compatible C compiler
- libxml2 development headers (libxml2-dev or libxml2-devel)
- make

### Runtime Requirements
- Python 3.x (or Python 2.7+)
- libxml2
- Root privileges (for initial DMI data access from /dev/mem)

## Installation

### From Source

1. Clone or download the repository:
```bash
git clone https://github.com/nima/python-dmidecode.git
cd python-dmidecode
```

2. Build the extension module:
```bash
make
```

3. Install (requires root):
```bash
sudo make install
```

### Uninstall
```bash
sudo make uninstall
```

### Building RPM Package
```bash
make tarball
make rpm
```

## Usage

### Basic Usage - Python Dictionary API

**Important**: The first run must be executed as root to access /dev/mem:

```python
#!/usr/bin/env python3
import dmidecode

# Query specific sections (returns dictionary)
bios_info = dmidecode.QuerySection('bios')
system_info = dmidecode.QuerySection('system')
processor_info = dmidecode.QuerySection('processor')
memory_info = dmidecode.QuerySection('memory')

# Print system manufacturer and model
for key, value in system_info.items():
    if isinstance(value, dict) and value.get('dmi_type') == 1:
        print(f"Manufacturer: {value['data']['Manufacturer']}")
        print(f"Product Name: {value['data']['Product Name']}")
        print(f"Serial Number: {value['data']['Serial Number']}")
        print(f"UUID: {value['data']['UUID']}")
```

### Query by DMI Type ID

```python
import dmidecode

# Query by specific DMI type ID
# Type 3 = Chassis Information
chassis = dmidecode.QueryTypeId(3)

# Type 4 = Processor Information
processor = dmidecode.QueryTypeId(4)

# Type 17 = Memory Device
memory_devices = dmidecode.QueryTypeId(17)
```

### Available Sections

| Section Name | DMI Types | Information |
|-------------|-----------|-------------|
| bios | 0, 13 | BIOS information and language |
| system | 1, 12, 15, 23, 32 | System information, configuration, event log |
| baseboard | 2, 10 | Base board and onboard devices |
| chassis | 3 | Chassis information |
| processor | 4 | Processor information |
| memory | 5, 6, 16, 17 | Memory controller and modules |
| cache | 7 | Cache information |
| connector | 8 | Port connectors |
| slot | 9 | System slots |

### DMI Type Reference

See doc/README.types for a complete list of DMI type IDs (0-43).

### Creating and Using DMI Dumps

DMI dumps allow you to:
- Test scripts without root access after initial dump
- Archive hardware configurations
- Analyze hardware offline

```python
import dmidecode

# Set dump file location (default: 'dmidata.dump' in current directory)
dmidecode.set_dev('my_hardware.dump')

# Create dump (requires root privileges)
dmidecode.dump()

# Now you can query from the dump file (no root needed)
bios = dmidecode.QuerySection('bios')
```

### Advanced Usage - XML API

The XML API provides structured data access using libxml2:

```python
import dmidecode

# Create dmidecode XML object
dmixml = dmidecode.dmidecodeXML()

# Set result type: DMIXML_DOC (document) or DMIXML_NODE (node)
dmixml.SetResultType(dmidecode.DMIXML_DOC)

# Query all DMI data as XML document
xmldoc = dmixml.QuerySection('all')

# Save to file
xmldoc.saveFormatFileEnc('hardware_info.xml', 'UTF-8', 1)

# XPath queries
xpathctx = xmldoc.xpathNewContext()

# Query specific hardware details
manufacturer = xpathctx.xpathEval('/dmidecode/SystemInfo/Manufacturer')
product_name = xpathctx.xpathEval('/dmidecode/SystemInfo/ProductName')
serial = xpathctx.xpathEval('/dmidecode/SystemInfo/SerialNumber')
uuid = xpathctx.xpathEval('/dmidecode/SystemInfo/SystemUUID')

for node in manufacturer:
    print(f"Manufacturer: {node.get_content()}")

# Query by type ID
processor_xml = dmixml.QueryTypeId(0x04)  # Processor
processor_xml.saveFormatFileEnc('-', 'UTF-8', 1)  # Print to stdout

# Cleanup
del xpathctx
del xmldoc
```

### Handling Warnings and Debug Messages

```python
import dmidecode
import logging

# Method 1: Automatic logging (recommended)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
dmidecode.enable_auto_logging(logging.DEBUG)

# Now all operations automatically log warnings and debug messages
data = dmidecode.QuerySection('bios')
# Debug messages (SMBIOS version, entry points) logged automatically


# Method 2: Manual warning/debug handling
def print_warnings():
    """Check for and print any warnings"""
    warn = dmidecode.get_warnings()
    if warn:
        print(f"WARNING: {warn}")
        dmidecode.clear_warnings()

def print_debug():
    """Check for and print debug messages"""
    debug = dmidecode.get_debug()
    if debug:
        print(f"DEBUG: {debug}")
        dmidecode.clear_debug()

# Query data
data = dmidecode.QuerySection('bios')
print_warnings()
print_debug()


# Method 3: Use log_messages() helper
dmidecode.enable_auto_logging(logging.WARNING)  # Auto-log warnings only
data = dmidecode.QuerySection('system')
dmidecode.log_messages()  # Manually trigger logging
```

### Legacy API (Deprecated)

The module also supports legacy function calls for backward compatibility:

```python
import dmidecode

# Legacy API - returns None, data accessed via internal state
dmidecode.bios()
dmidecode.system()
dmidecode.baseboard()
dmidecode.chassis()
dmidecode.processor()
dmidecode.memory()
dmidecode.cache()
dmidecode.connector()
dmidecode.slot()

# Legacy type query
dmidecode.type(3)  # Use QueryTypeId(3) instead
```

**Note**: The legacy API is maintained for backward compatibility. New code should use `QuerySection()` and `QueryTypeId()`.

### Practical Example: Memory Information

```python
#!/usr/bin/env python3
import dmidecode

# Get all memory information
memory_data = dmidecode.QuerySection('memory')

# Extract installed memory modules (Type 17)
print("Installed Memory:")
for key, value in memory_data.items():
    if isinstance(value, dict) and value.get('dmi_type') == 17:
        data = value.get('data', {})
        size = data.get('Size', 'Unknown')
        speed = data.get('Speed', 'Unknown')
        manufacturer = data.get('Manufacturer', 'Unknown')
        part_number = data.get('Part Number', 'Unknown')

        print(f"  Size: {size}")
        print(f"  Speed: {speed}")
        print(f"  Manufacturer: {manufacturer}")
        print(f"  Part Number: {part_number}")
        print()
```

## API Reference

### Main Functions

#### `QuerySection(section_name)`
Query DMI data by section name.
- **Parameters**: section_name (str) - One of: 'all', 'bios', 'system', 'baseboard', 'chassis', 'processor', 'memory', 'cache', 'connector', 'slot'
- **Returns**: Dictionary containing DMI data
- **Raises**: Exception on error

#### `QueryTypeId(type_id)`
Query DMI data by type ID.
- **Parameters**: type_id (int) - DMI type ID (0-43)
- **Returns**: Dictionary containing DMI data for specified type
- **Raises**: Exception on error

#### `dump()`
Create a dump of DMI data to file.
- **Returns**: Status string
- **Requires**: Root privileges
- **Note**: Writes to file specified by set_dev() or default 'dmidata.dump'

#### `set_dev(device)`
Set the device/file to read DMI data from.
- **Parameters**: device (str) - Path to /dev/mem or dump file
- **Returns**: Status

#### `get_dev()`
Get the current device/file path.
- **Returns**: String path to current device

#### `get_warnings()`
Get any warnings generated during DMI operations.
- **Returns**: String with warnings or None

#### `clear_warnings()`
Clear the warning buffer.

#### `get_debug()`
Get any debug messages generated during DMI operations.
- **Returns**: String with debug messages or None
- **Note**: Debug messages include SMBIOS entry points, version info, structure counts

#### `clear_debug()`
Clear the debug message buffer.

#### `enable_auto_logging(level=logging.WARNING)`
Enable automatic logging of warnings and debug messages using Python's logging module.
- **Parameters**: level (int) - Logging level (logging.WARNING or logging.DEBUG)
- **Note**: Requires `import logging` and logging configuration
- **Example**:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  dmidecode.enable_auto_logging(logging.DEBUG)
  ```

#### `disable_auto_logging()`
Disable automatic logging of warnings and debug messages.

#### `log_messages()`
Manually log any warnings and debug messages from the last operation.
- **Note**: Automatically called after operations if `enable_auto_logging()` was used

### XML API

#### `dmidecodeXML()`
Create XML API object.

#### `SetResultType(type)`
Set XML result type.
- **Parameters**: type - dmidecode.DMIXML_DOC or dmidecode.DMIXML_NODE

#### `QuerySection(section_name)`
Query section, return as libxml2 object.
- **Returns**: libxml2.xmlDoc or libxml2.xmlNode

#### `QueryTypeId(type_id)`
Query type ID, return as libxml2 object.
- **Returns**: libxml2.xmlDoc or libxml2.xmlNode

## Examples

See the `examples/` directory for complete working examples:

### dump_all_dmi.py - Comprehensive DMI Data Dumper

A powerful script that outputs ALL available DMI/SMBIOS information in multiple formats:

```bash
# Basic usage - dump all sections
sudo python3 examples/dump_all_dmi.py

# Show only summary
sudo python3 examples/dump_all_dmi.py --summary

# Dump specific sections only
python3 examples/dump_all_dmi.py --sections bios,system,processor

# Dump all DMI types (0-43) individually
sudo python3 examples/dump_all_dmi.py --all-types

# Output as JSON
sudo python3 examples/dump_all_dmi.py --format json > hardware.json

# Output as Python dict
sudo python3 examples/dump_all_dmi.py --format python

# Show debug messages (SMBIOS version, entry points, etc.)
sudo python3 examples/dump_all_dmi.py --debug

# Create dump file for non-root usage
sudo python3 examples/dump_all_dmi.py --create-dump
python3 examples/dump_all_dmi.py --dump-file dmidata.dump

# Show raw entry data (very verbose)
sudo python3 examples/dump_all_dmi.py --raw
```

**Features:**
- Dumps all DMI sections: bios, system, baseboard, chassis, processor, memory, cache, connector, slot
- Can dump all 44 DMI types (0-43) individually
- Multiple output formats: text (human-readable), JSON, Python dict
- Hardware summary with key information
- Supports DMI dump files for non-root usage
- Integrated with Python logging for debug messages
- Comprehensive error handling

### dmidump.py - API Feature Demonstration

Original example demonstrating all python-dmidecode features including XML API:

```bash
# Comprehensive API demonstration
sudo python3 examples/dmidump.py
```

## Testing

Run the included unit tests:
```bash
make unit
```

## Troubleshooting

### Permission Denied Errors
- Solution: Run as root or create a dump file as root first, then use dump file

### "No SMBIOS nor DMI entry point found"
- Your system may not have DMI/SMBIOS support
- Try checking if /dev/mem is accessible

### Module Import Error
- Ensure the module is installed: `sudo make install`
- Check Python version compatibility
- Verify libxml2 is installed

## Suggestions for Improvement

### High Priority
1. **Python Package Distribution**
   - Publish to PyPI for easy `pip install python-dmidecode`
   - Add setup.py wheel support for binary distributions
   - Consider creating conda packages

2. **Modern Python Support**
   - Add Python type hints throughout the codebase
   - Improve Python 3.8+ compatibility
   - Add dataclass representations of DMI structures

3. **Documentation**
   - Add comprehensive docstrings to all Python functions
   - Create Sphinx documentation
   - Add more code examples for common use cases
   - Document all DMI type structures

4. **API Improvements**
   - Add context manager support for automatic cleanup
   - Create higher-level OOP interface (classes for System, Processor, Memory, etc.)
   - Add JSON export capability alongside XML
   - Return typed objects instead of raw dictionaries

### Medium Priority
5. **Testing**
   - Expand unit test coverage
   - Add integration tests
   - Create CI/CD pipeline (GitHub Actions)
   - Add type checking with mypy
   - Add linting with ruff/pylint

6. **Error Handling**
   - Better exception hierarchy
   - More descriptive error messages
   - Validation of DMI data
   - Graceful degradation on partial failures

7. **Performance**
   - Cache parsed DMI data
   - Lazy loading of DMI sections
   - Optimize XML parsing

8. **Security**
   - Add option to run with reduced privileges using capabilities
   - Validate all input from DMI structures
   - Add fuzzing tests for C extension

### Low Priority
9. **Features**
   - Support for UEFI systems
   - Diff capability for comparing hardware configurations
   - Export to multiple formats (JSON, YAML, CSV)
   - Pretty-print formatters
   - Command-line tool wrapper

10. **Compatibility**
    - Test on more platforms (BSD variants, Solaris)
    - ARM architecture support
    - Windows support investigation
    - Container environment compatibility

11. **Developer Experience**
    - Add pre-commit hooks
    - Modernize build system (consider meson or cmake)
    - Add debugging utilities
    - Improve development documentation

## TODO

### Short Term
- [ ] Create comprehensive unit tests for all DMI types
- [ ] Add GitHub Actions CI/CD pipeline
- [ ] Write Sphinx documentation
- [ ] Add Python type hints to dmidecode.py
- [ ] Create PyPI package and publish
- [ ] Add JSON export functionality
- [ ] Improve error messages and exception handling
- [ ] Create object-oriented API layer
- [ ] Add examples for all DMI sections
- [ ] Document all supported DMI structures

### Medium Term
- [ ] Add context manager support for resource cleanup
- [ ] Create dataclass models for DMI structures
- [ ] Implement caching mechanism for performance
- [ ] Add command-line interface tool
- [ ] Support Python 3.12+ features
- [ ] Add fuzzing tests for C extension
- [ ] Create comparison/diff functionality
- [ ] Add YAML export capability
- [ ] Implement lazy loading for large DMI datasets
- [ ] Add validation for DMI data integrity

### Long Term
- [ ] Support for UEFI firmware interfaces
- [ ] Cross-platform support (Windows, macOS)
- [ ] Performance optimization for large systems
- [ ] Plugin system for custom DMI parsers
- [ ] Web-based hardware inventory tool
- [ ] Database storage backend option
- [ ] REST API wrapper
- [ ] Hardware change detection/monitoring
- [ ] Integration with configuration management tools (Ansible, Puppet)
- [ ] Container/VM detection and handling

### Infrastructure
- [ ] Migrate to modern build system (meson/cmake)
- [ ] Set up code coverage reporting
- [ ] Add static analysis tools
- [ ] Create contribution guidelines
- [ ] Set up issue templates
- [ ] Add security policy
- [ ] Create release automation
- [ ] Set up documentation hosting (Read the Docs)

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
http://lists.nongnu.org/mailman/listinfo/dmidecode-devel

## Links

- Project Page: http://projects.autonomy.net.au/python-dmidecode/
- Upstream dmidecode: http://www.nongnu.org/dmidecode/
- Bug Reports: Use GitHub issues or contact maintainers

## Version

Current version: 3.12.3

See doc/changelog for detailed version history.
