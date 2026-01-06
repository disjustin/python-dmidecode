/*
 * libxml_stubs.c
 * Stub implementations for libxml2mod Python binding functions
 *
 * These stubs allow the module to compile without linking to libxml2mod.
 * The XML API functions will raise an error if called since XML output
 * support has been removed in favor of JSON-only output.
 */

#include <Python.h>
#include <libxml/tree.h>

/*
 * Stub implementation of libxml_xmlNodePtrWrap
 * Originally from libxml2 Python bindings
 */
PyObject *libxml_xmlNodePtrWrap(xmlNodePtr node)
{
    (void)node;  /* Suppress unused parameter warning */
    PyErr_SetString(PyExc_NotImplementedError,
        "XML API is not available. Use JSON export functions instead.");
    return NULL;
}

/*
 * Stub implementation of libxml_xmlDocPtrWrap
 * Originally from libxml2 Python bindings
 */
PyObject *libxml_xmlDocPtrWrap(xmlDocPtr doc)
{
    (void)doc;  /* Suppress unused parameter warning */
    PyErr_SetString(PyExc_NotImplementedError,
        "XML API is not available. Use JSON export functions instead.");
    return NULL;
}
