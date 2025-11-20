#
#   dmidecode.py
#   Module front-end for the python-dmidecode module.
#
#   Copyright 2009      David Sommerseth <davids@redhat.com>
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
#   For the avoidance of doubt the "preferred form" of this code is one which
#   is in an open unpatent encumbered format. Where cryptographic key signing
#   forms part of the process of creating an executable the information
#   including keys needed to generate an equivalently functional executable
#   are deemed to be part of the source code.
#

import logging
import libxml2
from dmidecodemod import *

# Set up module logger
logger = logging.getLogger(__name__)

DMIXML_NODE='n'
DMIXML_DOC='d'

# Auto-logging configuration
_auto_log_enabled = False

def enable_auto_logging(level=logging.WARNING):
    """
    Enable automatic logging of warnings and debug messages from dmidecode operations.

    Args:
        level: Minimum logging level (default: logging.WARNING)
               Use logging.DEBUG to also log debug messages

    Example:
        import dmidecode
        import logging

        # Configure logging
        logging.basicConfig(level=logging.DEBUG)
        dmidecode.enable_auto_logging(logging.DEBUG)

        # Now all dmidecode operations will automatically log warnings and debug info
        data = dmidecode.QuerySection('bios')
    """
    global _auto_log_enabled
    _auto_log_enabled = True
    if logger.level == logging.NOTSET or logger.level > level:
        logger.setLevel(level)

def disable_auto_logging():
    """Disable automatic logging of warnings and debug messages."""
    global _auto_log_enabled
    _auto_log_enabled = False

def log_messages():
    """
    Log any warnings and debug messages from the last dmidecode operation.
    This is called automatically if enable_auto_logging() has been called.
    You can also call it manually to log messages on demand.
    """
    # Log warnings
    warnings = get_warnings()
    if warnings:
        for line in warnings.strip().split('\n'):
            if line.strip():
                logger.warning(line.strip())
        clear_warnings()

    # Log debug messages
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

class dmidecodeXML:
    "Native Python API for retrieving dmidecode information as XML"

    def __init__(self):
        self.restype = DMIXML_NODE;

    def SetResultType(self, type):
        """
        Sets the result type of queries.  The value can be DMIXML_NODE or DMIXML_DOC,
        which will return an libxml2::xmlNode or libxml2::xmlDoc object, respectively
        """

        if type == DMIXML_NODE:
            self.restype = DMIXML_NODE
        elif type == DMIXML_DOC:
            self.restype = DMIXML_DOC
        else:
            raise TypeError("Invalid result type value")
        return True

    def QuerySection(self, sectname):
        """
        Queries the DMI data structure for a given section name.  A section
        can often contain several DMI type elements
        """
        if self.restype == DMIXML_NODE:
            ret = libxml2.xmlNode( _obj = xmlapi(query_type='s',
                                                           result_type=self.restype,
                                                           section=sectname) )
        elif self.restype == DMIXML_DOC:
            ret = libxml2.xmlDoc( _obj = xmlapi(query_type='s',
                                                          result_type=self.restype,
                                                          section=sectname) )
        else:
            raise TypeError("Invalid result type value")

        # Auto-log if enabled
        if _auto_log_enabled:
            log_messages()

        return ret


    def QueryTypeId(self, tpid):
        """
        Queries the DMI data structure for a specific DMI type.
        """
        if self.restype == DMIXML_NODE:
            ret = libxml2.xmlNode( _obj = xmlapi(query_type='t',
                                                           result_type=self.restype,
                                                           typeid=tpid))
        elif self.restype == DMIXML_DOC:
            ret = libxml2.xmlDoc( _obj = xmlapi(query_type='t',
                                                          result_type=self.restype,
                                                          typeid=tpid))
        else:
            raise TypeError("Invalid result type value")

        # Auto-log if enabled
        if _auto_log_enabled:
            log_messages()

        return ret

