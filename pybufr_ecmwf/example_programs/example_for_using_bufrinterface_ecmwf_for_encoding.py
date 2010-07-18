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
import os          # operating system functions
import sys         # system functions
import numpy as np # import numerical capabilities
import time        # handling of date and time

# set the python path to find the (maybe not yet installed) module files
# (not needed if the module is installed in the default location)
import helpers 
helpers.set_python_path()

# import BUFR wrapper module
import pybufr_ecmwf
#  #]
#  #[ define constants for the descriptors we need

# note: it would be nice if these could be derived automatically
# from the actual BUFR tables used.

# define descriptor 1
dd_d_date_YYYYMMDD = 301011 # date
# this defines the sequence:
# 004001 ! year
# 004002 ! month
# 004003 ! day

# define descriptor 2
dd_d_time_HHMM = 301012 # time 
# this defines the sequence:
# 004004 ! hour 
# 004005 ! minute 

# define descriptor 3
dd_pressure = int('007004',10) # pressure [pa]  

# WARNING: filling the descriptor variable with 007004 will fail
# because python will interpret this as an octal value, and thus
# automatically convert 007004 to the decimal value 3588

# define descriptor 4
dd_temperature = int('012001',10) # [dry-bulb] temperature [K]  

# define descriptor 5
dd_latitude_high_accuracy = int('005001',10)
# latitude (high accuracy) [degree] 

# define descriptor 6
dd_longitude_high_accuracy = int('006001',10)
# longitude (high accuracy) [degree] 

#  #]

def encoding_example():
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """
    
    BI = pybufr_ecmwf.BUFRInterfaceECMWF(max_nr_descriptors=20)
    
    # fill sections 0,1,2 and 3
    bufr_code_centre          =  98 # ECMWF
    bufr_obstype              =   3 # sounding
    bufr_subtype_L1B          = 251 # L1B
    bufr_table_local_version  =   1
    bufr_table_master         =   0
    bufr_table_master_version =  15
    bufr_code_subcentre       =   0 # L2B processing facility
    bufr_compression_flag     =   0 #  64=compression/0=no compression
    
    num_subsets = 4
    BI.fill_sections_0123(bufr_code_centre,
                          bufr_obstype,
                          bufr_subtype_L1B,
                          bufr_table_local_version,
                          bufr_table_master,
                          bufr_table_master_version,
                          bufr_code_subcentre,
                          num_subsets,
                          bufr_compression_flag)

    # determine information from sections 0123 to construct the BUFR table
    # names expected by the ECMWF BUFR library and create symlinks to the
    # default tables if needed
    BI.setup_tables()
        
    # define a descriptor list
    BT = pybufr_ecmwf.BufrTemplate(max_nr_descriptors=20)
    
    BT.add_descriptors(dd_d_date_YYYYMMDD, # 0
                       dd_d_time_HHMM)     # 1
    
    # delay replication for the next 2 descriptors
    # allow at most 5 delayed replications
    BT.add_delayed_replicated_descriptors(5,
                                          dd_pressure,
                                          dd_temperature)
    
    # replicate the next 2 descriptors 3 times
    BT.add_replicated_descriptors(3,
                                  dd_latitude_high_accuracy,
                                  dd_longitude_high_accuracy)

    BI.register_and_expand_descriptors(BT)
    
    # retrieve the length of the expanded descriptor list
    exp_descr_list_length = BI.ktdexl
    print "exp_descr_list_length = ",exp_descr_list_length
    
    # fill the values array with some dummy varying data
    num_values = exp_descr_list_length*num_subsets
    values = np.zeros(num_values,dtype=np.float64) # this is the default
    num_cvalues = 1 # just a dummy value
    cvals  = np.zeros((num_cvalues,80),dtype=np.character)
    
    for subset in range(num_subsets):
	# note that python starts counting with 0, unlike fortran,
	# so there is no need to take (subset-1)
	i=subset*exp_descr_list_length
	
	values[i]        = 1999 # year
	i=i+1; values[i] =   12 # month
	i=i+1; values[i] =   31 # day
	i=i+1; values[i] =   23 # hour
	i=i+1; values[i] =   59    -        subset # minute
	i=i+1; values[i] = 2 # delayed replication factor
	# this delayed replication factor determines the actual number
	# of values to be stored for this particular subset
	# even if it is less then the number given in kdata above !
	for repl in range(2):
	    i=i+1; values[i] = 1013.e2 - 100.e2*subset+i # pressure [pa]
	    i=i+1; values[i] = 273.15  -    10.*subset+i # temperature [K]
	for repl in range(3):
	    i=i+1; values[i] = 51.82   +   0.05*subset+i # latitude
	    i=i+1; values[i] =  5.25   +    0.1*subset+i # longitude
        
    BI.encode_data(values,cvals)


print "-"*50
print "BUFR encoding example"
print "-"*50

encoding_example()

print "-"*50
print "done"
print "-"*50
