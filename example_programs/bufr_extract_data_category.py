#!/usr/bin/env python

"""
This is a small tool/example program intended to loop over all bufr messages
in a bufr file and extract the data category from it, which is then printed
to stdout.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 25-Nov-2010
#
# License: GPL v2.

#  #[ imported modules
import sys # operating system functions

# import the python file defining the RawBUFRFile class
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF

#  #]

def print_bufr_data_category(input_bufr_file):
    #  #[
    """
    an example routine to demonstrate how to retrieve
    some meta datafrom the BUFR messages in a BUFR file
    """
    # get an instance of the RawBUFRFile class
    rbf = RawBUFRFile()

    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    rbf.open(input_bufr_file, 'rb')

    # extract the number of BUFR messages from the file
    num_msgs = rbf.get_num_bufr_msgs()

    for msg_nr in range(1, num_msgs+1):
        raw_msg = rbf.get_raw_bufr_msg(msg_nr)[0]
        bufr_obj = BUFRInterfaceECMWF(encoded_message=raw_msg)
        bufr_obj.decode_sections_012()
        data_category = bufr_obj.ksec1[11-1]
        print 'BUFR msg %i has data category %i' % (msg_nr, data_category)

    # close the file
    rbf.close()
    #  #]

#  #[ run the tool
if len(sys.argv)<2:
    print 'please give a BUFR file as argument'
    sys.exit(1)

INPUT_BUFR_FILE = sys.argv[1]

print_bufr_data_category(INPUT_BUFR_FILE)
#  #]
