#!/usr/bin/env python

"""
This is a small test tool intended to loop over several bufr files
and load all bufr messages in the file.
This is intended to verify that the same script can handle loading
of bufr files that use different BUFR tables.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system
#
# Written by: J. de Kloe, KNMI, Initial version 6-Nov-2014
#
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

#  #[ imported modules
from __future__ import print_function
import sys, numpy
from pybufr_ecmwf.bufr import BUFRReader

#  #]

def read_bufr_file(input_bufr_file):
    #  #[ read a bufr file
    """
    read the file using the BUFRReader class and get the data
    with the get_values_as_2d_array method
    """

    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bufr = BUFRReader(input_bufr_file, warn_about_bufr_size=False)
    msg_nr = -1
    for msg_nr, msg in enumerate(bufr):
        num_subsets = msg.get_num_subsets()
        for subs, msg_or_subset_data in enumerate(msg):
            #names = msg_or_subset_data.names
            #units = msg_or_subset_data.units
            data = msg_or_subset_data.data
            if data.shape[0] == 0:
                print('NO DATA FOUND! this seems an empty BUFR message !')
                continue

            print('loaded BUFR msg nr. ', msg_nr,
                  'shape = ', data.shape)

            if len(data.shape) == 1:
                print('data[:2] = ', data[:2].tolist())
            else:
                print('data[:2,:2] = ', data[:2,:2].tolist())

            if subs > 1:
                break

    # close the file
    bufr.close()
    if msg_nr == -1:
        print('no BUFR messages found, are you sure this is a BUFR file?')
    #  #]

def main():
    #  #[ define the main program
    """ define the main code for this test program as a subroutine
    to prevent the ugly pylint convention of using capital letters
    for all variables at root level.
    """

    input_bufr_files = sys.argv[1:]
    print('input_bufr_files = ', input_bufr_files)
    for input_bufr_file in input_bufr_files:
        read_bufr_file(input_bufr_file)

#  #]

# run the tool
main()
