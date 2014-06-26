#!/usr/bin/env python

"""
This is a small example program intended to demonstrate
how a custom made pair of BUFR tables may be used for
encoding a BUFR message.
"""

#
# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 04-Sep-2011
#
# License: GPL v2.

#  #[ imported modules
import os, sys     # operating system functions
import numpy as np # import numerical capabilities

# import BUFR wrapper module
#import pybufr_ecmwf
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
from pybufr_ecmwf.bufr_template import BufrTemplate
#  #]
#  #[ define constants for the descriptors we need

# note: it would be nice if these could be derived automatically
# from the actual BUFR tables used.

# define some constants for the descriptors to be used
DD_B_048001 = int('048001', 10)
DD_B_048002 = int('048002', 10)
DD_D_348001 = 348001 # this defines the sequence: [048001, 048002]

#  #]

def encoding_example(output_bufr_file):
    #  #[
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """

    bufr = BUFRInterfaceECMWF(verbose=True)

    # fill sections 0, 1, 2 and 3
    num_subsets = 4
    bufr.fill_sections_0123(bufr_code_centre =  98, # ECMWF
                            bufr_obstype     =   3, # sounding
                            bufr_subtype     = 251, # L1B
                            bufr_table_local_version  =  1,
                            bufr_table_master         =  0,
                            bufr_table_master_version = 15,
                            bufr_code_subcentre = 0, # L2B processing facility
                            num_subsets = num_subsets,
                            bufr_compression_flag = 0)
    # 64=compression/0=no compression

    # determine information from sections 0123 to construct the BUFR table
    # names expected by the ECMWF BUFR library and create symlinks to the
    # default tables if needed
    # NOTE: these custom BUFR tables have been created by the
    #       create_bufr_tables.py example script
    bufr.setup_tables(table_b_to_use='B_my_test_BUFR_table.txt',
                      table_c_to_use='C_my_test_BUFR_table.txt',
                      table_d_to_use='D_my_test_BUFR_table.txt')

    # define a descriptor list
    template = BufrTemplate()

    template.add_descriptors(DD_B_048001,        # 0
                             DD_B_048002,        # 1
                             DD_D_348001)        # 2

    bufr.register_and_expand_descriptors(template)

    # retrieve the length of the expanded descriptor list
    exp_descr_list_length = bufr.ktdexl
    print "exp_descr_list_length = ", exp_descr_list_length

    # fill the values array with some dummy varying data
    num_values = exp_descr_list_length*num_subsets
    values = np.zeros(num_values, dtype=np.float64) # this is the default

    # note: these two must be identical for now, otherwise the
    # python to fortran interface breaks down. This also ofcourse is the
    # cause of the huge memory use of cvals in case num_values is large.
    num_cvalues = num_values
    cvals  = np.zeros((num_cvalues, 80), dtype=np.character)

    for subset in range(num_subsets):
        # note that python starts counting with 0, unlike fortran,
        # so there is no need to take (subset-1)
        i = subset*exp_descr_list_length

        # fill the message with some dummy data
        values[i] = 1.2515 + 0.0011*subset
        i = i+1
        values[i] = (3.4562 + 0.0012*subset)*1.e-9
        i = i+1
        values[i] = 1.2625 + 0.0003*subset
        i = i+1
        values[i] = (3.4561 + 0.0014*subset)*1.e-9

    # do the encoding to binary format
    bufr.encode_data(values, cvals)

    # get an instance of the RawBUFRFile class
    bf1 = RawBUFRFile()
    # open the file for writing
    bf1.open(output_bufr_file, 'wb')
    # write the encoded BUFR message
    bf1.write_raw_bufr_msg(bufr.encoded_message)
    # close the file
    bf1.close()
    #  #]

#  #[ run the example
if len(sys.argv)<2:
    print 'please give a BUFR file as first argument'
    sys.exit(1)

OUTP_BUFR_FILE = sys.argv[1]

# make sure the outputfile does not yet exist
if (os.path.exists(OUTP_BUFR_FILE)):
    os.remove(OUTP_BUFR_FILE)

print "-"*50
print "BUFR encoding example"
print "-"*50

encoding_example(OUTP_BUFR_FILE)
print 'succesfully written BUFR encoded data to file: ', OUTP_BUFR_FILE

print "-"*50
print "done"
print "-"*50
#  #]
