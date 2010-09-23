#!/usr/bin/env python

"""
This is a small example program intended to demonstrate
how the RawBUFRFile class defined in the pybufr_ecmwf.py
module may be used.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 21-Jan-2010    
#
# License: GPL v2.

#  #[ imported modules
import os          # operating system functions
import sys         # system functions

# import the python file defining the RawBUFRFile class
from pybufr_ecmwf import RawBUFRFile
#  #]

def raw_file_reading_example(input_bufr_file):
    #  #[
    # get an instance of the RawBUFRFile class
    BF = RawBUFRFile()
    
    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    BF.open(input_bufr_file, 'r')
    
    # print the internal data of the class instance
    BF.print_properties(prefix = "RawBUFRFile (opened for reading)")

    # print the number of BUFR messages in the file
    NUM_MSGS = BF.get_num_bufr_msgs()
    print "This file contains: ", NUM_MSGS, " BUFR messages."

    # sequentially read the raw (undecoded) BUFR messages from the
    # class instance
    msg1 = BF.get_next_raw_bufr_msg() # should return proper data
    msg2 = BF.get_next_raw_bufr_msg() # should return corrupted data
    msg3 = BF.get_next_raw_bufr_msg() # should return corrupted data
    print "a warning is expected here:"
    msg4 = BF.get_next_raw_bufr_msg() # returns with None

    for i in range(1, NUM_MSGS+1):
        # read a selected raw BUFR message from the class instance
        raw_data = BF.get_raw_bufr_msg(i)
        print "msg ", i, " got ", len(raw_data), " words"

    # close the file
    BF.close()
    
    # delete the class instance
    del(BF)
    return (msg1, msg2, msg3)
    #  #]
def raw_file_writing_example(output_bufr_file, msg1, msg2):
    #  #[
    
    # get an instance of the RawBUFRFile class
    BF1 = RawBUFRFile()
    
    # open the test file for writing
    BF1.open(output_bufr_file, 'w')
    
    # write a few raw (encoded) BUFR messages
    BF1.write_raw_bufr_msg(msg1)
    BF1.write_raw_bufr_msg(msg2)

    # print the internal data of the class instance
    BF1.print_properties(prefix = "RawBUFRFile (opened for writing)")
    
    # close the file
    BF1.close()
    
    # delete the class instance
    del(BF1)
    #  #]
def raw_file_appending_example(output_bufr_file, msg3):
    #  #[
    
    # get an instance of the RawBUFRFile class
    BF2 = RawBUFRFile()
    
    # open the test file for appending
    BF2.open(output_bufr_file, 'a')
    
    # write a third raw (encoded) BUFR messages
    BF2.write_raw_bufr_msg(msg3)
    
    # print the internal data of the class instance
    BF2.print_properties(prefix = "RawBUFRFile2 (opened for appending)")
    
    # close the file
    BF2.close()

    # delete the class instance
    del(BF2)
    #  #]

#  #[ run the example
if len(sys.argv)<3:
    print 'please give 2 BUFR files as argument'
    sys.exit(1)

input_bufr_file  = sys.argv[1]
output_bufr_file = sys.argv[2]
# make sure the outputfile does not yet exist
if (os.path.exists(output_bufr_file)):
    os.remove(output_bufr_file)

print "-"*50
print "reading example"
print "-"*50

(msg1, msg2, msg3) = raw_file_reading_example(input_bufr_file)

print "-"*50
print "writing example"
print "-"*50

raw_file_writing_example(output_bufr_file, msg1, msg2)

print "-"*50
print "appending example"
print "-"*50

raw_file_appending_example(output_bufr_file, msg3)

print "-"*50
print "done"
print "-"*50
#  #]
