#!/usr/bin/env python
"""
a module to execute unittests on all important pieces
of code in this module.
For the moment it mainly calls the example programs defined
in the example_programs directory, and compares the outputs to
stored expected outputs, but later more detailed unittests
are planned as well.
"""

#  #[ some notes
#
# Note about the use of the "#  #[" and "#  #]" comments:
#   these are folding marks for my favorite editor, emacs, combined with its
#   folding mode
#   (see http://www.emacswiki.org/emacs/FoldingMode for more details)
# Please do not remove them.
#
# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI (www.knmi.nl), Initial version 12-Nov-2009    
#
# License: GPL v2.
#
#  #]
#  #[ imported modules
import os          # operating system functions
#import sys         # system functions
import unittest  # import the unittest functionality

# import some home made helper routines
from helpers import call_cmd_and_verify_output, set_python_path
set_python_path()

from pybufr_ecmwf import BUFRInterfaceECMWF
from pybufr_ecmwf import RawBUFRFile
from pybufr_ecmwf import bufr

#import ecmwfbufr # import the wrapper module

#  #]

print "Starting test program:"

class CheckRawECMWFBUFR(unittest.TestCase):
    #  #[ 3 tests
    """
    a class to check the ecmwf_bufr_lib interface 
    """
    # note: tests MUST have a name starting with "test"
    #       otherwise the unittest module will not use them
    example_programs_dir = "example_programs/"
    def test_run_decoding_example(self):
        #  #[
        """
        run the decoding example program
        """
        # run the provided example code and verify the output
        testprog = "example_for_using_ecmwfbufr_for_decoding.py"
        cmd = os.path.join(self.example_programs_dir, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]
    def test_run_encoding_example(self):
        #  #[
        """
        run the encoding example program
        """
        # run the provided example code and verify the output
        testprog = "example_for_using_ecmwfbufr_for_encoding.py"
        cmd = os.path.join(self.example_programs_dir, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]
    def test_run_pb_routines_example(self):
        #  #[
        """
        run the pb routines example program
        """
        
        # NOTE: for debugging the pb-routines it is possible
        # to set the PBIO_PBOPEN environment setting to a value
        # of 1. From this it is clear that the pbopen code is
        # executed, and the problem is in the interfacingm which
        # leads to this error:
        #
        # SystemError: NULL result without error in PyObject_Call
        
        # run the provided example code and verify the output
        testprog = "example_for_using_pb_routines.py"
        cmd = os.path.join(self.example_programs_dir, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]
    #  #]

class CheckBUFRInterfaceECMWF(unittest.TestCase):
    #  #[ 4 tests
    """
    a class to check the bufr_interface_ecmwf class
    """
    # note: tests MUST have a name starting with "test"
    #       otherwise the unittest module will not use them
    example_programs_dir = "example_programs/"
    def test_init(self):
        #  #[
        """
        test instantiating the class
        """

        # just instantiate the class
        # since this was done already above, before starting the
        # sequence of unit tests, and since we omit the verbose
        # option, this should be silent
        bufr = BUFRInterfaceECMWF()
        
        # check its type
        checkbufr1 = isinstance(bufr, BUFRInterfaceECMWF)
        self.assertEqual(checkbufr1, True)
        checkbufr2 = isinstance(bufr, int)
        self.assertEqual(checkbufr2, False)
        
        # check that a call with a non-defined keyword fails
        self.assertRaises(TypeError,
                          BUFRInterfaceECMWF, dummy = 42)
        
        # todo: implement this (if this turns out to be important)
        # the module does no typechecking (yet) on its
        # inputs, so this one is not yet functional
        # self.assertRaises(TypeError,
        #                  BUFRInterfaceECMWF, verbose = 42)
        
        #  #]
    def test_get_exp_bufr_table_names(self):
        #  #[
        """
        test the get_expected_ecmwf_bufr_table_names method
        """
        
        center               = 210 # = ksec1( 3)
        subcenter            =   0 # = ksec1(16)
        local_version        =   1 # = ksec1( 8)
        master_table_version =   0 # = ksec1(15)
        edition_number       =   3 # =  ksec0( 3)
        master_table_number  =   0 # = ksec1(14)
        bufr = BUFRInterfaceECMWF()
        
        # dont use this! This would need an import of helpers
        # which in turn imports pybufr_ecmwf so would give a circular
        # dependency ...
        # ecmwf_bufr_tables_dir = helpers.get_tables_dir()

        this_path = os.path.split(__file__)[0]
        ecmwf_bufr_tables_dir = os.path.join(this_path, "ecmwf_bufrtables")
        if not os.path.exists(ecmwf_bufr_tables_dir):
            print "Error: could not find BUFR tables directory"
            raise IOError
        
        # make sure the path is absolute, otherwise the ECMWF library
        # might fail when it attempts to use it ...
        ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
        
        (btable, dtable) = \
                 bufr.get_expected_ecmwf_bufr_table_names(ecmwf_bufr_tables_dir,
                                                          center,
                                                          subcenter,
                                                          local_version,
                                                          master_table_version,
                                                          edition_number,
                                                          master_table_number)

        # print "tabel name B: ", btable
        # print "tabel name D: ", dtable
        self.assertEqual(btable, 'B0000000000210000001.TXT')
        self.assertEqual(dtable, 'D0000000000210000001.TXT')
        #  #]
    def test_run_decoding_example(self):
        #  #[
        """
        test the decoding example program
        """
        
        # run the provided example code and verify the output
        testprog = "example_for_using_bufrinterface_ecmwf_for_decoding.py"
        cmd = os.path.join(self.example_programs_dir, testprog)
        
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]
    def test_run_encoding_example(self):
        #  #[
        """
        test the encoding example program
        """

        # run the provided example code and verify the output
        testprog = "example_for_using_bufrinterface_ecmwf_for_encoding.py"
        cmd = os.path.join(self.example_programs_dir, testprog)
        
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]

    #  #]
            
