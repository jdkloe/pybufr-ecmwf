#!/usr/bin/env python

"""
This is a small tool/example program intended to inspect a given
bufr file and sort the possible different types of BUFR messages
into different files, with names derived from their template
of unexpanded descriptors.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 09-Jul-2013
#
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

#  #[ imported modules
from __future__ import print_function
import sys     # operating system functions

# import the python file defining the RawBUFRFile class
#from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr import BUFRReader

#  #]

def construct_unique_filename(list_of_unexp_descr, max_filename_len=75):
    #  #[ construct a fileame based on the given template
    '''
    First try to combine the unexpanded descriptor list, by joining them
    with underscores. This should make a guaranteed unique filename
    fit for sorting a bufr file into different types of messages.
    However, the filename can become too long for the current filesystem,
    so implement a maximum length, and if the name is too long, truncate it
    and add the hash of the full descriptor list to make it unique.
    '''
    output_filename = '_'.join(d for d in list_of_unexp_descr)
    if len(output_filename) > max_filename_len:
        import hashlib
        m = hashlib.md5()
        m.update(output_filename)
        md5hexsum = m.hexdigest()
        n=len(md5hexsum)
        if n>max_filename_len:
            print('Sorry, your setting for filename length is shorter than')
            print('the md5 hexdigest hash length. This way the bufr messages')
            print('cannot be sorted into files with guaranteerd unique names.')
            print('Please choose a filename length of {} or above'.format(n))
        output_filename = output_filename[:max_filename_len-n]+md5hexsum
            
    return output_filename
    #  #]

def sort_msgs(input_bufr_file):
    #  #[
    """
    a little example routine to demonstrate how to extract
    BUFR messages from a BUFR file, sort them, and write them
    out again to another file.
    """

    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bob = BUFRReader(input_bufr_file, warn_about_bufr_size=False)
    files_dict = {}

    msg_nr = 0
    while True:
        try:
            bob.get_next_msg()
        except EOFError:
            break
        except KeyError:
            # allow sorting of BUFR messages that cannot be decoded
            # because the needed key is not in the available set of
            # BUFR table files. This tool only uses unexpanded descriptors
            # so ability to decode should not be required.
            # A user still may wish to first sort, and then decode
            # a subset of messages that can be decoded.
            pass
        
        msg_nr += 1
        print('handling message nr ', msg_nr)
        list_of_unexp_descr = bob.bufr_obj.py_unexp_descr_list
        output_filename = construct_unique_filename(list_of_unexp_descr)
        if files_dict.has_key(output_filename):
            fdescr = files_dict[output_filename][0]
            files_dict[output_filename][1] += 1 # increment count
        else:
            fdescr = open(output_filename, 'wb')
            count = 1
            files_dict[output_filename] = [fdescr, count]
        fdescr.write(bob.bufr_obj.encoded_message)

    generated_files = files_dict.keys()
    for k in files_dict.keys():
        count = files_dict[k][1]
        print('file ', k, ' contains ', count, ' messages')
        files_dict[k][0].close()

    return generated_files
    #  #]

#  #[ run the tool
if len(sys.argv) < 2:
    print('please give a BUFR file as argument')
    sys.exit(1)

INPUT_BUFR_FILE = sys.argv[1]
GEN_FILES = sort_msgs(INPUT_BUFR_FILE)
print('generated_files:')
print('\n'.join('   {}'.format(fn) for fn in GEN_FILES))
#  #]
