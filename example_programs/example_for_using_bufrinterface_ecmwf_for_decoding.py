#!/usr/bin/env python

"""
This is a small example program intended to demonstrate
how the pybufr_ecmwf wrapper interface to the ECMWF BUFR library may be
used for decoding a BUFR message.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 25-Feb-2010    
#
# License: GPL v2.

#  #[ imported modules
import sys  # operating system functions

# import the BUFR wrapper module
#import pybufr_ecmwf
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
#  #]

# decoding_excample
def display_results(bufr):
    #  #[
    """
    a collation of prints to demonstrate that the message was properly decoded
    """
    
    # print a selection of the decoded numbers
    print '------------------------------'
    print "Metadata for decoded BUFR message:"
    bufr.print_sections_01234_metadata()

    print '------------------------------'
    print "The list of names and units for the numbers in this BUFR message:"
    bufr.print_names_and_units()

    print '------------------------------'
    print "Decoded BUFR message:"

    print "values array: ", bufr.values
    txt = ''.join(str(v)+';' for v in bufr.values[:20] if v>0.)
    print "values[:20] : ", txt

    nsubsets = bufr.get_num_subsets()
    print "number of subsets in the BUFR message is: ", nsubsets

    nelements = bufr.get_num_elements()
    print "number of elements in each subset is: ", nelements

    lat_array = bufr.get_values(24)
    lon_array = bufr.get_values(25)

    for subs in range(nsubsets):
        if (30*(subs/30) == subs):
            print " lat_array["+str(subs)+"] = "+str(lat_array[subs])+\
                  " lon_array["+str(subs)+"] = "+str(lon_array[subs])


    print '------------------------------'
    # this is a nice way to verify that you picked the right element from
    # the bufr message:
    print 'latitude  name [unit]: %s [%s]' % bufr.get_element_name_and_unit(24)
    print 'longitude name [unit]: %s [%s]' % bufr.get_element_name_and_unit(25)
    print '------------------------------'

    bufr.fill_descriptor_list()
    
    print 'busel result:'
    print "ktdlen = ", bufr.ktdlen
    print "ktdexl = ", bufr.ktdexl

    descriptor_list          = bufr.get_descriptor_list()
    expanded_discriptor_list = bufr.get_expanded_descriptor_list()
    print "descriptor list: ", descriptor_list
    print "descriptor list length: ", len(descriptor_list)
    print "expanded descriptor list: ", expanded_discriptor_list
    print "expanded descriptor list length: ", len(expanded_discriptor_list)
    
    print '------------------------------'
    print "printing content of section 3:"
    bufr.print_descriptors()
    #  #]
def decoding_example(input_bufr_file, custom_bufr_tables=None):
    #  #[
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """

    # read the binary data using the BUFRFile class
    print 'loading testfile: ', input_bufr_file
    rbf = RawBUFRFile(verbose=False)
    rbf.open(input_bufr_file, 'r')
    (words, section_sizes, section_start_locations) = \
            rbf.get_next_raw_bufr_msg()
    rbf.close()

    if words is None:
        print 'No valid BUFR messages found'
        sys.exit(0)
    
    print '------------------------------'
    bufr = BUFRInterfaceECMWF(encoded_message=words,
                              section_sizes=section_sizes,
                              section_start_locations=section_start_locations)

    print "calling: decode_sections_012():"
    bufr.decode_sections_012()

    print "Metadata for decoded BUFR message:"
    bufr.print_sections_012_metadata()

    print "calling: setup_tables()"
    if custom_bufr_tables:
        bufr.setup_tables(table_b_to_use=custom_bufr_tables[0],
                          table_d_to_use=custom_bufr_tables[1])
    else:
        bufr.setup_tables()

    print "calling: print_sections_012():"
    bufr.print_sections_012()

    # seems not to work correctly now ...
    #bufr.fill_descriptor_list()
    #bufr.print_descriptors()

    print '------------------------------'
    print "calling: bufr.decode_data():"
    bufr.decode_data()

    return bufr
    #  #]

#  #[ run the example
if len(sys.argv)<2:
    print 'please give a BUFR file as first argument'
    sys.exit(1)
    
INP_BUFR_FILE = sys.argv[1]

print "-"*50
print "BUFR decoding example"
print "-"*50

CUSTOM_BUFR_TABLES = \
      ('pybufr_ecmwf/alt_bufr_tables/GENERIC_SCAT_BUFR_TABLE_B.TXT',
       'pybufr_ecmwf/alt_bufr_tables/GENERIC_SCAT_BUFR_TABLE_D.TXT')
if 'noaa_mos' in INP_BUFR_FILE:
    BUFRMSG = decoding_example(INP_BUFR_FILE)
else:
    # the custom generic_scat tables are only usefull when decoding
    # scatteromet BUFR files
    BUFRMSG = decoding_example(INP_BUFR_FILE)
#    BUFRMSG = decoding_example(INP_BUFR_FILE,
#                               custom_bufr_tables=CUSTOM_BUFR_TABLES)
    
#BUFRMSG = decoding_example(INP_BUFR_FILE)
display_results(BUFRMSG)
print 'succesfully decoded data from file: ', INP_BUFR_FILE

print "-"*50
print "done"
print "-"*50
#  #]
