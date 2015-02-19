#!/usr/bin/env python

"""
This is a small tool/example program intended to loop over all bufr messages
in a bufr file and extract all the data from it, which is then printed
to stdout or written to file, either in ascii or csv format.
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
#import sys # operating system functions
#import getopt # a simpler version of argparse, which was introduced in
#              # python 2.7, and is not by default available for older versions

# import the python file defining the RawBUFRFile class
from pybufr_ecmwf.bufr import BUFRReader
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr_template import BufrTemplate
#from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
#from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
#from pybufr_ecmwf.helpers import python3

#  #]

def select_subsets(input_bufr_file, output_bufr_file):
    #  #[ select on subsets
    """
    select data and write out again
    """

    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bob = BUFRReader(input_bufr_file, warn_about_bufr_size=False)

    # open the file for writing
    rbf_out = RawBUFRFile()
    rbf_out.open(output_bufr_file, 'wb')

    msg_nr = 0
    while True:
        try:
            bob.get_next_msg()
            msg_nr += 1
        except EOFError:
            break

        data = bob.get_values_as_2d_array()
        print 'data.shape = ', data.shape

        if data.shape[0]*data.shape[1] == 0:
            print 'NO DATA FOUND! this seems an empty BUFR message !'
            continue

        # select every other subset
        new_data = data[::2, :]

        print 'new_data.shape = ', new_data.shape
        #bob.bufr_obj

        nsub = bob.bufr_obj.get_num_subsets()
        n_exp_descr = len(bob.bufr_obj.values)/nsub
        bob.bufr_obj.fill_descriptor_list(nr_of_expanded_descriptors=
                                          n_exp_descr)
        bob.bufr_obj.ktdlst = bob.bufr_obj.get_descriptor_list()

        delayed_repl_data = bob.bufr_obj.derive_delayed_repl_factors()
        bob.bufr_obj.fill_delayed_repl_data(delayed_repl_data)

        new_nsub = new_data.shape[0]
        bob.bufr_obj.nr_subsets = new_nsub
        BT = BufrTemplate()
        BT.add_descriptors(*bob.bufr_obj.ktdlst)#[:self.ktdlen])
        BT.nr_of_delayed_repl_factors = 1
        BT.del_repl_max_nr_of_repeats_list = list(delayed_repl_data)
        bob.bufr_obj.register_and_expand_descriptors(BT)

        bob.bufr_obj.kdate = new_nsub*list(delayed_repl_data)

        print 'bob.bufr_obj.cvals.shape = ', bob.bufr_obj.cvals.shape
        bob.bufr_obj.encode_data(new_data, bob.bufr_obj.cvals[:32, :])
        rbf_out.write_raw_bufr_msg(bob.bufr_obj.encoded_message)

        #for subs in range(len(data[:, 0])):
        #    output_fd.write(str(subs)+separator+
        #                    separator.join(str(val) for val in data[subs, :])+
        #                    "\n")
        print 'converted BUFR msg nr. ', msg_nr


    # close the file
    bob.close()
    if msg_nr == 0:
        print 'no BUFR messages found, are you sure this is a BUFR file?'

    rbf_out.close()
    #  #]

# run the tool
bufr_file_in = 'test/testdata/Testoutputfile1.BUFR'
bufr_file_out = 'test/testdata/Testoutputfile1.BUFR.selected_subsets_only'
select_subsets(bufr_file_in, bufr_file_out)
