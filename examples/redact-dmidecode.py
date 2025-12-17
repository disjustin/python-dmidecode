#!/usr/bin/env python3

import argparse
import re
import sys

"""
A simple Python script to redact sensitive information from dmidecode output logs.

Sensitive fields typically include:
- Serial Number
- Product Name
- Asset Tag
- UUID
- SKU Number (sometimes sensitive)
- Part Number (for memory devices, often linked to serial)

The script replaces the values of these fields with '[REDACTED]' while preserving the structure of the output.
It processes the input line by line, handling indented lines correctly.

Usage:
    python redact_dmidecode.py input.txt > redacted.txt
    cat dmidecode_output.txt | python redact_dmidecode.py
"""

SENSITIVE_PATTERNS = [
    r'(Serial Number):\s*.+',
    r'(Product Name):\s*.+',
    r'(Asset Tag):\s*.+',
    r'(UUID):\s*.+',
    r'(SKU Number):\s*.+',
    r'(Part Number):\s*.+',  # Often sensitive in memory devices
]

COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SENSITIVE_PATTERNS]

def redact_line(line: str) -> str:
    """
    Redact sensitive values in a single line if it matches any pattern.
    Only replaces the value part after the colon.
    """
    for pattern in COMPILED_PATTERNS:
        def repl(match):
            key = match.group(1)
            return f"{key}: [REDACTED]"
        
        new_line = pattern.sub(repl, line.strip())
        if new_line != line.strip():
            # Re-add original indentation
            indent = line[:len(line) - len(line.lstrip())]
            return indent + new_line + '\n'
    return line

def main():
    parser = argparse.ArgumentParser(
        description="Redact sensitive information (serial numbers, UUIDs, etc.) from dmidecode output."
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        type=argparse.FileType('r'),
        default=sys.stdin,
        help="Input file containing dmidecode output (default: stdin)"
    )
    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('w'),
        default=sys.stdout,
        help="Output file for redacted content (default: stdout)"
    )
    
    args = parser.parse_args()
    
    with args.input_file as infile, args.output as outfile:
        for line in infile:
            redacted = redact_line(line)
            outfile.write(redacted)

if __name__ == "__main__":
    main()