class CheckRawBUFRFile(unittest.TestCase):
    #  #[ 4 tests
    """
    a class to check the raw_bufr_file class
    """
    # note: tests MUST have a name starting with "test"
    #       otherwise the unittest module will not use them
    #
    # common settings for the following tests
    input_test_bufr_file = 'testdata/Testfile3CorruptedMsgs.BUFR'
    def test_init(self):
        #  #[
        """
        test instantiating the class
        """
        bufrfile1 = RawBUFRFile(verbose = True)
        self.assertEqual(bufrfile1.bufr_fd, None)
        self.assertEqual(bufrfile1.filename, None)
        self.assertEqual(bufrfile1.filemode, None)
        self.assertEqual(bufrfile1.filesize, None)
        self.assertEqual(bufrfile1.data, None)
        self.assertEqual(bufrfile1.list_of_bufr_pointers, [])
        self.assertEqual(bufrfile1.nr_of_bufr_messages, 0)
        self.assertEqual(bufrfile1.last_used_msg, 0)
        self.assertEqual(bufrfile1.verbose, True)
        bufrfile2 = RawBUFRFile(verbose = False)
        self.assertEqual(bufrfile2.verbose, False)
        #  #]
    def test_open(self):
        #  #[
        """
        test opening a BUFR file
        """
        bufrfile = RawBUFRFile(verbose = False)
        
        # check behaviour when mode is missing
        self.assertRaises(TypeError,
                          bufrfile.open, self.input_test_bufr_file)
        
        # check behaviour when mode is invalid
        self.assertRaises(AssertionError,
                          bufrfile.open, self.input_test_bufr_file, 'q')
        
        # check behaviour when filename is not a string
        self.assertRaises(TypeError, bufrfile.open, 123, 'r')
        
        # check behaviour when file does not exist
        self.assertRaises(IOError, bufrfile.open, 'dummy', 'r',
                          silent = True)
        
        # check behaviour when reading a file without proper permission
        testfile = "tmp_testfile.read.BUFR"
        if (os.path.exists(testfile)):
            # force the file to be readwrite
            os.chmod(testfile, 0666)
            os.remove(testfile)

        # create a small dummy fle
        fdescr = open(testfile, 'wt')
        fdescr.write('dummy data')
        fdescr.close()
        # force the file to be unaccessible
        os.chmod(testfile, 0000)
        # do the test
        self.assertRaises(IOError, bufrfile.open, testfile, 'r',
                          silent = True)
        # cleanup
        if (os.path.exists(testfile)):
            # force the file to be readwrite
            os.chmod(testfile, 0666)
            os.remove(testfile)
            
        # check behaviour when writing to file without proper permission
        testfile = "tmp_testfile.write.BUFR"
        if (os.path.exists(testfile)):
            # force the file to be readwrite
            os.chmod(testfile, 0666)
            os.remove(testfile)

        # create a small dummy fle
        fdescr = open(testfile, 'wt')
        fdescr.write('dummy data')
        fdescr.close()
        # force the file to be readonly
        os.chmod(testfile, 0444)
        # do the test
        self.assertRaises(IOError, bufrfile.open, testfile, 'w',
                          silent = True)
        # cleanup
        if (os.path.exists(testfile)):
            # force the file to be readwrite
            os.chmod(testfile, 0666)
            os.remove(testfile)                
        #  #]
    def test_close(self):
        #  #[
        """
        test opening and closing a BUFR file
        """
        bufrfile = RawBUFRFile(verbose = False)
        bufrfile.open(self.input_test_bufr_file, 'r')
        bufrfile.close()
        
        # check that a second close fails
        self.assertRaises(AttributeError, bufrfile.close)
        #  #]
    def test_run_example(self):
        #  #[
        """
        test the example file for handling raw BUFR data
        """
        # run the provided example code and verify the output
        cmd = "example_programs/example_for_using_rawbufrfile.py"
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]
    #  #]

