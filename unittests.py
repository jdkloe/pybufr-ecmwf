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
# note: the tests in the test classes below MUST have a name starting 
#       with "test" otherwise the unittest module will not use them
#

#  #]
#  #[ pylint exceptions
#
# disable the warning on too many records, since here this
# is caused by the many methods in the unittest.TestCase
# class that is used for unit testing, and there is really
# nothing I can do to change this.
#
# disable warning: Too many public methods (../20)
# pylint: disable-msg=R0904
#
#  #]
#  #[ imported modules
import os, sys    # operating system functions
import unittest   # import the unittest functionality
import subprocess # support running additional executables
import glob       # support wildcard expansion on filenames
from build_interface import InterfaceBuildError

def get_and_set_the_module_path(syspath):
    #  #[
    """
    a little helper function to see where to import the module from,
    either the local directory or the build/lib.linux* directory
    """
    possible_so_files_1 = glob.glob(os.path.join('.',
                                                 'pybufr_ecmwf',
                                                 'ecmwfbufr.so'))
    possible_so_files_2 = glob.glob(os.path.join('.', 'build', 'lib*',
                                                 'pybufr_ecmwf',
                                                 'ecmwfbufr.so'))
    # print 'possible_so_files_1 = ',possible_so_files_1
    # print 'possible_so_files_2 = ',possible_so_files_2
    # sys.exit(1)
    
    if len(possible_so_files_1)>0:
        module_path = './'
    elif len(possible_so_files_2)>0:
        module_path = glob.glob(os.path.join('.', 'build', 'lib*'))[0]
    else:
        errtxt = 'could not find ecmwfbufr.so; '+\
                 'the interface seems not yet build!'
        raise InterfaceBuildError(errtxt)

    abs_module_path = os.path.abspath(module_path)
    print 'appending path: ', abs_module_path
    syspath.append(abs_module_path)

    if module_path != './':
        # remove the current dir from the path
        for spth in syspath:
            if os.path.abspath(spth)==os.path.abspath('./'):
                print 'removing path: ', os.path.abspath(spth)
                syspath.remove(spth)

    print 'syspath = ',syspath
    return abs_module_path
    #  #]

MY_MODULE_PATH = get_and_set_the_module_path(sys.path)
print 'TESTJOS: sys.path = ',sys.path

from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
# from pybufr_ecmwf import bufr
from pybufr_ecmwf import bufr_table
from pybufr_ecmwf import ecmwfbufr

#import ecmwfbufr # import the wrapper module

#  #]

def call_cmd_and_verify_output(cmd):
    #  #[
    """ a wrapper around run_shell_command for easier testing.
    It automatically constructs a name for the test output based
    on the class and function name from which it was called.
    Then it executes the test function and redirects the stdout and
    stderr outputs to files with the just constructed names.
    Finally it compares the actual test outputs with expected outputs
    that should be present in the current directory.
    If the outputs are as expected the function returns True,
    otherwise False."""

    # disable the "Too many local variables" pylint warning
    # since I feel this helper routine really could not be
    # rewritten using less local variables
    #
    # pylint: disable-msg=R0914

    # assume at first that all will work as planned
    success = True

    #  #[ some old notes
    #print "__name__ = ", __name__
    #print "__file__ = ", __file__
    #print "self.__class__.__name__ = ", self.__class__.__name__
    #print "func_filename = ", sys._getframe().f_code.co_filename
    #print "func_name = ", sys._getframe().f_code.co_name
    #print "dir(frame) = ", dir(sys._getframe())
    #print "dir(f_code) = ", dir(sys._getframe().f_code)
    #print "0:callers name = ", sys._getframe(0).f_code.co_name
    #
    #print "2:callers name = ", sys._getframe(2).f_code.co_name
    #sys.exit(1)
    # see: http://code.activestate.com/recipes/66062/
    # for more examples on using sys._getframe()
    #  #]
    
    # determine the full path of the current python interpreter
    # python_interpreter = sys.executable

    # disable the pylint warning:
    # "Access to a protected member _getframe of a client class"
    # pylint: disable-msg=W0212

    # determine the name of the calling function
    name_of_calling_function = sys._getframe(1).f_code.co_name

    # determine the name of the class that defines the calling function
    classname_of_calling_function = \
                 sys._getframe(1).f_locals['self'].__class__.__name__

    # pylint: enable-msg=W0212

    # construct filenames for the actual and expected outputs
    basename = os.path.join("example_programs/expected_test_outputs",
                            classname_of_calling_function+"."+\
                            name_of_calling_function)
    actual_stdout   = basename+".actual_stdout"
    actual_stderr   = basename+".actual_stderr"
    expected_stdout = basename+".expected_stdout"
    expected_stderr = basename+".expected_stderr"

    # get the list of already defined env settings
    env = os.environ
    if (env.has_key('PYTHONPATH')):
        env['PYTHONPATH'] = env['PYTHONPATH']+':'+MY_MODULE_PATH
    else:
        env['PYTHONPATH'] = MY_MODULE_PATH
        
    # execute the test and catch all output
    subpr = subprocess.Popen(cmd,
                             shell  = True,
                             env    = env,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE)
    lines_stdout = subpr.stdout.readlines()
    lines_stderr = subpr.stderr.readlines()

    # write the actual outputs to file
    file_descr = open(actual_stdout, 'wt')
    file_descr.writelines(lines_stdout)
    file_descr.close()

    file_descr = open(actual_stderr, 'wt')
    file_descr.writelines(lines_stderr)
    file_descr.close()
    
    # try to read the expected outputs
    try:
        expected_lines_stdout = open(expected_stdout, 'rt').readlines()
        expected_lines_stderr = open(expected_stderr, 'rt').readlines()
    
        # compare the actual and expected outputs
        if not (lines_stdout == expected_lines_stdout):
            print "stdout differs from what was expected!!!"
            print "to find out what happended execute this diff command:"
            print "xdiff ", actual_stdout, ' ', expected_stdout
            success = False
            
        if not (lines_stderr == expected_lines_stderr):
            print "stderr differs from what was expected!!!"
            print "to find out what happended execute this diff command:"
            print "xdiff ", actual_stderr, ' ', expected_stderr
            success = False
    except IOError:
        print "ERROR: expected output not found; probably because"
        print "you just defined a new unittest case."
        print "Missing filenames:"
        if not os.path.exists(expected_stdout):
            print "expected_stdout: ", expected_stdout
            print "(actual output available in: ", actual_stdout, ")"
        if not os.path.exists(expected_stderr):
            print "expected_stderr: ", expected_stderr
            print "(actual output available in: ", actual_stderr, ")"
        success = False
        
    return success

    # enable the "Too many local variables" warning again
    # pylint: enable-msg=R0914
    #  #]

