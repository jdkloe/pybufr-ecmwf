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
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

#  #[ imported modules
from __future__ import print_function
import sys     # operating system functions

# import the python file defining the RawBUFRFile class
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
#  #]

def count_msgs(input_bufr_file):
    #  #[
    """
    a little example routine to demonstrate how to extract
    the number of messages from a BUFR file
    """

    # get an instance of the RawBUFRFile class
    rbf = RawBUFRFile()
    #rbf = RawBUFRFile(verbose=True)

    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    rbf.open(input_bufr_file, 'rb')

    # extract the number of BUFR messages from the file
    num_msgs = rbf.get_num_bufr_msgs()

    # print('rbf.nr_of_bufr_messages = ',rbf.nr_of_bufr_messages)

    # close the file
    rbf.close()

    # delete the class instance
    # (just as test, not really needed here since this scope is about
    #  to be deleted anyway)
    del rbf

    return num_msgs
    #  #]

#  #[ run the tool
if len(sys.argv) < 2:
    print('please give a BUFR file as argument')
    sys.exit(1)

INPUT_BUFR_FILE = sys.argv[1]
print(count_msgs(INPUT_BUFR_FILE))
#  #]
