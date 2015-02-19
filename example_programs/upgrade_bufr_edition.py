#!/usr/bin/env python

"""
This is a small tool/example program intended to loop over all bufr messages
in a bufr file, promote the input bufr message to the latest edition number,
and then write it to the output bufr file.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 04-Feb-2014
#
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

#  #[ imported modules
import sys # operating system functions

# import the python file defining the RawBUFRFile class
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
#from pybufr_ecmwf.bufr_template import BufrTemplate
#from pybufr_ecmwf.ecmwfbufr_parameters import JELEM
#  #]

def upgrade_bufr_file(input_bufr_file, output_bufr_file):
    #  #[
    """
    an example routine to demonstrate how to read a BUFR message,
    upgrade it's edition number, and write it to an output BUFR file
    """
    # get 2 instances of the RawBUFRFile class
    rbf_in = RawBUFRFile()
    rbf_out = RawBUFRFile()

    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    rbf_in.open(input_bufr_file, 'rb')

    # open the file for writing
    rbf_out.open(output_bufr_file, 'wb')

    # extract the number of BUFR messages from the file
    num_msgs = rbf_in.get_num_bufr_msgs()

    for msg_nr in range(1, num_msgs+1):
        raw_msg, section_sizes, section_start_locations = \
                 rbf_in.get_raw_bufr_msg(msg_nr)
        bufr_obj = BUFRInterfaceECMWF(raw_msg, section_sizes,
                                      section_start_locations,
                                      verbose=True)

        bufr_obj.decode_sections_012()
        bufr_obj.setup_tables()
        bufr_obj.decode_data()

        nsub = bufr_obj.get_num_subsets()
        n_exp_descr = len(bufr_obj.values)/nsub
        bufr_obj.fill_descriptor_list(nr_of_expanded_descriptors=n_exp_descr)

        bufr_obj.ksec0[3-1] = 4 # set bufr edition to 4
        bufr_obj.ktdlst = bufr_obj.get_descriptor_list()

        # extract delayed replication factors
        delayed_repl_data = bufr_obj.derive_delayed_repl_factors()

        # fill the list of replication factors
        bufr_obj.fill_delayed_repl_data(delayed_repl_data)

        # encode the data
        bufr_obj.encode_data(bufr_obj.values, bufr_obj.cvals)
        print 'Encode BUFR msg %i' % msg_nr

        rbf_out.write_raw_bufr_msg(bufr_obj.encoded_message)

    # close the file
    rbf_in.close()
    rbf_out.close()
    #  #]

#  #[ run the tool
if len(sys.argv) < 3:
    print 'please specify the input and output BUFR file names as argument'
    sys.exit(1)

INPUT_BUFR_FILE = sys.argv[1]
OUTPUT_BUFR_FILE = sys.argv[2]

upgrade_bufr_file(INPUT_BUFR_FILE, OUTPUT_BUFR_FILE)
#  #]
