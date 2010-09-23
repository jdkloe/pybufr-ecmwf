#!/usr/bin/env python

"""
This is a small example program intended to demonstrate
how the pybufr_ecmwf wrapper interface to the ECMWF BUFR library may be
used for encoding a BUFR message.
"""

#
# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 25-Feb-2010    
#
# License: GPL v2.

#  #[ imported modules
import os,sys      # operating system functions
import numpy as np # import numerical capabilities

# import BUFR wrapper module
import pybufr_ecmwf

#  #]
#  #[ define constants for the descriptors we need

# note: it would be nice if these could be derived automatically
# from the actual BUFR tables used.

# define descriptor 1
DD_D_DATE_YYYYMMDD = 301011 # date
# this defines the sequence:
# 004001 ! year
# 004002 ! month
# 004003 ! day

# define descriptor 2
DD_D_TIME_HHMM = 301012 # time 
# this defines the sequence:
# 004004 ! hour 
# 004005 ! minute 

# define descriptor 3
DD_PRESSURE = int('007004', 10) # pressure [pa]  

# WARNING: filling the descriptor variable with 007004 will fail
# because python will interpret this as an octal value, and thus
# automatically convert 007004 to the decimal value 3588

# define descriptor 4
DD_TEMPERATURE = int('012001', 10) # [dry-bulb] temperature [K]  

# define descriptor 5
DD_LATITUDE_HIGH_ACCURACY = int('005001', 10)
# latitude (high accuracy) [degree] 

# define descriptor 6
DD_LONGITUDE_HIGH_ACCURACY = int('006001', 10)
# longitude (high accuracy) [degree] 

#  #]

def encoding_example(output_bufr_file):
    #  #[
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """
    
    bufr = pybufr_ecmwf.BUFRInterfaceECMWF(max_nr_descriptors=20)
    
    # fill sections 0, 1, 2 and 3
    bufr_code_centre          =  98 # ECMWF
    bufr_obstype              =   3 # sounding
    bufr_subtype_l1b          = 251 # L1B
    bufr_table_local_version  =   1
    bufr_table_master         =   0
    bufr_table_master_version =  15
    bufr_code_subcentre       =   0 # L2B processing facility
    bufr_compression_flag     =   0 #  64=compression/0=no compression
    
    num_subsets = 4
    bufr.fill_sections_0123(bufr_code_centre,
                            bufr_obstype,
                            bufr_subtype_l1b,
                            bufr_table_local_version,
                            bufr_table_master,
                            bufr_table_master_version,
                            bufr_code_subcentre,
                            num_subsets,
                            bufr_compression_flag)

    # determine information from sections 0123 to construct the BUFR table
    # names expected by the ECMWF BUFR library and create symlinks to the
    # default tables if needed
    bufr.setup_tables()
    
    # define a descriptor list
    template = pybufr_ecmwf.BufrTemplate(max_nr_descriptors=20)
    
    template.add_descriptors(DD_D_DATE_YYYYMMDD, # 0
                             DD_D_TIME_HHMM)     # 1
    
    # delay replication for the next 2 descriptors
    # allow at most 2 delayed replications
    template.add_delayed_replic_descriptors(2,
                                            DD_PRESSURE,
                                            DD_TEMPERATURE)
    
    # replicate the next 2 descriptors 3 times
    template.add_replicated_descriptors(3,
                                        DD_LATITUDE_HIGH_ACCURACY,
                                        DD_LONGITUDE_HIGH_ACCURACY)

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
        
        values[i]        = 1999 # year
        i = i+1
        values[i] =   12 # month
        i = i+1
        values[i] =   31 # day
        i = i+1
        values[i] =   23 # hour
        i = i+1
        values[i] =   59    -        subset # minute
        i = i+1
        values[i] = 2 # delayed replication factor
        # this delayed replication factor determines the actual number
        # of values to be stored for this particular subset
        # even if it is less then the number given in kdata above !
        for repl in range(2):
            i = i+1
            values[i] = 1013.e2 - 100.e2*subset+i+repl # pressure [pa]
            i = i+1 
            values[i] = 273.15  -    10.*subset+i+repl # temperature [K]
        for repl in range(3):
            i = i+1
            values[i] = 51.82   +   0.05*subset+i+repl # latitude
            i = i+1
            values[i] =  5.25   +    0.1*subset+i+repl # longitude

    # do the encoding to binary format
    bufr.encode_data(values, cvals)
    
    # get an instance of the RawBUFRFile class
    BF1 = pybufr_ecmwf.RawBUFRFile()
    # open the file for writing
    BF1.open(output_bufr_file, 'w')
    # write the encoded BUFR message
    BF1.write_raw_bufr_msg(bufr.encoded_message)
    # close the file
    BF1.close()
    #  #]

#  #[ run the example
if len(sys.argv)<2:
    print 'please give a BUFR file as first argument'
    sys.exit(1)

output_bufr_file = sys.argv[1]

# make sure the outputfile does not yet exist
if (os.path.exists(output_bufr_file)):
    os.remove(output_bufr_file)

print "-"*50
print "BUFR encoding example"
print "-"*50

encoding_example(output_bufr_file)
print 'succesfully written BUFR encoded data to file: ',output_bufr_file

print "-"*50
print "done"
print "-"*50
#  #]
