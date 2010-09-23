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
import pybufr_ecmwf

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
def decoding_example(input_bufr_file):
    #  #[
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """

    # read the binary data using the BUFRFile class
    print 'loading testfile: ', input_bufr_file
    rbf = pybufr_ecmwf.RawBUFRFile()
    rbf.open(input_bufr_file, 'r')
    words = rbf.get_next_raw_bufr_msg()
    rbf.close()
    
    print '------------------------------'
    bufr = pybufr_ecmwf.BUFRInterfaceECMWF(encoded_message=words,
                                           max_nr_expanded_descriptors=44)

    print "calling: decode_sections_012():"
    bufr.decode_sections_012()

    print "Metadata for decoded BUFR message:"
    bufr.print_sections_012_metadata()

    print "calling: setup_tables()"
    bufr.setup_tables()

    print "calling: print_sections_012():"
    bufr.print_sections_012()

    print '------------------------------'
    print "calling: ecmwfbufr.bufrex():"
    bufr.decode_data()

    return bufr
    #  #]

#  #[ run the example
if len(sys.argv)<2:
    print 'please give a BUFR file as first argument'
    sys.exit(1)
    
input_bufr_file = sys.argv[1]

print "-"*50
print "BUFR decoding example"
print "-"*50

BUFRMSG = decoding_example(input_bufr_file)
display_results(BUFRMSG)
print 'succesfully decoded data from file: ',input_bufr_file

print "-"*50
print "done"
print "-"*50
#  #]
