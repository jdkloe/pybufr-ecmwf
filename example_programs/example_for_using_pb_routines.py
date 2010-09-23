#!/usr/bin/env python

"""
This is a small example program intended to demonstrate
how the pb-routines from the ECMWF BUFR library
may be used.

KNOWN PROBLEM:
on my 64-bit linux machine this code fails, and gives the following error:
...
input_test_bufr_file = [Testfile3CorruptedMsgs.BUFR]
calling: ecmwfbufr.pbopen()
Traceback (most recent call last):
  File ".//example_for_using_pb_routines.py", line 67, in <module>
    (c_file_unit,bufr_error_flag) = ecmwfbufr.pbopen(input_test_bufr_file,'R')
SystemError: NULL result without error in PyObject_Call
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 22-Jan-2010
#
# License: GPL v2.

#  #[ imported modules
import os          # import os functionality
import sys         # system functions
import numpy as np # import numerical capabilities

# import the raw wrapper interface to the ECMWF BUFR library
from pybufr_ecmwf import ecmwfbufr
#  #]

def pb_example(input_bufr_file):
    #  #[
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """

    # pbopen test
    c_file_unit     = 0
    bufr_error_flag = 0
    print "input_bufr_file = ["+input_bufr_file+"]"
    print "calling: ecmwfbufr.pbopen()"
    (c_file_unit, bufr_error_flag) = ecmwfbufr.pbopen(input_bufr_file, 'R')
    
    # this will be the call if intent(inplace) is used in the 
    # insert_pb_interface_definition method of BUFRInterfaceECMWF
    # in stead of intent(in) and intent(out):
    # ecmwfbufr.pbopen(c_file_unit, input_bufr_file,
    #                  'R', bufr_error_flag)
    
    print "c_file_unit = ", c_file_unit
    print "bufr_error_flag = ", bufr_error_flag
    
    # pbbufr test
    
    buffer_size_words = 12000
    buffer_size_bytes = buffer_size_words/4
    
    for i in range(4):
        msg_size_bytes = 0
        bufr_error_flag = 0
        print "calling: ecmwfbufr.pbbufr()"
        databuffer = np.zeros(buffer_size_words, dtype=np.int)
        ecmwfbufr.pbbufr(c_file_unit, databuffer, buffer_size_bytes,
                         msg_size_bytes, bufr_error_flag)
        print "BUFR message: ", i
        
        # retrieve these sizes manually, since they seem not
        # provided by the current interface (don't know why)
        msg_size_words = len(np.where(databuffer>0)[0])
        msg_size_bytes = msg_size_words*4
        print "msg_size_bytes = ", msg_size_bytes
        print "buffer[0:4] = ", databuffer[0:4]
        print "bufr_error_flag = ", bufr_error_flag
        
        # warning: on my system only the first 36 bytes (9 words)
        # of each BUFR message are read in this way, so for now
        # this pb-interface seems useless, even if it compiles
        # and runs without explicit errors ....
        
    # pbclose test
    
    bufr_error_flag = 0
    print "calling: ecmwfbufr.pbclose()"
    ecmwfbufr.pbclose(c_file_unit, bufr_error_flag)
    print "bufr_error_flag = ", bufr_error_flag
    #  #]

# run the example
print "-"*50
print "pb usage example"
print "-"*50

if len(sys.argv)<2:
    print 'please give a BUFR file as first argument'
    sys.exit(1)

input_bufr_file = sys.argv[1]
pb_example(input_bufr_file)
print 'succesfully read data from file: ',input_bufr_file

print "-"*50
print "done"
print "-"*50
