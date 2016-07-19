#!/usr/bin/env python

"""
This is a small example program intended to demonstrate how the highest
level pybufr_ecmwf.bufr interface to the ECMWF BUFR library may be used
for decoding a BUFR message via iteration.

This interface only works for BUFR files that contain messages which
can be represented as 2D arrays.
"""

from __future__ import print_function
import sys
import os

from pybufr_ecmwf.bufr import BUFRReader

def decoding_example(input_bufr_file):
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """


    # suppres the default ECMWF welcome message which
    # is not yet redirected to the above defined fileunit
    os.environ['PRINT_TABLE_NAMES'] = 'FALSE'
    # read the binary data using the BUFRReader class
    print('loading testfile: ', input_bufr_file)
    with BUFRReader(input_bufr_file) as bufr:
        for data, names, units in bufr.messages():
                print(data.shape)
                print(len(names))
                print(len(units))


if len(sys.argv) < 2:
    print('please give a BUFR file as first argument')
    sys.exit(1)

INP_BUFR_FILE = sys.argv[1]

print("-"*50)
print("BUFR decoding example")
print("-"*50)

EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
if 'noaa_mos' in INP_BUFR_FILE:
    BUFRMSG = decoding_example(INP_BUFR_FILE)
else:
    BUFRMSG = decoding_example(INP_BUFR_FILE)

print('succesfully decoded data from file: ', INP_BUFR_FILE)

print("-"*50)
print("done")
print("-"*50)
