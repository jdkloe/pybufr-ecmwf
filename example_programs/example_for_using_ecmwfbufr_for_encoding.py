#!/usr/bin/env python

"""
This is a small example program intended to demonstrate
how the raw wrapper interface to the ECMWF BUFR library may be
used for encoding a BUFR message.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 21-Jan-2010
#
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

#  #[ pylint exceptions
#
# the whole point of this example program is to demonstrate that
# using the bare interface costs an awfull lot of lines of code to
# get things working properly.
# Therefore I don't want pylint to start complaining about using
# too many lines or variables here, so disable these warnings:
#
# disable warning: "Too many local variables"
# pylint: disable=R0914
#
# disable warning: "Too many statements"
# pylint: disable=R0915
#
#  #]
#  #[ imported modules
from __future__ import print_function
import os, sys     # operating system functions
import numpy as np # import numerical capabilities
import time        # handling of date and time

# import the RawBUFRFile class to write the encoded raw BUFR data to file
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile

# import the raw wrapper interface to the ECMWF BUFR library
from pybufr_ecmwf import ecmwfbufr
#  #]

def ensure_symlink_exists(source, destination):
    #  #[
    """ a little helper function for creating symlinks in
    case they are not yet present, to avoid duplicate code
    or pylint to complain about to many branches """
    if not os.path.exists(destination):
        os.symlink(source, destination)
    #  #]

def encoding_example(output_bufr_file):
    #  #[
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """
    # define the needed constants
    max_nr_descriptors = 20 # 300
    max_nr_expanded_descriptors = 140 # 160000
    max_nr_subsets = 361 # 25

    ktdlen = max_nr_descriptors
    # krdlen = max_nr_delayed_replication_factors
    kelem = max_nr_expanded_descriptors
    kvals = max_nr_expanded_descriptors*max_nr_subsets
    # jbufl  = max_bufr_msg_size
    # jsup   = length_ksup

    #  initialise all arrays
    print('------------------------------')
    print('reinitialising all arrays...')
    print('------------------------------')
    #ksup   = np.zeros(          9, dtype = np.int)
    ksec0 = np.zeros(3, dtype=np.int)
    ksec1 = np.zeros(40, dtype=np.int)
    ksec2 = np.zeros(4096, dtype=np.int)
    #key    = np.zeros(         52, dtype = np.int)
    ksec3 = np.zeros(4, dtype=np.int)
    ksec4 = np.zeros(2, dtype=np.int)
    cnames = np.zeros((kelem, 64), dtype=np.character)
    cunits = np.zeros((kelem, 24), dtype=np.character)
    values = np.zeros(kvals, dtype=np.float64) # this is the default
    cvals = np.zeros((kvals, 80), dtype=np.character)
    ktdlen = 0
    ktdlst = np.zeros(max_nr_descriptors, dtype=np.int)
    ktdexl = 0
    ktdexp = np.zeros(max_nr_expanded_descriptors, dtype=np.int)
    kerr = 0

    # handle BUFR tables
    print('------------------------------')

    # define our own location for storing (symlinks to) the BUFR tables
    private_bufr_tables_dir = os.path.abspath("./tmp_BUFR_TABLES")
    if not os.path.exists(private_bufr_tables_dir):
        os.mkdir(private_bufr_tables_dir)

    # make the needed symlinks to bufr tables

    # inspect the location of the ecmwfbufr.so file, and derive
    # from this the location of the BUFR tables that are delivered
    # with the ECMWF BUFR library software
    ecmwfbufr_path = os.path.split(ecmwfbufr.__file__)[0]
    path1 = os.path.join(ecmwfbufr_path, "ecmwf_bufrtables")
    path2 = os.path.join(ecmwfbufr_path, '..', "ecmwf_bufrtables")

    if os.path.exists(path1):
        ecmwf_bufr_tables_dir = path1
    elif os.path.exists(path2):
        ecmwf_bufr_tables_dir = path2
    else:
        print("Error: could not find BUFR tables directory")
        raise IOError

    # make sure the path is absolute, otherwise the ECMWF library
    # might fail when it attempts to use it ...
    ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)

    needed_b_table = "B0000000000098015001.TXT"
    needed_d_table = "D0000000000098015001.TXT"
    available_b_table = "B0000000000098013001.TXT"
    available_d_table = "D0000000000098013001.TXT"

    source = os.path.join(ecmwf_bufr_tables_dir, available_b_table)
    destination = os.path.join(private_bufr_tables_dir, needed_b_table)
    ensure_symlink_exists(source, destination)

    source = os.path.join(ecmwf_bufr_tables_dir, available_d_table)
    destination = os.path.join(private_bufr_tables_dir, needed_d_table)
    ensure_symlink_exists(source, destination)

    # make sure the BUFR tables can be found
    # also, force a slash at the end, otherwise the library fails
    # to find the tables
    envir = os.environ
    envir["BUFR_TABLES"] = private_bufr_tables_dir+os.path.sep

    # redirect all fortran stdout to fileunit 12, so the text
    # will end-up in a file called 'fort.12'
    # This is needed to get reproducible output for my unittests.
    # Without this trick the stdout stream from fortran and the stdout
    # stream from c/python may be mixed in inpredictable ways
    # (depending on the size of the buffer used to store the streams)
    os.environ['STD_OUT'] = '12'

    # suppres the default ECMWF welcome message which
    # is not yet redirected to the above defined fileunit
    os.environ['PRINT_TABLE_NAMES'] = 'FALSE'

    # fill sections 0,1,2 and 3
    bufr_edition = 4
    bufr_code_centre = 98 # ECMWF
    bufr_obstype = 3 # sounding
    bufr_subtype_l1b = 251 # L1B
    bufr_table_local_version = 1
    bufr_table_master = 0
    bufr_table_master_version = 15
    bufr_code_subcentre = 0 # L2B processing facility
    bufr_compression_flag = 0 # 64=compression/0=no compression

    (year, month, day, hour, minute) = time.localtime()[:5]
    #(year, month, day, hour, minute, second,
    # weekday, julianday, isdaylightsavingstime) = time.localtime()

    num_subsets = 4

    # fill section 0
    ksec0[1-1] = 0
    ksec0[2-1] = 0
    ksec0[3-1] = bufr_edition

    # fill section 1
    ksec1[1-1] = 22                       # length sec1 bytes
    #                                        [filled by the encoder]
    # however,a minimum of 22 is obliged here
    ksec1[2-1] = bufr_edition              # bufr edition
    ksec1[3-1] = bufr_code_centre          # originating centre
    ksec1[4-1] = 1                       # update sequence
    ksec1[5-1] = 0                       # (PRESENCE SECT 2)
    #                                        (0/128 = no/yes)
    ksec1[6-1] = bufr_obstype              # message type
    ksec1[7-1] = bufr_subtype_l1b          # subtype
    ksec1[8-1] = bufr_table_local_version  # version of local table
    ksec1[9-1] = (year-2000)               # Without offset year - 2000
    ksec1[10-1] = month                     # month
    ksec1[11-1] = day                       # day
    ksec1[12-1] = hour                      # hour
    ksec1[13-1] = minute                    # minute
    ksec1[14-1] = bufr_table_master         # master table
    ksec1[15-1] = bufr_table_master_version # version of master table
    ksec1[16-1] = bufr_code_subcentre       # originating subcentre
    ksec1[17-1] = 0
    ksec1[18-1] = 0

    # a test for ksec2 is not yet defined

    # fill section 3
    ksec3[1-1] = 0
    ksec3[2-1] = 0
    ksec3[3-1] = num_subsets                # no of data subsets
    ksec3[4-1] = bufr_compression_flag      # compression flag

    # define a descriptor list
    ktdlen = 9 # length of unexpanded descriptor list
    ktdlst = np.zeros(ktdlen, dtype=np.int)

    # define descriptor 1
    dd_d_date_yyyymmdd = 301011 # date
    # this defines the sequence:
    # 004001 ! year
    # 004002 ! month
    # 004003 ! day

    # define descriptor 2
    dd_d_time_hhmm = 301012 # time
    # this defines the sequence:
    # 004004 ! hour
    # 004005 ! minute

    # define descriptor 3
    dd_pressure = int('007004', 10) # pressure [pa]

    # WARNING: filling the descriptor variable with 007004 will fail
    # because python will interpret this as an octal value, and thus
    # automatically convert 007004 to the decimal value 3588

    # define descriptor 4
    dd_temperature = int('012001', 10) # [dry-bulb] temperature [K]

    # define descriptor 5
    dd_latitude_high_accuracy = int('005001', 10)
    # latitude (high accuracy) [degree]

    # define descriptor 6
    dd_longitude_high_accuracy = int('006001', 10)
    # longitude (high accuracy) [degree]

    # define the delayed replication code
    delayed_descr_repl_factor = int('031001', 10)

    def get_replication_code(num_descriptors, num_repeats):
        """
        calculate the replication note needed to describe
        how many times a descriptor sequence is to be repeated
        """
        repl_factor = 100000 + num_descriptors*1000 + num_repeats
        # for example replicating 2 descriptors 25 times will
        # be encoded as: 102025
        # for delayed replication, set num_repeats to 0
        # then add the delayed_descr_repl_factor after this code
        return repl_factor

    ktdlst[0] = dd_d_date_yyyymmdd
    ktdlst[1] = dd_d_time_hhmm

    # delay replication for the next 2 descriptors
    ktdlst[2] = get_replication_code(2, 0)
    ktdlst[3] = delayed_descr_repl_factor # = 031001

    ktdlst[4] = dd_pressure
    ktdlst[5] = dd_temperature

    # replicate the next 2 descriptors 3 times
    ktdlst[6] = get_replication_code(2, 3)

    ktdlst[7] = dd_latitude_high_accuracy
    ktdlst[8] = dd_longitude_high_accuracy

    # call BUXDES
    # buxdes: expand the descriptor list
    #         and fill the array ktdexp and the variable ktdexp
    #         [only usefull when creating a bufr msg with table D entries

    # iprint = 0 # default is to be silent
    iprint = 1
    if iprint == 1:
        print("------------------------")
        print(" printing BUFR template ")
        print("------------------------")

    # define and fill the list of replication factors
    num_del_repl_factors = 1
    kdata = np.zeros(num_subsets*num_del_repl_factors, dtype=np.int)
    for i in range(num_subsets):
        # Warning: just set the whole array to the maximum you wish to have.
        # Letting this number vary seems not to work with the current
        # ECMWF library. It will allways just look at the first element
        # in the kdata array. (or do I misunderstand the BUFR format here?)
        kdata[i] = 2 # i+1
    print("delayed replication factors: ", kdata)

    ecmwfbufr.buxdes(iprint, ksec1, ktdlst, kdata,
                     ktdexl, ktdexp, cnames, cunits, kerr)
    print("ktdlst = ", ktdlst)
    selection = np.where(ktdexp > 0)
    #print("selection = ",selection)
    print("ktdexp = ", ktdexp[selection])
    print("ktdexl = ", ktdexl) # this one seems not to be filled ...?
    if kerr != 0:
        print("kerr = ", kerr)
        sys.exit(1)

    # print("cnames = ", cnames)
    # print("cunits = ", cunits)

    # retrieve the length of the expanded descriptor list
    exp_descr_list_length = len(np.where(ktdexp > 0)[0])
    print("exp_descr_list_length = ", exp_descr_list_length)

    # fill the values array with some dummy varying data
    num_values = exp_descr_list_length*num_subsets
    values = np.zeros(num_values, dtype=np.float64) # this is the default

    for subset in range(num_subsets):
        # note that python starts counting with 0, unlike fortran,
        # so there is no need to take (subset-1)
        i = subset*exp_descr_list_length
        values[i] = 1999 # year

        i = i+1
        values[i] = 12 # month

        i = i+1
        values[i] = 31 # day

        i = i+1
        values[i] = 23 # hour

        i = i+1
        values[i] = 59 - subset # minute

        i = i+1
        values[i] = 2 # delayed replication factor
        # this delayed replication factor determines the actual number
        # of values to be stored for this particular subset
        # even if it is less then the number given in kdata above !
        for repl in range(2):
            i = i+1
            values[i] = 1013.e2 - 100.e2*subset+i+repl # pressure [pa]

            i = i+1
            values[i] = 273.15 - 10.*subset+i+repl # temperature [K]

        for repl in range(3):
            i = i+1
            values[i] = 51.82 + 0.05*subset+i+repl # latitude

            i = i+1
            values[i] = 5.25 + 0.1*subset+i+repl # longitude

    # call BUFREN
    #   bufren: encode a bufr message
    #sizewords = 200
    #kbuff = np.zeros(num_values, dtype = np.int)
    cvals = np.zeros((num_values, 80), dtype=np.character)
    # define the output buffer
    num_bytes = 5000
    num_words = num_bytes/4
    words = np.zeros(num_words, dtype=np.int)

    ecmwfbufr.bufren(ksec0, ksec1, ksec2, ksec3, ksec4,
                     ktdlst, kdata, exp_descr_list_length,
                     values, cvals, words, kerr)

    print("bufren call finished")
    if kerr != 0:
        print("kerr = ", kerr)
        sys.exit(1)

    print("words=")
    print(words)

    nonzero_locations = np.where(words != 0)
    #print('nonzero_locations = ',nonzero_locations[0])

    numwords = nonzero_locations[0][-1] + 1
    print("encoded size: ", numwords, " words or ", numwords*4, " bytes")

    encoded_message = words[:numwords]

    # get an instance of the RawBUFRFile class
    bf1 = RawBUFRFile()
    # open the file for writing
    bf1.open(output_bufr_file, 'wb')
    # write the encoded BUFR message
    bf1.write_raw_bufr_msg(encoded_message)
    # close the file
    bf1.close()
    #  #]

#  #[ run the example
if len(sys.argv) < 2:
    print('please give a BUFR file as first argument')
    sys.exit(1)

OUTP_BUFR_FILE = sys.argv[1]

# make sure the outputfile does not yet exist
if os.path.exists(OUTP_BUFR_FILE):
    os.remove(OUTP_BUFR_FILE)

print("-"*50)
print("BUFR encoding example")
print("-"*50)

encoding_example(OUTP_BUFR_FILE)
print('succesfully written BUFR encoded data to file: ', OUTP_BUFR_FILE)

print("-"*50)
print("done")
print("-"*50)
#  #]
