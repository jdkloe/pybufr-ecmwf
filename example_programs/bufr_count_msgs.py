#!/usr/bin/env python

"""
This is a small tool/example program intended to inspect a given
bufr file and extract the nr of bufr messages in it, which is
then printed to stdout.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 24-Sep-2010    
#
# License: GPL v2.

#  #[ imported modules
import os, sys     # operating system functions

# import the python file defining the RawBUFRFile class
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
#  #]

def count_msgs(input_bufr_file):
    #  #[
    # get an instance of the RawBUFRFile class
    BF = RawBUFRFile()
    #BF = RawBUFRFile(verbose=True)
    
    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    BF.open(input_bufr_file, 'r')
    
    # extract the number of BUFR messages from the file
    num_msgs = BF.get_num_bufr_msgs()

    # print 'BF.nr_of_bufr_messages = ',BF.nr_of_bufr_messages
    
    # close the file
    BF.close()
    
    # delete the class instance
    del(BF)
    return num_msgs
    #  #]

#  #[ run the tool
if len(sys.argv)<2:
    print 'please give a BUFR file as argument'
    sys.exit(1)

input_bufr_file  = sys.argv[1]

num_msgs = count_msgs(input_bufr_file)
print num_msgs
#  #]
