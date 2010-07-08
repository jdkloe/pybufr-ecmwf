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
import os          # operating system functions
import sys         # system functions
import numpy as np # import numerical capabilities

# set the python path to find the (maybe not yet installed) module files
# (not needed if the module is installed in the default location)
import helpers 
helpers.set_python_path()

# import the BUFR wrapper module
import pybufr_ecmwf
#  #]

# decoding_excample
def decoding_example():
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """

    # read the binary data using the BUFRFile class
    testdata_dir = helpers.get_testdata_dir()
    input_test_bufr_file = os.path.join(testdata_dir,'Testfile.BUFR')

    print 'loading testfile: ',input_test_bufr_file
    rbf = pybufr_ecmwf.RawBUFRFile()
    rbf.open(input_test_bufr_file, 'r')
    words = rbf.get_next_raw_bufr_msg()
    rbf.close()
    
    print '------------------------------'
    BI = pybufr_ecmwf.BUFRInterfaceECMWF(encoded_message=words,
                                         max_nr_expanded_descriptors=44)

    print "calling: decode_sections_012():"
    BI.decode_sections_012()

    print "Metadata for decoded BUFR message:"
    BI.print_sections_012_metadata()

    print "calling: setup_tables()"
    BI.setup_tables()

    print "calling: print_sections_012():"
    BI.print_sections_012()

    print '------------------------------'
    print "calling: ecmwfbufr.bufrex():"
    BI.decode_data()

    # print a selection of the decoded numbers
    print '------------------------------'
    print "Metadata for decoded BUFR message:"
    BI.print_sections_01234_metadata()

    print '------------------------------'
    print "The list of names and units for the numbers in this BUFR message:"
    BI.print_names_and_units()

    print '------------------------------'
    print "Decoded BUFR message:"

    print "values array: ", BI.values
    txt = ''.join(str(v)+';' for v in BI.values[:20] if v>0.)
    print "values[:20] : ", txt

    nsubsets = BI.get_num_subsets()
    print "number of subsets in the BUFR message is: ",nsubsets

    nelements = BI.get_num_elements()
    print "number of elements in each subset is: ",nelements

    lat_array = BI.get_values(24)
    lon_array = BI.get_values(25)

    lat = np.zeros(nsubsets)
    lon = np.zeros(nsubsets)
    for subs in range(nsubsets):
        if (30*(subs/30) == subs):
            print " lat_array["+str(subs)+"] = "+str(lat_array[subs])+\
                  " lon_array["+str(subs)+"] = "+str(lon_array[subs])


    print '------------------------------'
    # this is a nice way to verify that you picked the right element from
    # the BUFR message:
    print 'latitude  name [unit]: %s [%s]' % BI.get_element_name_and_unit(24)
    print 'longitude name [unit]: %s [%s]' % BI.get_element_name_and_unit(25)
    print '------------------------------'

    BI.fill_descriptor_list()
    
    print 'busel result:'
    print "ktdlen = ", BI.ktdlen
    print "ktdexl = ", BI.ktdexl

    descriptor_list          = BI.get_descriptor_list()
    expanded_discriptor_list = BI.get_expanded_descriptor_list()
    print "descriptor list: ",descriptor_list
    print "descriptor list length: ",len(descriptor_list)
    print "expanded descriptor list: ",expanded_discriptor_list
    print "expanded descriptor list length: ",len(expanded_discriptor_list)
    
    print '------------------------------'
    print "printing content of section 3:"
    BI.print_descriptors()
    

print "-"*50
print "BUFR decoding example"
print "-"*50

decoding_example()

print "-"*50
print "done"
print "-"*50