class CheckBufr(unittest.TestCase):
    #  #[
    # note: tests MUST have a name starting with "test"
    #       otherwise the unittest module will not use them
    def test_singleton(self):
        #  #[
        a = pybufr_ecmwf.bufr.Singleton(1)
        b = pybufr_ecmwf.bufr.Singleton(1)
        self.assertEqual(a is b,True)

        repr_a = repr(a)
        del(a)
        c = pybufr_ecmwf.bufr.Singleton(1)
        repr_c = repr(c)
        self.assertEqual(repr_a,repr_c)
        
        #  #]
    #  #]

# this just runs all tests
print "Running unit tests:"
unittest.main()

    
# still todo:
#
# add test calls to:
#   bupkey: pack ecmwf specific key into section 2
# and possibly to:
#   btable: tries to load a bufr-B table
#    [usefull for testing the presence of a needed table]
#   get_name_unit: get a name and unit string for a given descriptor
#   buprq: sets some switches that control the bufr library

#################################################
# ideas on how the module should/could be used: #
#################################################

#################################################
# reading a BUFR file
#################################################
#
# bf = BUFRFile(filename,'r')
# print bf.get_num_bufr_msgs()
# ==> 3
# print len(bf)
# ==> 3
#
# for msg in bf:
#    print msg
#    ==> BUFR msg holding 361 subsets of 44 descriptors
#    print len(msg)
#    ==>361
#    for subset in msg:
#      print subset
#      ==>BUFR MSG SUBSET holding 44 descriptors
#      print len(subset)
#      ==>44
#      for item in subset:
#         if item['name'] == 'LATITUDE (COARSE ACCURACY)':
#            print item.value
#            ==>-2.91
#    
#    x = msg.get_values('LATITUDE (COARSE ACCURACY)')  
#    print x
#    array([1.21,1.43,1.66,...])
#
#      
################################################

################################################
# creating a BUFR table from scratch
################################################
# 
# bt = BUFRtable()
# bt.add_B(key="011012", # also called "table reference"
#          name="WIND SPEED AT 10 M",
#          unit="M/S",
#          scale=1,      # also named "unit scale"
#          offset=0,     # also called "reference value"
#          numbits=12,   # also called "data width"
#          remark="some comment")
#
# ERROR: InvalidKeyError: only BUFR table B keys with FXXYYY reference
# numbers with above XX in the range 48-63 or YYY in the range 192-255
# are allowed to be redefined for local use. The other ranges are reserved
# for the official reference numbers as issued by WMO.
#
# (NOTE: for use of this format outside meteorology it might be usefull
#  to add a switch to allow this anyway)
#
# bt.add_B(key="063012", # also called "table reference"
#          name="MODIFIED WIND SPEED AT 10 M",
#          unit="CM/S",
#          scale=3,      # also named "unit scale"
#          offset=0,     # also called "reference value"
#          numbits=9,   # also called "data width"
#          remark="my own private wind speed definition")
#
# (should end succesfull)
#
# tm = BufrTemplate()
# tm.add_descriptors(dd_d_date_YYYYMMDD,
#                    dd_d_time_HHMM)
#
# bt.add_D(key="363255"
#          tmpl=tm,
#          remark="my remark")
#
# bt.copy_B(from="B0000000000210000001.TXT",
#           key="005001",
#           newkey="063001")
#
# bt.copy_B(from="B0000000000210000001.TXT",
#           newkey="006001") # newkey=key="006001" in this case
#
# bt.copy_D(from="D0000000000210000001.TXT",
#           key="300003"
#           newkey="363003")
#
# bt.copy_D(from="D0000000000210000001.TXT",
#           key="300004") # newkey=key="300004" in this case
#
# bt.save(filename_B,filename_D) # saves B and D tables
#
################################################

################################################
# see also:
# http://www.wmo.int/pages/prog/www/WMOCodes.html
# http://www.wmo.int/pages/prog/www/WMOCodes/BUFRTableB_112007.doc
# http://www.wmo.int/pages/prog/www/WMOCodes/Guides/BUFRCREXPreface_en.html
# for the official WMO documentation
#
# and
#
# http://www.ecmwf.int/products/data/software/bufr.html
# http://www.ecmwf.int/products/data/software/bufr_user_guide.pdf
# http://www.ecmwf.int/products/data/software/bufr_reference_manual.pdf
# for the ECMWF documentation
#
