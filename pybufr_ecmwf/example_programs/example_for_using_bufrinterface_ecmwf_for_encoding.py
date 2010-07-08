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


print "-"*50
print "BUFR encoding example"
print "-"*50

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
			  bufr_code_subcentre)
    
    
    # a test for ksec2 is not yet defined
    
    # fill section 3
    ksec3[1-1]= 0
    ksec3[2-1]= 0
    ksec3[3-1]= num_subsets                # no of data subsets
    ksec3[4-1]= bufr_compression_flag      # compression flag
    
    # define a descriptor list
    ktdlen = 9 # length of unexpanded descriptor list
    ktdlst = np.zeros(ktdlen,dtype=np.int)
    
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
    
    # define the delayed replication code
    Delayed_Descr_Repl_Factor = int('031001',10)
    
    def get_replication_code(num_descriptors,num_repeats):
	repl_factor = 100000 + num_descriptors*1000 + num_repeats
	# for example replicating 2 descriptors 25 times will be encoded as: 102025
	# for delayed replication, set num_repeats to 0
	# then add the Delayed_Descr_Repl_Factor after this code
	return repl_factor

    ktdlst[0] = dd_d_date_YYYYMMDD
    ktdlst[1] = dd_d_time_HHMM
    
    # delay replication for the next 2 descriptors
    ktdlst[2] = get_replication_code(2,0)
    ktdlst[3] = Delayed_Descr_Repl_Factor # = 031001
    
    ktdlst[4] = dd_pressure
    ktdlst[5] = dd_temperature
    
    # replicate the next 2 descriptors 3 times
    ktdlst[6] = get_replication_code(2,3)
    
    ktdlst[7] = dd_latitude_high_accuracy
    ktdlst[8] = dd_longitude_high_accuracy
    
    # call BUXDES
    # buxdes: expand the descriptor list
    #         and fill the array ktdexp and the variable ktdexp
    #         [only usefull when creating a bufr msg with table D entries
    
    # iprint=0 # default is to be silent
    iprint=1
    if (iprint == 1):
	print "------------------------"
	print " printing BUFR template "
	print "------------------------"
	
    # define and fill the list of replication factors
    num_del_repl_factors = 1
    kdata = np.zeros(num_subsets*num_del_repl_factors,dtype=np.int)
    for i in range(num_subsets):
	# Warning: just set the whole array to the maximum you wish to have.
	# Letting this number vary seems not to work with the current
	# ECMWF library. It will allways just look at the first element
	# in the kdata array. (or do I misunderstand the BUFR format here?)
	kdata[i] = 2 # i+1
    print "delayed replication factors: ",kdata
    
    ecmwfbufr.buxdes(iprint,ksec1,ktdlst,kdata,
		     ktdexl,ktdexp,cnames,cunits,kerr)
    print "ktdlst = ",ktdlst
    selection = np.where(ktdexp>0)
    print "ktdexp = ",ktdexp[selection]
    print "ktdexl = ",ktdexl # this one seems not to be filled ...?
    if (kerr != 0):
	print "kerr = ",kerr
	sys.exit(1)

    # print "cnames = ",cnames
    # print "cunits = ",cunits
    
    # retrieve the length of the expanded descriptor list
    exp_descr_list_length = len(np.where(ktdexp>0)[0])
    print "exp_descr_list_length = ",exp_descr_list_length
    
    # fill the values array with some dummy varying data
    num_values = exp_descr_list_length*num_subsets
    values = np.zeros(num_values,dtype=np.float64) # this is the default
    
    #values = np.zeros(     kvals,dtype=np.float64) # this is the default
    #cvals  = np.zeros((kvals,80),dtype=np.character)
    
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
        
    # call BUFREN
    #   bufren: encode a bufr message
    sizewords = 200
    kbuff = np.zeros(num_values,dtype=np.int)
    cvals = np.zeros((num_values,80),dtype=np.character)
    # define the output buffer
    num_bytes = 5000
    num_words = 4*num_bytes
    words = np.zeros(num_words,dtype=np.int)
    
    print "kvals = ",kvals
    print "cvals = ",cvals
    ecmwfbufr.bufren(ksec0,ksec1,ksec2,ksec3,ksec4,
		     ktdlst,kdata,exp_descr_list_length,
		     values,cvals,words,kerr)
    print "bufren call finished"
    if (kerr != 0):
	print "kerr = ",kerr
	sys.exit(1)

    print "words="
    print words
    nw = len(np.where(words>0)[0])
    print "encoded size: ",nw," words or ",nw*4," bytes"


print "-"*50
print "BUFR encoding example"
print "-"*50

encoding_example()
