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
        md5 = hashlib.md5()
        md5.update(output_filename.encode())

        md5hexsum = md5.hexdigest()
        md5_len = len(md5hexsum)
        if md5_len > max_filename_len:
            print('Sorry, your setting for filename length is shorter than')
            print('the md5 hexdigest hash length. This way the bufr messages')
            print('cannot be sorted into files with guaranteerd unique names.')
            print('Please choose a filename length of {} or above'.
                  format(md5_len))
        output_filename = output_filename[:max_filename_len-md5_len]+md5hexsum

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
    num_msgs = bob._rbf.get_num_bufr_msgs()
    progress_step = max(1, int(num_msgs/20))

    files_dict = {}
    msg_nr = 0
    while True:
        can_be_decoded = False
        try:
            bob.get_next_msg()
            can_be_decoded = True
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
        if progress_step*int(msg_nr/progress_step) == msg_nr:
            print('handling message nr {} out of {}'.format(msg_nr, num_msgs))

        list_of_unexp_descr = bob.msg._bufr_obj.py_unexp_descr_list
        output_filename = construct_unique_filename(list_of_unexp_descr)
        if output_filename in files_dict:
            fdescr = files_dict[output_filename][0]
            files_dict[output_filename][1] += 1 # increment count
        else:
            fdescr = open(output_filename, 'wb')
            count = 1
            files_dict[output_filename] = [fdescr, count, can_be_decoded,
                                           list_of_unexp_descr]
        fdescr.write(bob.msg._bufr_obj.encoded_message)

    generated_files = files_dict.keys()
    num_that_can_be_decoded = 0
    num_that_cannot_be_decoded = 0
    # note: sort the output to make the result reproducible
    # (makes its behaviour much nicer in the unittests)
    for k in sorted(files_dict):
        fdescr, count, can_be_decoded, list_of_unexp_descr = files_dict[k]
        print('file {} contains {} messages'.format(k[:25], count))
        files_dict[k][0].close()
        if can_be_decoded:
            num_that_can_be_decoded += 1
        else:
            num_that_cannot_be_decoded += 1
            # check to see if local descriptors are present
            for descr in list_of_unexp_descr:
                if int(descr[3:]) >= 192:
                    print('==>A local descriptor definition is present: ',
                          descr)
            print('==>this template cannot be decoded with '+
                  'standard WMO BUFR tables.')

    print('Sorting results:')
    print('BUFR messages with {} different templates are present in this file'.
          format(num_that_can_be_decoded+num_that_cannot_be_decoded))
    if num_that_cannot_be_decoded > 0:
        print('decoding is not possible for {} templates.'.
              format(num_that_cannot_be_decoded))

    return generated_files
    #  #]

if __name__ == '__main__':
    #  #[ run the tool
    if len(sys.argv) < 2:
        print('please give a BUFR file as argument')
        sys.exit(1)

    INPUT_BUFR_FILE = sys.argv[1]
    GEN_FILES = sort_msgs(INPUT_BUFR_FILE)
    # note: sort the output to make the result reproducible
    # (makes its behaviour much nicer in the unittests)
    print('generated_files:')
    print('\n'.join('   {}'.format(fn) for fn in sorted(GEN_FILES)))
    #  #]
