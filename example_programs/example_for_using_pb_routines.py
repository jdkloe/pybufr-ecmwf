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
import os, sys     # system functions
import numpy as np # import numerical capabilities

# import the raw wrapper interface to the ECMWF BUFR library
from pybufr_ecmwf import ecmwfbufr
from pybufr_ecmwf.helpers import python3
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
    # unit and error_flag are of type fortint*
    # name and mode are of type string
    (c_file_unit, bufr_error_flag) = ecmwfbufr.pbopen(input_bufr_file, 'R')

    # this will be the call if intent(inplace) is used in the
    # insert_pb_interface_definition method of BUFRInterfaceECMWF
    # in stead of intent(in) and intent(out):
    # ecmwfbufr.pbopen(c_file_unit, input_bufr_file,
    #                  'R', bufr_error_flag)

    print "c_file_unit = ", c_file_unit
    print "pbopen: bufr_error_flag = ", bufr_error_flag

    # pbbufr test

    buffer_size_words = 12000
    buffer_size_bytes = buffer_size_words*4
    file_pos = 0
    file_size = os.path.getsize(input_bufr_file)
    msg_count = 0

    while True:
        msg_size_bytes = 0
        bufr_error_flag = 0
        msg_count += 1

        print "calling: ecmwfbufr.pbbufr()"
        databuffer = np.zeros(buffer_size_words, dtype=np.int)
        ecmwfbufr.pbbufr(c_file_unit, databuffer, buffer_size_bytes,
                         msg_size_bytes, bufr_error_flag)
        print "BUFR message: ", msg_count

        # this always gives zero so is not very useful
        # print "pbbufr result: msg_size_bytes = ", msg_size_bytes

        rawbytes = databuffer.tostring()

        if python3:
            end_section = rawbytes.find(b'7777')
        else:
            end_section = rawbytes.find('7777')

        print 'end_section = ', end_section
        if end_section == -1:
            break

        # retrieve these sizes manually, since they seem not
        # provided by the current interface (don't know why)
        msg_size_bytes = end_section+4
        msg_size_words = int(msg_size_bytes/4)
        if msg_size_bytes > msg_size_words*4:
            msg_size_words += 1
        print "msg_size_bytes = ", msg_size_bytes
        print "msg_size_words = ", msg_size_words

        # msg_size_words = len(np.where(databuffer>0)[0])
        # msg_size_bytes = msg_size_words*4
        # print "(rough estimate) msg_size_bytes = ", msg_size_bytes

        print "raw words [0:4] = ", databuffer[0:4]
        if python3:
            print "raw bytes [0:4] = ", rawbytes[0:4].decode()
        else:
            print "raw bytes [0:4] = ", rawbytes[0:4]
        # print "raw bytes [0:4] = ", [ord(b) for b in rawbytes[0:4]]
        print "pbbufr: bufr_error_flag = ", bufr_error_flag

        # warning: on my system only the first 36 bytes (9 words)
        # of each BUFR message are read in this way, so for now
        # this pb-interface seems useless, even if it compiles
        # and runs without explicit errors ....

        offset = msg_size_bytes
        file_pos += offset
        if file_pos >= file_size:
            break

        # pbseek currently does not work as intended. Don't know why.

        #whence = 1 # define offset to be calculated from current position
        # all inputs and outputs must be of type fortint* !
        #bufr_error_flag = ecmwfbufr.pbseek(c_file_unit, offset, whence)
        #print "pbseek: bufr_error_flag = ", bufr_error_flag
        # possible return values should be:
        #   -2 = error in handling file,
        #   -1 = end-of-file
        #   otherwise,  = byte offset from start of file.
        # However, this seems not to work correctly at the moment...

    # pbclose test

    bufr_error_flag = 0
    print "calling: ecmwfbufr.pbclose()"
    ecmwfbufr.pbclose(c_file_unit, bufr_error_flag)
    print "pbclose: bufr_error_flag = ", bufr_error_flag
    #  #]

# run the example
print "-"*50
print "pb usage example"
print "-"*50

if len(sys.argv)<2:
    print 'please give a BUFR file as first argument'
    sys.exit(1)

INP_BUFR_FILE = sys.argv[1]
pb_example(INP_BUFR_FILE)
print 'succesfully read data from file: ', INP_BUFR_FILE

print "-"*50
print "done"
print "-"*50
