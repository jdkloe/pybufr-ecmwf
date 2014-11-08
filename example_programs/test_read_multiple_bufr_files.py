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
# License: GPL v2. See the COPYING.txt file for details.

#  #[ imported modules
import sys
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
    bob = BUFRReader(input_bufr_file, warn_about_bufr_size=False)

    msg_nr = 0
    while True:
        try:
            bob.get_next_msg()
            msg_nr += 1
        except EOFError:
            break

        data = bob.get_values_as_2d_array()

        if data.shape[0]*data.shape[1] == 0:
            print 'NO DATA FOUND! this seems an empty BUFR message !'
            continue

        print 'loaded BUFR msg nr. ', msg_nr, 'shape = ', data.shape
        print 'data[:2,:2] = ', data[:2, :2]

    # close the file
    bob.close()
    if msg_nr == 0:
        print 'no BUFR messages found, are you sure this is a BUFR file?'
    #  #]

def main():
    #  #[ define the main program
    """ define the main code for this test program as a subroutine
    to prevent the ugly pylint convention of using capital letters
    for all variables at root level.
    """

    input_bufr_files = sys.argv[1:]
    print 'input_bufr_files = ', input_bufr_files
    for input_bufr_file in input_bufr_files:
        read_bufr_file(input_bufr_file)

#  #]

# run the tool
main()
