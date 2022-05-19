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

def limit_to_6_digits(x):
    import numpy
    #print('INSIDE: x=',x )
    result = numpy.round(x*1e6)/1e6
    #print('INSIDE: r=',result )
    return result

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
    example_printed = False
    with BUFRReader(input_bufr_file) as bufr:
        for msg in bufr:
            for msg_or_subset_data in msg:
                data = msg_or_subset_data.data
                names = msg_or_subset_data.names
                units = msg_or_subset_data.units
                print('data.shape = ', data.shape)
                print('len(names) = ', len(names))
                print('len(units) = ', len(units))

                if not example_printed:
                    # print some of the values to show
                    # that decoding really happened
                    if len(data.shape) == 2:
                        values = limit_to_6_digits(data[0, :25])
                        print('data[0, :25] = ', values.tolist())
                    else:
                        values = limit_to_6_digits(data[:25])
                        print('data[:25] = ', values.tolist())
                    example_printed = True

if len(sys.argv) < 2:
    print('please give a BUFR file as first argument')
    sys.exit(1)

INP_BUFR_FILE = sys.argv[1]

print("-"*50)
print("BUFR decoding example")
print("-"*50)

EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
#if 'noaa_mos' in INP_BUFR_FILE:
#    BUFRMSG = decoding_example(INP_BUFR_FILE)
#else:
BUFRMSG = decoding_example(INP_BUFR_FILE)

print('succesfully decoded data from file: ', INP_BUFR_FILE)

print("-"*50)
print("done")
print("-"*50)
