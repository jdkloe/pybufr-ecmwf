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
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
#  #]

def raw_file_reading_example(input_bufr_file):
    #  #[
    """
    example for reading a BUFR message
    """

    # get an instance of the RawBUFRFile class
    rbf = RawBUFRFile()
    
    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    rbf.open(input_bufr_file, 'rb')
    
    # print the internal data of the class instance
    rbf.print_properties(prefix = "RawBUFRFile (opened for reading)")

    # print the number of BUFR messages in the file
    num_msgs = rbf.get_num_bufr_msgs()
    print "This file contains: ", num_msgs, " BUFR messages."

    # sequentially read the raw (undecoded) BUFR messages from the
    # class instance
    msg1 = rbf.get_next_raw_bufr_msg()[0] # should return proper data
    try:
        msg2 = rbf.get_next_raw_bufr_msg()[0] # should return corrupted data
    except EOFError:
        msg2 = None
    try:
        msg3 = rbf.get_next_raw_bufr_msg()[0] # should return corrupted data
    except EOFError:
        msg3 = None

    print "a warning is expected here:"
    # msg4 =
    try:
        rbf.get_next_raw_bufr_msg()[0] # should raise an EOF error
    except EOFError:
        print "Warning: EOF reached !"

    for i in range(1, num_msgs+1):
        # read a selected raw BUFR message from the class instance
        raw_data = rbf.get_raw_bufr_msg(i)[0]
        print "msg ", i, " got ", len(raw_data), " words"

    # close the file
    rbf.close()
    
    # delete the class instance
    del(rbf)
    return (msg1, msg2, msg3)
    #  #]
def raw_file_writing_example(output_bufr_file, msg1, msg2):
    #  #[
    """
    example for writing a BUFR message
    """
    
    # get an instance of the RawBUFRFile class
    bf1 = RawBUFRFile()
    
    # open the test file for writing
    bf1.open(output_bufr_file, 'wb')
    
    # write a few raw (encoded) BUFR messages
    bf1.write_raw_bufr_msg(msg1)
    if msg2 is not None:
        bf1.write_raw_bufr_msg(msg2)

    # print the internal data of the class instance
    bf1.print_properties(prefix = "RawBUFRFile (opened for writing)")
    
    # close the file
    bf1.close()
    
    # delete the class instance
    del(bf1)
    #  #]
def raw_file_appending_example(output_bufr_file, msg3):
    #  #[
    """
    example for appending a BUFR message
    """
    
    # get an instance of the RawBUFRFile class
    bf2 = RawBUFRFile()
    
    # open the test file for appending
    bf2.open(output_bufr_file, 'ab')
    
    # write a third raw (encoded) BUFR messages
    if msg3 is not None:
        bf2.write_raw_bufr_msg(msg3)
    
    # print the internal data of the class instance
    bf2.print_properties(prefix = "RawBUFRFile2 (opened for appending)")
    
    # close the file
    bf2.close()

    # delete the class instance
    del(bf2)
    #  #]

#  #[ run the example
if len(sys.argv)<3:
    print 'please give 2 BUFR files as argument'
    sys.exit(1)

INP_BUFR_FILE = sys.argv[1]
OUTP_BUFR_FILE = sys.argv[2]
# make sure the outputfile does not yet exist
if (os.path.exists(OUTP_BUFR_FILE)):
    os.remove(OUTP_BUFR_FILE)

print "-"*50
print "reading example"
print "-"*50

(MSG1, MSG2, MSG3) = raw_file_reading_example(INP_BUFR_FILE)

print "-"*50
print "writing example"
print "-"*50

raw_file_writing_example(OUTP_BUFR_FILE, MSG1, MSG2)

print "-"*50
print "appending example"
print "-"*50

raw_file_appending_example(OUTP_BUFR_FILE, MSG3)

print "-"*50
print "done"
print "-"*50
#  #]