print "Starting test program:"

class CheckRawECMWFBUFR(unittest.TestCase):
    #  #[ 3 tests
    """
    a class to check the ecmwf_bufr_lib interface 
    """
    example_programs_dir   = 'example_programs'
    testdatadir            = 'example_programs/testdata'
    testinputfile          = os.path.join(testdatadir,
                                          'Testfile.BUFR')
    corruptedtestinputfile = os.path.join(testdatadir,
                                          'Testfile3CorruptedMsgs.BUFR')
    testoutputfile2u       = os.path.join(testdatadir,
                                          'Testoutputfile2u.BUFR')

    def test_run_decoding_example(self):
        #  #[
        """
        run the decoding example program
        """
        # run the provided example code and verify the output
        testprog = "example_for_using_ecmwfbufr_for_decoding.py"
        cmd = os.path.join(self.example_programs_dir, testprog)
        cmd = cmd + ' ' + self.testinputfile
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                

        # unfortunately the next check is impossible because the
        # fort.12 file holding the fortran stdout seems only closed/flushed
        # after the end of this python script, causing inpredictible results.
        # Note that the example_for_using_bufrinterface_ecmwf_for_decoding
        # and example_for_using_bufrinterface_ecmwf_for_encoding tests
        # use the bufr_interface_ecmwf.py module which implement an explicit
        # close of the fortran file used for stdout, so in these tests
        # the actual text output of the ecmwf bufr library routines is
        # tested as well.

        # verify the output to the 'fort.12' file
        #success = True
        #expected_stdout = \
        #   os.path.join("example_programs/expected_test_outputs",
        #                'CheckRawECMWFBUFR.test_run_decoding_example.fort.12')
        #actual_stdout = 'fort.12'
        #try:
        #    # try to read the actual and expected outputs
        #    expected_lines_stdout = open(expected_stdout, 'rt').readlines()
        #    lines_stdout = open(actual_stdout, 'rt').readlines()
        #
        #    # compare the actual and expected outputs
        #    if not (lines_stdout == expected_lines_stdout):
        #        print "stdout differs from what was expected!!!"
        #        print "to find out what happended execute this diff command:"
        #        cmd = "xdiff "+actual_stdout+' '+expected_stdout
        #        print cmd
        #        # os.system(cmd)
        #        success = False
        #    
        #except IOError:
        #    print "ERROR: expected output not found; probably because"
        #    print "you just defined a new unittest case."
        #    print "Missing filename:"
        #    if not os.path.exists(expected_stdout):
        #        print "expected_stdout: ", expected_stdout
        #        print "(actual output available in: ", actual_stdout, ")"
        #    success = False
        #
        #self.assertEqual(success, True)

        os.remove('fort.12')
        #  #]
    def test_run_encoding_example(self):
        #  #[
        """
        run the encoding example program
        """
        # run the provided example code and verify the output
        testprog = "example_for_using_ecmwfbufr_for_encoding.py"
        cmd = os.path.join(self.example_programs_dir, testprog)
        cmd = cmd + ' ' + self.testoutputfile2u
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                

        # see also the note on why the 'fort.12' redirected stdout is
        # not tested in the test_run_decoding_example method above.

        os.remove('fort.12')

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
        cmd = cmd + ' ' + self.corruptedtestinputfile
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]
    #  #]

