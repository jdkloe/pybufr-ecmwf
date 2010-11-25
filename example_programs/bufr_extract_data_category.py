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
import os, sys # operating system functions
import numpy   # array functionality

# import the python file defining the RawBUFRFile class
from pybufr_ecmwf.bufr import BUFRReader
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF

#  #]

def print_bufr_data_category(input_bufr_file):
    #  #[

    # get an instance of the RawBUFRFile class
    BF = RawBUFRFile()
    
    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    BF.open(input_bufr_file, 'r')
    
    # extract the number of BUFR messages from the file
    num_msgs = BF.get_num_bufr_msgs()

    for msg_nr in range(1,num_msgs+1):
        raw_msg = BF.get_raw_bufr_msg(msg_nr)
        bufr_obj = BUFRInterfaceECMWF(encoded_message=raw_msg)
        bufr_obj.decode_sections_012()
        DataCategory = bufr_obj.ksec1[11-1]
        print 'BUFR msg %i has DataCategory %i' % (msg_nr, DataCategory)
        
    # close the file
    BF.close()
    #  #]

#  #[ run the tool
if len(sys.argv)<2:
    print 'please give a BUFR file as argument'
    sys.exit(1)

input_bufr_file  = sys.argv[1]

print_bufr_data_category(input_bufr_file)
#  #]
