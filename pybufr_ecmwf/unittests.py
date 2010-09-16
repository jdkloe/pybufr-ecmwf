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

from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
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