class CheckBUFRInterfaceECMWF(unittest.TestCase):
    #  #[ 4 tests
    """
    a class to check the bufr_interface_ecmwf class
    """
    example_programs_dir   = "example_programs"
    testdatadir            = 'example_programs/testdata'
    testinputfile          = os.path.join(testdatadir,
                                          'Testfile.BUFR')
    testoutputfile1u       = os.path.join(testdatadir,
                                          'Testoutputfile1u.BUFR')
    def test_init(self):
        #  #[
        """
        test instantiating the class
        """

        # just instantiate the class
        # since this was done already above, before starting the
        # sequence of unit tests, and since we omit the verbose
        # option, this should be silent
        bufrobj = BUFRInterfaceECMWF()
        
        # check its type
        checkbufr1 = isinstance(bufrobj, BUFRInterfaceECMWF)
        self.assertEqual(checkbufr1, True)
        checkbufr2 = isinstance(bufrobj, int)
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
        bufrobj = BUFRInterfaceECMWF()

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
            print "Error: could not find BUFR tables directory"
            raise IOError

        # make sure the path is absolute, otherwise the ECMWF library
        # might fail when it attempts to use it ...
        ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
        
        (btable, dtable) = \
                 bufrobj.get_expected_ecmwf_bufr_table_names(\
                             ecmwf_bufr_tables_dir,
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
        cmd = cmd + ' ' + self.testinputfile

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
        cmd = cmd + ' ' + self.testoutputfile1u
        
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]
    def test_run_extract_data_category(self):
        #  #[
        """
        test the bufr_extract_data_category example program
        """

        # run the provided example code and verify the output
        testprog = "bufr_extract_data_category.py"
        cmd = os.path.join(self.example_programs_dir, testprog)
        cmd = cmd + ' ' + self.testinputfile
        
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]

    #  #]
            
class CheckRawBUFRFile(unittest.TestCase):
    #  #[ 4 tests
    """
    a class to check the raw_bufr_file class
    """
    # common settings for the following tests
    example_programs_dir   = "example_programs"
    testdatadir            = 'example_programs/testdata'
    testinputfile          = os.path.join(testdatadir,
                                          'Testfile.BUFR')
    corruptedtestinputfile = os.path.join(testdatadir,
                                          'Testfile3CorruptedMsgs.BUFR')
    testoutputfile3u       = os.path.join(testdatadir,
                                          'Testoutputfile3u.BUFR')

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
                          bufrfile.open, self.corruptedtestinputfile)
        
        # check behaviour when mode is invalid
        self.assertRaises(AssertionError,
                          bufrfile.open, self.corruptedtestinputfile, 'q')
        
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

        # create a small dummy file
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
        bufrfile.open(self.corruptedtestinputfile, 'r')
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
        cmd = cmd + ' ' + self.corruptedtestinputfile + \
              ' ' + self.testoutputfile3u
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]
    def test_run_count_msgs(self):
        #  #[
        """
        test the example file for counting BUFR messages in a file
        """
        # run the provided example code and verify the output
        cmd = "example_programs/bufr_count_msgs.py"
        cmd = cmd + ' ' + self.testinputfile
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)                
        #  #]
    #  #]

class CheckBufrTable(unittest.TestCase):
    #  #[
    """
    a class to check the bufr_table.py file
    """
    def test_singleton(self):
        #  #[
        """
        check the implementation of the singletom class in bufr.py
        """
        aaa = bufr_table.Singleton(1)
        bbb = bufr_table.Singleton(1)
        self.assertEqual(aaa is bbb, True)

        repr_aaa = repr(aaa)
        del(aaa)
        ccc = bufr_table.Singleton(1)
        repr_ccc = repr(ccc)
        self.assertEqual(repr_aaa, repr_ccc)
        
        #  #]
    #  #]

class CheckBufr(unittest.TestCase):
    #  #[
    """
    a class to check the bufr.py file
    """
    # common settings for the following tests
    example_programs_dir   = "example_programs"
    testdatadir            = 'example_programs/testdata'
    testinputfile          = os.path.join(testdatadir,
                                          'Testfile.BUFR')
    def test_run_decoding_example(self):
        #  #[
        """
        test the decoding example program
        """
        
        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(self.example_programs_dir, testprog)
        cmd = cmd + ' ' + self.testinputfile

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
