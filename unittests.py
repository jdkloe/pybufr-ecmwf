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
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html
#
# note: the tests in the test classes below MUST have a name starting
#       with "test" otherwise the unittest module will not use them
#

# note for debugging:
# run a single testcase like this:
# ./unittests.py CheckBUFRWriter.test_run_unknown_descriptor_case

#  #]
#  #[ pylint exceptions
#
# disable the warning on too many records, since here this
# is caused by the many methods in the unittest.TestCase
# class that is used for unit testing, and there is really
# nothing I can do to change this.
#
# disable warning: Too many public methods (../20)
# pylint: disable=R0904
#
#  #]
#  #[ imported modules
from __future__ import (absolute_import, division,
                        print_function) # , unicode_literals)

import os         # operating system functions
import sys        # operating system functions
import shutil     # operating system functions
import unittest   # import the unittest functionality
import subprocess # support running additional executables
import stat       # to retrieve a file modification timestamp
import time       # to handle date/time formatting

from pybufr_ecmwf.helpers import get_and_set_the_module_path
from pybufr_ecmwf.custom_exceptions import IncorrectUsageError

DUMMY_SYS_PATH = sys.path[:] # provide a copy
(DUMMY_SYS_PATH, MY_MODULE_PATH) = get_and_set_the_module_path(DUMMY_SYS_PATH)
# print '(sys.path, MY_MODULE_PATH) = ',(sys.path, MY_MODULE_PATH)

# in case the build is done by setup.py, the created ecmwfbufr.so module will
# be in a path like SWROOT/build/lib.linux-x86_64-2.7/pybufr_ecmwf/
# To ensure the unittests find it, temporarily rename SWROOT/pybufr_ecmwf/
# and create a symlink to SWROOT/build/lib.linux-x86_64-2.7/pybufr_ecmwf/
PYBUFR_ECMWF_MODULE_WAS_RENAMED = False
if 'build/lib' in MY_MODULE_PATH:
    print('renaming pybufr_ecmwf to pybufr_ecmwf.renamed')
    shutil.move('pybufr_ecmwf', 'pybufr_ecmwf.renamed')
    print('creating symlink pybufr_ecmwf')
    os.symlink(os.path.join(MY_MODULE_PATH, 'pybufr_ecmwf'), # source
               'pybufr_ecmwf') # destination
    PYBUFR_ECMWF_MODULE_WAS_RENAMED = True
#else:
#    print('MY_MODULE_PATH = ', MY_MODULE_PATH)

try:
    from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
    from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
    # from pybufr_ecmwf import bufr
    # from pybufr_ecmwf import bufr_table
    from pybufr_ecmwf import ecmwfbufr
except (SyntaxError, ImportError):  # as err:
    # ensure the code reaches the point where the pybufr_ecmwf.renamed
    # is renamed back to pybufr_ecmwf, so allow imports to fail
    print('ERROR: some imports failed!!!')
    # print('Error was: '+str(err))
    # pass
    # raise

#import ecmwfbufr # import the wrapper module

#  #]
#  #[ some constants
EXAMPLE_PROGRAMS_DIR = 'example_programs'
TEST_DIR = 'test'
TESTDATADIR = os.path.join(TEST_DIR, 'testdata')
EXP_OUTP_DIR = os.path.join(TEST_DIR, 'expected_test_outputs')
ACT_OUTP_DIR = os.path.join(TEST_DIR, 'actual_test_outputs')

if not os.path.exists(ACT_OUTP_DIR):
    os.mkdir(ACT_OUTP_DIR)
#  #]

def call_cmd(cmd, rundir=''):
    #  #[ do the actual call to an external test script
    """ a wrapper around run_shell_command for easier testing.
    It sets the environment setting PYTHONPATH to allow the
    code to find the current pybufr-ecmwf library"""

    # get the list of already defined env settings
    env = os.environ
    if 'PYTHONPATH' in env:
        settings = env['PYTHONPATH'].split(':')
        if not MY_MODULE_PATH in settings:
            env['PYTHONPATH'] = MY_MODULE_PATH+':'+env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = MY_MODULE_PATH

    if use_eccodes:
        env['PYBUFR_ECMWF_USE_ECCODES'] = 'True'
    else:
        env['PYBUFR_ECMWF_USE_ECCODES'] = 'False'
        

    # print('DEBUG: env[PYTHONPATH] = ',env['PYTHONPATH'])
    # print('DEBUG: env[BUFR_TABLES] = ',env.get('BUFR_TABLES','undefined'))
    # print('DEBUG: cmd = ',cmd)

    # remove the env setting to
    # /tmp/pybufr_ecmwf_temporary_files_*/tmp_BUFR_TABLES/
    # that may have been left by a previous test
    if 'BUFR_TABLES' in env:
        del env['BUFR_TABLES']

    # change dir if needed
    if rundir:
        cwd = os.getcwd()
        os.chdir(rundir)

    # execute the test and catch all output
    subpr = subprocess.Popen(cmd, shell=True, env=env,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    lines_stdout = subpr.stdout.readlines()
    lines_stderr = subpr.stderr.readlines()
    subpr.stdout.close()
    subpr.stderr.close()
    subpr.wait()

    if rundir:
        os.chdir(cwd)

    text_lines_stdout = [l.decode() for l in lines_stdout]
    text_lines_stderr = [l.decode() for l in lines_stderr]
    return (text_lines_stdout, text_lines_stderr)
    #  #]

def prune_stderr_line(line):
    #  #[ remove paths from stderr
    '''
    in case of an error the stderr lines will contain full paths
    to the problematic python files, and these may differ from
    installation to installation, so cut them away.
    '''
    search_str1 = 'File "'
    search_str2 = '", line '
    if (search_str1 in line) and (search_str2 in line):
        start_index = line.index(search_str1) + len(search_str1)
        end_index   = line.index(search_str2)
        problematic_file = line[start_index:end_index]
        # print('DEBUG: problematic_file = [{0}]'.format(problematic_file))
        # print('DEBUG: start_index = ', start_index)
        # print('DEBUG: end_index   = ', end_index)
        # print('DEBUG: line = [{0}]'.format(line))
        # print('DEBUG: line[:start_index] = [{0}]'.format(line[:start_index]))
        # print('DEBUG: line[end_index:] ) = [{0}]'.format(line[end_index:]  ))
        pruned_line = ( line[:start_index] +
                        os.path.split(problematic_file)[1] +
                        line[end_index:] )
        # print('DEBUG: pruned_line = [{0}]'.format(pruned_line))
        return pruned_line
    else:
        return line
    #  #]

#def call_cmd_and_verify_output(cmd, rundir='', verbose=False):
def call_cmd_and_verify_output(cmd, rundir='', verbose=True,
                               template_values={}):
    #  #[ call a test script and verify its output
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
    # pylint: disable=R0914

    # assume at first that all will work as planned
    success = True

    # force verbose output (usefull to see what happens if
    # travis fails for a python version I dont have locally)
    #verbose = True

    #  #[ some old notes
    #print("__name__ = ", __name__)
    #print("__file__ = ", __file__)
    #print("self.__class__.__name__ = ", self.__class__.__name__)
    #print("func_filename = ", sys._getframe().f_code.co_filename)
    #print("func_name = ", sys._getframe().f_code.co_name)
    #print("dir(frame) = ", dir(sys._getframe()))
    #print("dir(f_code) = ", dir(sys._getframe().f_code))
    #print("0:callers name = ", sys._getframe(0).f_code.co_name)
    #
    #print("2:callers name = ", sys._getframe(2).f_code.co_name)
    #sys.exit(1)
    # see: http://code.activestate.com/recipes/66062/
    # for more examples on using sys._getframe()
    #  #]

    # determine the full path of the current python interpreter
    # python_interpreter = sys.executable

    # disable the pylint warning:
    # "Access to a protected member _getframe of a client class"
    # pylint: disable=W0212

    # determine the name of the calling function
    name_of_calling_function = sys._getframe(1).f_code.co_name

    # determine the name of the class that defines the calling function
    classname_of_calling_function = \
                 sys._getframe(1).f_locals['self'].__class__.__name__

    # pylint: enable=W0212

    # construct filenames for the actual and expected outputs
    basename_exp = os.path.join(EXP_OUTP_DIR,
                                classname_of_calling_function+"."+\
                                name_of_calling_function)
    basename_act = os.path.join(ACT_OUTP_DIR,
                                classname_of_calling_function+"."+\
                                name_of_calling_function)
    actual_stdout = basename_act+".actual_stdout"
    actual_stderr = basename_act+".actual_stderr"
    expected_stdout = basename_exp+".expected_stdout"
    expected_stderr = basename_exp+".expected_stderr"

    tmp_cmd = 'python3 '+cmd
    # execute the test and catch all output
    (lines_stdout, lines_stderr) = call_cmd(tmp_cmd, rundir)

    # write the actual outputs to file
    file_descr = open(actual_stdout, 'w')
    file_descr.writelines(lines_stdout)
    file_descr.close()

    file_descr = open(actual_stderr, 'w')
    file_descr.writelines(lines_stderr)
    file_descr.close()

    # try to read the expected outputs
    try:
        fd_stdout = open(expected_stdout, 'r')
        fd_stderr = open(expected_stderr, 'r')
        expected_lines_stdout = fd_stdout.readlines()
        expected_lines_stderr = fd_stderr.readlines()
        fd_stdout.close()
        fd_stderr.close()

    except IOError:
        print("ERROR: expected output not found; probably because")
        print("you just defined a new unittest case.")
        print("Missing filenames:")
        if not os.path.exists(expected_stdout):
            print("expected_stdout: ", expected_stdout)
            print("(actual output available in: ", actual_stdout, ")")
        if not os.path.exists(expected_stderr):
            print("expected_stderr: ", expected_stderr)
            print("(actual output available in: ", actual_stderr, ")")
        success = False
        return success

    for i, line in enumerate(lines_stderr):
        lines_stderr[i] = prune_stderr_line(line)
    for i, line in enumerate(expected_lines_stderr):
        expected_lines_stderr[i] = prune_stderr_line(line)
            
    if template_values:
        for key in template_values:
            value = template_values[key]

            for i, line in enumerate(expected_lines_stdout):
                if '#'+key+'#' in line:
                    modified_line = line.replace('#'+key+'#', value)
                    expected_lines_stdout[i] = modified_line

            for i, line in enumerate(expected_lines_stderr):
                if '#'+key+'#' in line:
                    modified_line = line.replace('#'+key+'#', value)
                    expected_lines_stderr[i] = modified_line

    # since the python3 version changes much printing properties,
    # make life easier by ignoring whitespace
    lines_stdout = [l.strip() for l in lines_stdout]
    lines_stderr = [l.strip() for l in lines_stderr]
    expected_lines_stdout = [l.strip() for l in expected_lines_stdout]
    expected_lines_stderr = [l.strip() for l in expected_lines_stderr]

    # compare the actual and expected outputs
    if lines_stdout != expected_lines_stdout:
        print("stdout differs from what was expected!!!")
        print("to find out what happended execute this diff command:")
        print("xdiff "+actual_stdout+' '+expected_stdout)
        if verbose:
            nlines = max(len(lines_stdout),
                         len(expected_lines_stdout))
            for iline in range(nlines):
                try:
                    line_stdout = lines_stdout[iline]
                except:
                    line_stdout = '[empty]'

                try:
                    exp_line_stdout = expected_lines_stdout[iline]
                except:
                    exp_line_stdout = '[empty]'

                if line_stdout != exp_line_stdout:
                    print('line {0} stdout output:      [{1}]'.
                          format(iline, line_stdout[:80]))
                    print('line {0} stdout exp. output: [{1}]'.
                          format(iline, exp_line_stdout[:80]))
        success = False

    if lines_stderr != expected_lines_stderr:
        print("stderr differs from what was expected!!!")
        print("to find out what happended execute this diff command:")
        print("xdiff "+actual_stderr+' '+expected_stderr)
        if verbose:
            nlines = max(len(lines_stderr),
                         len(expected_lines_stderr))
            for iline in range(nlines):
                try:
                    line_stderr = lines_stderr[iline]
                except IndexError:
                    line_stderr = '[empty]'

                try:
                    exp_line_stderr = expected_lines_stderr[iline]
                except IndexError:
                    exp_line_stderr = '[empty]'

                if line_stderr != exp_line_stderr:
                    print('line {0} stderr output:      [{1}]'.
                          format(iline, line_stderr[:80]))
                    print('line {0} stderr exp. output: [{1}]'.
                          format(iline, exp_line_stderr[:80]))
        success = False

    return success

    # enable the "Too many local variables" warning again
    # pylint: enable=R0914
    #  #]

print("Starting test program:")

use_eccodes = False # not yet default
if '--eccodes' in sys.argv:
    use_eccodes = True
    sys.argv.remove('--eccodes')
    print('using eccodes for unittest run')
else:
    print('using bufrdc for unittest run')


# test classes that work for both bufrdc and eccodes

# manual run:
'''
setenv PYTHONPATH `pwd`
setenv PYBUFR_ECMWF_USE_ECCODES True
./example_programs/example_for_using_bufr_message_iteration.py test/testdata/S-O3M_GOME_NOP_02_M02_20120911034158Z_20120911034458Z_N_O_20120911043724Z.bufr
'''

class CheckBUFRReader(unittest.TestCase):
    #  #[ 3 tests
    """
    a class to check the BUFRReader class
    """
    # common settings for the following tests
    testinputfileERS = os.path.join(
        TESTDATADIR, 'ISXH58EUSR199812162225')

    testinputfileGOME = os.path.join(
        TESTDATADIR,
        'S-O3M_GOME_NOP_02_M02_20120911034158Z_20120911034458Z_N_O_20120911043724Z.bufr')

    testinputfileGRAS = os.path.join(
        TESTDATADIR,
        'S-GRM_-GRAS_RO_L12_20120911032706_001_METOPA_2080463714_DMI.BUFR')

    # taken from development branch nl8_CY45R1_May23
    testinputfileAEOLUS = os.path.join(TESTDATADIR, "aeolus_l2b.bufr")
        

    def test_run_decoding_example_message_iter_ERS(self):
        #  #[
        """
        test the decoding example program
        """

        # run the provided example code and verify the output
        testprog = "example_for_using_bufr_message_iteration.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' ' + self.testinputfileERS

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]

    def test_run_decoding_example_message_iter_GOME(self):
        #  #[
        """
        test the decoding example program
        """

        # run the provided example code and verify the output
        testprog = "example_for_using_bufr_message_iteration.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' ' + self.testinputfileGOME

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]

    def test_run_decoding_example_message_iter_GRAS(self):
        #  #[
        """
        test the decoding example program
        """

        # run the provided example code and verify the output
        testprog = "example_for_using_bufr_message_iteration.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' ' + self.testinputfileGRAS

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]

    def test_run_decoding_example_message_iter_AEOLUS(self):
        #  #[
        """
        test the decoding example program
        """

        # run the provided example code and verify the output
        testprog = "example_for_using_bufr_message_iteration.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' ' + self.testinputfileAEOLUS

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]

    #  #]

# test classes that only work for bufrdc

if not use_eccodes:
  class CheckRawECMWFBUFR(unittest.TestCase):
    #  #[ 4 tests
    """
    a class to check the ecmwf_bufr_lib interface
    """
    # common settings for the following tests
    testinputfile = os.path.join(TESTDATADIR, 'Testfile.BUFR')
    corruptedtestinputfile = os.path.join(TESTDATADIR,
                                          'Testfile3CorruptedMsgs.BUFR')
    testoutputfile2u = os.path.join(TESTDATADIR, 'Testoutputfile2u.BUFR')

    def test_run_decoding_example(self):
        #  #[
        """
        run the decoding example program
        """
        # run the provided example code and verify the output
        testprog = "example_for_using_ecmwfbufr_for_decoding.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
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
        #    expected_lines_stdout = open(expected_stdout, 'r').readlines()
        #    lines_stdout = open(actual_stdout, 'r').readlines()
        #
        #    # compare the actual and expected outputs
        #    if not (lines_stdout == expected_lines_stdout):
        #        print("stdout differs from what was expected!!!")
        #        print("to find out what happended execute this diff command:")
        #        cmd = "xdiff "+actual_stdout+' '+expected_stdout
        #        print(cmd)
        #        # os.system(cmd)
        #        success = False
        #
        #except IOError:
        #    print("ERROR: expected output not found; probably because")
        #    print("you just defined a new unittest case.")
        #    print("Missing filename:")
        #    if not os.path.exists(expected_stdout):
        #        print("expected_stdout: ", expected_stdout)
        #        print("(actual output available in: ", actual_stdout, ")")
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
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
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
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' ' + self.testinputfile
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_pb_routines_example2(self):
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
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' ' + self.corruptedtestinputfile
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    #  #]

  class CheckBUFRInterfaceECMWF(unittest.TestCase):
    #  #[ 5 tests
    """
    a class to check the bufr_interface_ecmwf class
    """
    # common settings for the following tests
    testinputfile = os.path.join(TESTDATADIR, 'Testfile.BUFR')
    testoutputfile1u = os.path.join(TESTDATADIR, 'Testoutputfile1u.BUFR')

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
                          BUFRInterfaceECMWF, dummy=42)

        # todo: implement this (if this turns out to be important)
        # the module does no typechecking (yet) on its
        # inputs, so this one is not yet functional
        # self.assertRaises(TypeError,
        #                  BUFRInterfaceECMWF, verbose=42)

        #  #]
    def test_get_exp_bufr_table_names(self):
        #  #[
        """
        test the get_expected_ecmwf_bufr_table_names method
        """

        center = 210 # = ksec1( 3)
        subcenter = 0 # = ksec1(16)
        local_version = 1 # = ksec1( 8)
        master_table_version = 0 # = ksec1(15)
        edition_number = 3 # =  ksec0( 3)
        master_table_number = 0 # = ksec1(14)
        bufrobj = BUFRInterfaceECMWF()

        # inspect the location of the ecmwfbufr*.so file, and derive
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
        bufrobj.ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)

        (btable, ctable, dtable) = \
                 bufrobj.get_expected_ecmwf_bufr_table_names(\
                             center,
                             subcenter,
                             local_version,
                             master_table_version,
                             edition_number,
                             master_table_number)

        # print("tabel name B: ", btable)
        # print("tabel name D: ", dtable)
        self.assertEqual(btable, 'B0000000000210000001.TXT')
        self.assertEqual(ctable, 'C0000000000210000001.TXT')
        self.assertEqual(dtable, 'D0000000000210000001.TXT')
        #  #]
    def test_run_decoding_example(self):
        #  #[
        """
        test the decoding example program
        """

        # run the provided example code and verify the output
        testprog = "example_for_using_bufrinterface_ecmwf_for_decoding.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
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
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
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
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' ' + self.testinputfile

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]

    #  #]

  class CheckBUFRSorter(unittest.TestCase):
    #  #[ 1 test
    """
    a class to check the sort_bufr_msgs tool
    """
    # common settings for the following tests
    testinputfile = os.path.join(
        TESTDATADIR, 'synop2.bin')

    def test_run_sort_bufr_msgs(self):
        #  #[
        """
        test the sort_bufr_msgs tool
        """

        # run the provided example code and verify the output
        testprog = "sort_bufr_msgs.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' ' + self.testinputfile

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def tearDown(self):
        # cleanup after running the tests from this class
        # print('tearDown running')
        os.system('\\rm -f 3070*')
        os.system('\\rm -f 001101_001102*')
    #  #]

  class CheckBUFRWriter(unittest.TestCase):
    #  #[ 1 test
    def test_run_test_simple_wmo_template(self):
        #  #[
        """
        test a simple writer without delayed replication
        """

        # run the provided example code and verify the output
        testprog = "test_simple_wmo_template.py"
        cmd = os.path.join(TEST_DIR, testprog)

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_test_simple_ccittia5_template(self):
        #  #[
        """
        test a simple writer with ascii text entries
        """

        # run the provided example code and verify the output
        testprog = "test_simple_ccittia5_template.py"
        cmd = os.path.join(TEST_DIR, testprog)

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_unknown_descriptor_case(self):
        #  #[
        """
        test composing a BUFR message with an unknown descriptor
        """

        # run the provided script and verify the output
        testprog = "test_unknown_descriptor_in_template.py"
        cmd = os.path.join(TEST_DIR, testprog)

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def tearDown(self):
        # cleanup after running the tests from this class
        # print('tearDown running')
        os.system('\\rm -f dummy_bufr_file*')
    #  #]

  class CheckBUFRMessage_W(unittest.TestCase):
    #  #[ test filling BUFRMessage_W instances
    # for the default WMO definitions see:
    # pybufr_ecmwf/ecmwf_bufrtables/B0000000000000026000.TXT
    # pybufr_ecmwf/ecmwf_bufrtables/D0000000000000026000.TXT
    #
    def setUp(self):
        #  #[ setup BUFRWriter and BUFRMessage_W instances
        #print('doing setup')
        from pybufr_ecmwf.bufr import BUFRWriter

        self.bwr = BUFRWriter()
        #self.bwr.open(output_bufr_file)
        self.msg = self.bwr.add_new_msg(num_subsets=3)
        #  #]
    def test_single_descriptor(self):
        #  #[ properties of a single descriptor for pressure
        self.msg.set_template('010004')
        names = self.msg.get_field_names()
        self.assertEqual(names, ['PRESSURE',])
        props = self.msg.field_properties[10004]
        self.assertEqual(props['min_allowed_value'], 0.0)
        self.assertEqual(props['max_allowed_value'], 163830.0)
        self.assertEqual(props['step'], 10.0)
        #  #]
    def test_str_assign_single_descriptor(self):
        #  #[ assign to a single descriptor for pressure using str. descr.
        self.msg.set_template('010004')
        self.msg['PRESS'] = -10.0
        def assign(msg, value):
            msg['PRESS'] = value
            return True

        self.assertRaises(IncorrectUsageError, assign, self.msg, [])
        self.assertRaises(IncorrectUsageError, assign, self.msg, [10., 20.])
        self.assertEqual(assign(self.msg, 123.), True)
        self.assertEqual(assign(self.msg, [10., 20., 30.]), True)        
        #  #]
    def test_numstr_assign_single_descriptor(self):
        #  #[ assign to a single descr. for pressure using numstr. descr.
        self.msg.set_template('010004')
        def assign1(msg, value):
            msg['010004'] = value
            return True

        self.assertEqual(assign1(self.msg, 123.), True)
        self.assertEqual(assign1(self.msg, [10., 20., 30.]), True)        
        #  #]
    def test_num_assign_single_descriptor(self):
        #  #[ assign to a single descr. for pressure using num. descr.
        self.msg.set_template('010004')
        def assign2(msg, value):
            msg[0] = value
            return True
        
        self.assertEqual(assign2(self.msg, 123.), True)
        self.assertEqual(assign2(self.msg, [10., 20., 30.]), True)        
        #  #]
    def test_range_single_descriptor(self):
        #  #[ range check for a single descriptor for pressure
        self.msg.set_template('010004')
        self.msg['PRESS'] = -10.0
        def assign(msg, value):
            msg['PRESS'] = value
            return True

        self.msg.do_range_check = False # default
        self.assertEqual(assign(self.msg, -120.), True)
        self.msg.do_range_check = True
        self.assertRaises(ValueError, assign, self.msg, -120.)
        #  #]
    def test_simple_sequence(self):
        #  #[ properties for a shore sequence
        self.msg.set_template('301033')
        names = self.msg.get_field_names()
        self.assertEqual(names, 
                         ['BUOY/PLATFORM IDENTIFIER',
                          'TYPE OF STATION',
                          'YEAR',
                          'MONTH',
                          'DAY',
                          'HOUR',
                          'MINUTE',
                          'LATITUDE (HIGH ACCURACY)',
                          'LONGITUDE (HIGH ACCURACY)'])
        #  #]
    def test_assign_simple_sequence(self):
        #  #[ assign to an element of a short sequence
        self.msg.set_template('301033')
        def assign(msg, value):
            msg['LATITUDE'] = value
            return True
        self.assertEqual(assign(self.msg, 1.), True)
        self.assertEqual(assign(self.msg, [1., 2., 3.]), True)
        self.assertRaises(IncorrectUsageError, assign, self.msg, [])
        self.assertRaises(IncorrectUsageError, assign, self.msg,
                          [1., 2., 3., 4., 5., 6.])
        #  #]
    def test_invalid_assign_simple_sequence(self):
        #  #[ invalid assignments for a short sequence
        self.msg.set_template('301033')
        def assign(msg, value):
            msg['WRONGTITUDE'] = value
            return True
        self.assertRaises(IncorrectUsageError, assign, self.msg, 1.0)
        #  #]
    def test_double_assign_simple_sequence(self):
        #  #[ double assignments for a short sequence
        self.msg.set_template('301033')
        def assign(msg, value):
            msg['ITUDE'] = value
            return True
        #assign(self.msg, 1.0)
        self.assertRaises(IncorrectUsageError, assign, self.msg, 1.0)
        #  #]
    def test_assign_longer_sequence(self):
        #  #[ assign to an element of a longer sequence
        self.msg.set_template('312021') # ERS scatterometer template
        names = self.msg.get_field_names()
        #self.assertEqual('names', names)

        def assign(msg, value):
            msg['BACKSCATTER[1]'] = value
            return True
        self.assertEqual(assign(self.msg, 1.), True)
        #self.assertEqual(assign(self.msg, [1., 2., 3.]), True)
        #self.assertRaises(IncorrectUsageError, assign, self.msg, [])
        #self.assertRaises(IncorrectUsageError, assign, self.msg,
        #                  [1., 2., 3., 4., 5., 6.])
        #  #]
    def test_num_assign_longer_sequence(self):
        #  #[ assign to an element of a longer sequence
        self.msg.set_template('312021') # ERS scatterometer template
        names = self.msg.get_field_names()
        #self.assertEqual('names', list(enumerate(names)))

        def assign(msg, value):
            # element with index 28 is first occurrence of BACKSCATTER
            # in this template
            msg[28] = value
            return True
        self.assertEqual(assign(self.msg, 1.), True)
        self.assertEqual(assign(self.msg, [1., 2., 3.]), True)
        #  #]
    def test_invalid_assign_longer_sequence(self):
        #  #[ assign to an element of a longer sequence
        self.msg.set_template('312021') # ERS scatterometer template
        names = self.msg.get_field_names()
        def assign(msg, value):
            msg['BACKSCATTER'] = value
            return True

        self.assertRaises(IncorrectUsageError, assign, self.msg, 1.)
        #  #]
    def test_invalid_num_assign_longer_sequence(self):
        #  #[ assign to an element of a longer sequence
        self.msg.set_template('312021') # ERS scatterometer template
        names = self.msg.get_field_names()
        #self.assertEqual('names', list(enumerate(names)))

        def assign(msg, value):
            # this template has only 44 elements, index 0 upto 43,
            # so 44 should be out of range
            msg[44] = value
            return True

        self.assertRaises(IndexError, assign, self.msg, 1.)
        #  #]
    def test_assign_2d_array(self):
        #  #[ fill a bufr msg using a 2d array
        self.msg.set_template('301033')

        def assign(msg, values):
            msg.fill(values)
            return True
        test_values = [3*[1,],
                       3*[2,],
                       3*[2016,],
                       3*[12,],
                       3*[31,],
                       3*[23,],
                       [57,59,59],
                       [53.,54.,55.],
                       [5.,6.,7.], ]

        self.assertEqual(assign(self.msg, test_values), True)

        import numpy
        np_test_values = numpy.array(test_values)
        self.assertEqual(assign(self.msg, test_values), True)

        self.assertEqual(numpy.all(np_test_values.T.flatten() ==
                                    self.msg.values), True)

        self.assertRaises(IncorrectUsageError, assign,
                          self.msg, np_test_values[:5,:])
        self.assertRaises(IncorrectUsageError, assign,
                          self.msg, np_test_values[:,:2])
        #  #]
    def test_assign_subset(self):
        #  #[ fill a given subset of a bufr msg
        self.msg.set_template('301033')

        def assign(msg, isubset, values):
            msg.fill_subset(isubset, values)
            return True
        test_values = [1, 2, 2016, 12, 31, 23, 59, 55., 7.]

        self.assertEqual(assign(self.msg, 0, test_values), True)

        import numpy
        np_test_values = numpy.array(test_values)
        self.assertEqual(assign(self.msg, 0, test_values), True)

        self.assertEqual(numpy.all(np_test_values ==
                                    self.msg.values[:9]), True)

        self.assertRaises(IncorrectUsageError, assign,
                          self.msg, 3, np_test_values[:5])
        self.assertRaises(IncorrectUsageError, assign,
                          self.msg, 0, np_test_values[:5])
        #  #]
    def test_assign_del_repl(self):
        #  #[ assign templ. that uses del. repl.
        max_nr_of_replications = [1, ]
        self.msg.set_template('301028', max_repl = max_nr_of_replications)

        names = self.msg.get_field_names()
        #self.assertEqual('names', names)

        def assign(msg, value):
            msg['EFFECTIVE RADIUS OF FEATURE'] = value
            return True

        self.assertEqual(assign(self.msg, 1.), True)
        #  #]
    def test_invalid_assign_del_repl(self):
        #  #[ assign templ. that uses del. repl.

        # triggers an error because no max_repl parameter
        # is provided in the set_template call
        def set_templ(msg, templ):
            msg.set_template(templ)

        self.assertRaises(IncorrectUsageError, set_templ, self.msg, '301028')
        #  #]
    # ascii/ccittia5 tests
    def test_single_ascii_descriptor(self):
        #  #[ properties of a single ascii descriptor
        self.msg.set_template('000015') # units name
        names = self.msg.get_field_names()
        self.assertEqual(names, ['UNITS NAME',])
         # 000015 will be interpreted as octal, dont use that
        props = self.msg.field_properties[15]
        self.assertEqual(props['min_allowed_num_chars'], 0)
        self.assertEqual(props['max_allowed_num_chars'], 24)
        #  #]
    def test_single_too_long_ascii_descriptor(self):
        #  #[ test truncation
        self.msg.set_template('000015') # units name
        names = self.msg.get_field_names()
        #self.assertEqual(names, ['UNITS NAME',])
        # 000015 will be interpreted as octal, dont use that
        stored_sys_stderr = sys.stderr
        from io import StringIO
        sys.stderr = StringIO()
        self.msg[0] = '0123456789'*3
        expected_result = "WARNING: string is too long and will be truncated"
        current_stderr_output = sys.stderr.getvalue()
        sys.stderr = stored_sys_stderr

        self.assertEqual( (expected_result in current_stderr_output),
                          True)
        #  #]
    def test_str_assign_single_ascii_descriptor(self):
        #  #[ assign to a single ascii descriptor using str. descr.
        self.msg.set_template('000015')
        #self.msg['UNITS NAME'] = "a dummy unit"
        def assign(msg, value):
            msg['UNITS NAME'] = value
            return True

        #self.assertRaises(IncorrectUsageError, assign, self.msg, [])
        #self.assertRaises(IncorrectUsageError, assign, self.msg, [10., 20.])
        self.assertEqual(assign(self.msg, "M/S"), True)

        # a bit of cheeting: need to reset internal variable
        # cvals_index to allow multiple assignment tests in this function
        self.msg.cvals_index = 0
        self.assertEqual(assign(self.msg, "MM/SS"), True)

        self.msg.cvals_index = 0
        self.assertEqual(assign(self.msg, ["A", "B", "C"]), True)        
        #  #]
    def test_str_double_assign_single_ascii_descriptor(self):
        #  #[ double assignment test
        self.msg.set_template('000015')

        def assign(msg, value):
            msg['UNITS NAME'] = value
            return True

        self.assertEqual(assign(self.msg, "M/S"), True)
        # a second call triggers an error, since we have only
        # one string per subset in this template!
        self.assertRaises(IndexError, assign, self.msg, "M/S")
        #  #]

    def tearDown(self):
        #print('doing teardown')
        pass
    #  #]

  class CheckRawBUFRFile(unittest.TestCase):
    #  #[ 5 tests
    """
    a class to check the raw_bufr_file class
    """
    # common settings for the following tests
    testinputfile = os.path.join(TESTDATADIR, 'Testfile.BUFR')
    corruptedtestinputfile = os.path.join(TESTDATADIR,
                                          'Testfile3CorruptedMsgs.BUFR')
    testoutputfile3u = os.path.join(TESTDATADIR, 'Testoutputfile3u.BUFR')

    def test_init(self):
        #  #[
        """
        test instantiating the class
        """
        bufrfile1 = RawBUFRFile(verbose=True)
        self.assertEqual(bufrfile1.bufr_fd, None)
        self.assertEqual(bufrfile1.filename, None)
        self.assertEqual(bufrfile1.filemode, None)
        self.assertEqual(bufrfile1.filesize, None)
        self.assertEqual(bufrfile1.data, None)
        self.assertEqual(bufrfile1.list_of_bufr_pointers, [])
        self.assertEqual(bufrfile1.nr_of_bufr_messages, 0)
        self.assertEqual(bufrfile1.last_used_msg, 0)
        self.assertEqual(bufrfile1.verbose, True)
        bufrfile2 = RawBUFRFile(verbose=False)
        self.assertEqual(bufrfile2.verbose, False)
        #  #]
    def test_open(self):
        #  #[
        """
        test opening a BUFR file
        """
        bufrfile = RawBUFRFile(verbose=False)

        # check behaviour when mode is missing
        self.assertRaises(TypeError,
                          bufrfile.open, self.corruptedtestinputfile)

        # check behaviour when mode is invalid
        self.assertRaises(AssertionError,
                          bufrfile.open, self.corruptedtestinputfile, 'q')

        # check behaviour when filename is not a string
        expected_exception = OSError
        # Note: the python3 case for this assert prints some info
        # to stdout in case the test succeeds, which doesn't give the
        # nice dotted lines when running unit tests that all pass...
        # Therefore suppress stdout for this line.
        devnull = open(os.devnull, 'w')
        stdout_saved = sys.stdout
        sys.stdout = devnull
        self.assertRaises(expected_exception, bufrfile.open, 123, 'rb')
        sys.stdout = stdout_saved
        devnull.close()

        # check behaviour when file does not exist
        self.assertRaises(IOError, bufrfile.open, 'dummy', 'rb',
                          silent=True)

        # check the name of the user
        user = os.getenv("USER")
        if user != 'root':
            # note, this following permission test fails when running the
            # test suite as root, so skip it if that is the case

            # check behaviour when reading a file without proper permission
            testfile = "tmp_testfile.read.BUFR"
            if os.path.exists(testfile):
                # force the file to be readwrite
                os.chmod(testfile, 0o666)
                os.remove(testfile)

            # create a small dummy file
            fdescr = open(testfile, 'w')
            fdescr.write('dummy data')
            fdescr.close()
            # force the file to be unaccessible
            os.chmod(testfile, 0000)
            # do the test
            self.assertRaises(IOError, bufrfile.open, testfile, 'rb',
                              silent=True)

            # cleanup
            if os.path.exists(testfile):
                # force the file to be readwrite
                os.chmod(testfile, 0o666)
                os.remove(testfile)

            # check behaviour when writing to file without proper permission
            testfile = "tmp_testfile.write.BUFR"
            if os.path.exists(testfile):
                # force the file to be readwrite
                os.chmod(testfile, 0o666)
                os.remove(testfile)

            # create a small dummy fle
            fdescr = open(testfile, 'w')
            fdescr.write('dummy data')
            fdescr.close()
            # force the file to be readonly
            os.chmod(testfile, 0o444)
            # do the test
            self.assertRaises(IOError, bufrfile.open, testfile, 'wb',
                              silent=True)

            # cleanup
            if os.path.exists(testfile):
                # force the file to be readwrite
                os.chmod(testfile, 0o666)
                os.remove(testfile)
        #  #]
    def test_close(self):
        #  #[
        """
        test opening and closing a BUFR file
        """
        bufrfile = RawBUFRFile(verbose=False)
        bufrfile.open(self.corruptedtestinputfile, 'rb')
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
    #  #[ 4 tests
    """
    a class to check the bufr_table.py file
    """
    def test_get_name(self):
        #  #[ test convert_code_to_descriptor_name.py
        '''
        run the provided example code and verify the output
        '''
        testprog = 'convert_code_to_descriptor_name.py'
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_get_descriptor(self):
        #  #[ test find_descriptor_code.py
        '''
        run the provided example code and verify the output
        '''
        testprog = 'find_descriptor_code.py'
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_single_table(self):
         #  #[
        """
        test consistency of one set of bufr table files
        """
        # run the provided example code and verify the output
        cmd = "bufr_table.py simpletest"
        success = call_cmd_and_verify_output(cmd, rundir='pybufr_ecmwf')
        self.assertEqual(success, True)
        #  #]
    def test_reloading_a_different_table(self):
         #  #[
        """
        test ability to load several different sets of tables
        from a single script, by decoding several bufr files that
        require different templates and different tables.
        """
        # run the provided example code and verify the output
        testfile1 = 'test/testdata/S-O3M_GOME_NOP_02_M02_20120911'+\
                    '034158Z_20120911034458Z_N_O_20120911043724Z.bufr'
        testfile2 = 'test/testdata/Testfile.BUFR'

        # example_programs/
        testprog = "test_read_multiple_bufr_files.py"

        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        # this is not python2.6 compatible
        #cmd += " {} {} {} {}".format(testfile1, testfile1,
        #                             testfile2, testfile2)
        # so use this in stead:
        for fn in (testfile1, testfile1, testfile2, testfile2):
            cmd += ' '+fn

        success = call_cmd_and_verify_output(cmd)#, rundir='pybufr_ecmwf')
        self.assertEqual(success, True)
        #  #]
    #  #]

  class CheckCustomTables(unittest.TestCase):
    #  #[ 2 tests
    """
    a class to check the creation and use of custom BUFR table files
    """
    def test_create_custom_bufr_tables(self):
        #  #[
        """
        test the creation of custom BUFR table files
        """
        b_table_file = 'B_my_test_BUFR_table.txt'
        c_table_file = 'C_my_test_BUFR_table.txt'
        d_table_file = 'D_my_test_BUFR_table.txt'

        # run the provided example code and verify the output
        testprog = "create_bufr_tables.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)

        # verify the content of the created table files
        expected_b_table_file = os.path.join('test',
                                             'expected_test_outputs',
                                             b_table_file+'.expected')
        expected_c_table_file = os.path.join('test',
                                             'expected_test_outputs',
                                             c_table_file+'.expected')
        expected_d_table_file = os.path.join('test',
                                             'expected_test_outputs',
                                             d_table_file+'.expected')

        fdb = open(b_table_file)
        fdc = open(c_table_file)
        fdd = open(d_table_file)
        b_table_txt = fdb.readlines()
        c_table_txt = fdc.readlines()
        d_table_txt = fdd.readlines()
        fdb.close()
        fdc.close()
        fdd.close()

        fdb = open(expected_b_table_file)
        fdc = open(expected_c_table_file)
        fdd = open(expected_d_table_file)
        expected_b_table_txt = fdb.readlines()
        expected_c_table_txt = fdc.readlines()
        expected_d_table_txt = fdd.readlines()
        fdb.close()
        fdc.close()
        fdd.close()

        # allows larger chuncks during comparisons by assertEqual
        self.maxDiff = None

        self.assertEqual(b_table_txt, expected_b_table_txt)
        self.assertEqual(c_table_txt, expected_c_table_txt)
        self.assertEqual(d_table_txt, expected_d_table_txt)

#        os.remove(b_table_file)
#        os.remove(c_table_file)
#        os.remove(d_table_file)
        #  #]
    def test_use_custom_bufr_tables(self):
        #  #[
        """
        test the use of the custom BUFR table files
        """
        test_bufr_file = 'TESTCUSTOM.BUFR'
        b_table_file = 'B_my_test_BUFR_table.txt'
        c_table_file = 'C_my_test_BUFR_table.txt'
        d_table_file = 'D_my_test_BUFR_table.txt'

        # create the custom BUFR tables
        testprog = "create_bufr_tables.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        call_cmd(cmd)
        # don't check this call, this has been checked above already

        # run the provided example code and verify the output
        testprog = "use_custom_tables_for_encoding.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' ' + test_bufr_file
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)

        # clean up
        os.remove(b_table_file)
        os.remove(c_table_file)
        os.remove(d_table_file)
        os.remove(test_bufr_file)
        #  #]
    #pylint: disable=C0103
    def tearDown(self):
        # cleanup after running the tests from this class
        # print('tearDown running')
        os.system('\\rm -rf tmp_BUFR_TABLES')
        os.system('\\rm -rf /tmp/pybufr_ecmwf_temporary_files_*/'+\
                  'tmp_BUFR_TABLES')
    #pylint: enable=C0103
    #  #]

  class CheckBufr(unittest.TestCase):
    #  #[ 11 tests
    """
    a class to check the bufr.py file
    """
    # common settings for the following tests
    testinputfile = os.path.join(TESTDATADIR, 'Testfile.BUFR')
    testinputfile_unpadded = os.path.join(TESTDATADIR,
                                          'ISXH58EUSR199812162225')
    fname = 'S-GRM_-GRAS_RO_L12_20120911032706_001_METOPA_2080463714_DMI.BUFR'
    testinputfile_gras = os.path.join(TESTDATADIR, fname)

    fname = ('S-O3M_GOME_NOP_02_M02_20120911034158Z_20120911034458Z_'+
             'N_O_20120911043724Z.bufr')
    testinputfile_o3m = os.path.join(TESTDATADIR, fname)

    def test_run_decode_example1_ascii(self):
        #  #[
        """
        test the decoding example program and produce ascii output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -1 -a -i ' + self.testinputfile

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_example1_csv(self):
        #  #[
        """
        test the decoding example program, and produce csv output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -1 -c -i ' + self.testinputfile

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_example2_ascii(self):
        #  #[
        """
        test the decoding example program and produce ascii output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -2 -a -f -i ' + self.testinputfile

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_example2_csv(self):
        #  #[
        """
        test the decoding example program and produce csv output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -2 -c -i ' + self.testinputfile

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_example2_csv_expflags(self):
        #  #[
        """
        test the decoding example program and produce csv output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -2 -c -f -i ' + self.testinputfile

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_example3_ascii(self):
        #  #[
        """
        test the decoding example program and produce ascii output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -3 -a -i ' + self.testinputfile

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_example3_csv(self):
        #  #[
        """
        test the decoding example program and produce csv output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -3 -c -i ' + self.testinputfile

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_unpadded_testfile_csv(self):
        #  #[
        """
        test the decoding example program and produce csv output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -1 -c -i ' + self.testinputfile_unpadded

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_gras_testfile_csv(self):
        #  #[
        """
        test the decoding example program and produce csv output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -4 -c -i ' + self.testinputfile_gras

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_gras_testfile_csv_expflags(self):
        #  #[
        """
        test the decoding example program and produce csv output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -4 -c -f -i ' + self.testinputfile_gras

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    def test_run_decode_o3m_testfile_csv(self):
        #  #[
        """
        test the decoding example program and produce csv output
        """

        # run the provided example code and verify the output
        testprog = "bufr_to_ascii.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        cmd = cmd + ' -4 -c -i ' + self.testinputfile_o3m

        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)
        #  #]
    #  #]

  class CheckVersionInfo(unittest.TestCase):
    #  #[ 1 test
    '''
    a class to test the retrieval of version info works correct
    '''
    def test_version_info(self):
        '''
        print some version info variables to ensure they are filled
        '''
        # get install date by looking at the modification date
        # of the generated pybufr_ecmwf/version.py file
        file_to_test = 'pybufr_ecmwf/version.py'
        stats = os.stat(file_to_test)
        mtime = time.localtime(stats.st_mtime)
        myformat = '%Y'
        mtime_txt = time.strftime(myformat, mtime)
        template_values = {'YEAR':mtime_txt}

        testprog = "print_version_info.py"
        cmd = os.path.join(TEST_DIR, testprog)
        success = call_cmd_and_verify_output(cmd,
                                             template_values=template_values)
        self.assertEqual(success, True)
    #  #]

  class CheckDelayedReplication(unittest.TestCase):
    #  #[ 4 tests
    '''
    a class to test the encoding and decoding of BUFR files
    using delayed replication with different replication
    factors for subsequent subsets in the same message

    The tests in this class follow the following sequence:
        * composes custom BUFR tables
        * then encodes a test BUFR message
        * then decodes the same message again
    '''
    def test_delayed_replication_in_example_dir(self):
        '''run the example program'''
        testprog = "delayed_replication_example.py"
        cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)

    def test_delayed_replication(self):
        '''run the special test in the test folder'''
        testprog = "test_delayed_replication.py"
        cmd = os.path.join(TEST_DIR, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)

    def test_delayed_replication_nested(self):
        '''run the special test in the test folder'''
        testprog = "test_delayed_replication_nested.py"
        cmd = os.path.join(TEST_DIR, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)

    def test_delayed_repetition(self):
        '''run the special test in the test folder'''
        testprog = "test_delayed_repetition.py"
        cmd = os.path.join(TEST_DIR, testprog)
        success = call_cmd_and_verify_output(cmd)
        self.assertEqual(success, True)

    def tearDown(self):
        # clean up
        test_bufr_file = 'dummy_bufr_file.bfr'
        b_table_file = 'B_test_table.txt'
        c_table_file = 'C_test_table.txt'
        d_table_file = 'D_test_table.txt'

        os.remove(b_table_file)
        os.remove(c_table_file)
        os.remove(d_table_file)
        os.remove(test_bufr_file)
    #  #]

if not use_eccodes:
    # specific tests on bufrdc internals that cannot be ported to eccodes
    class CheckAddedFortranCode(unittest.TestCase):
        #  #[ 1 test
        '''
        a class to test some fortran code added to the BUFR library
        '''
        def test_retrieve_settings(self):
            '''
            test a little script to retrieve fortran settings
            in the BUFR library
            '''
            testprog = "test_retrieve_settings.py"
            cmd = os.path.join(TEST_DIR, testprog)
            success = call_cmd_and_verify_output(cmd)
            self.assertEqual(success, True)
        #  #]

    

# cleanup old tmp_BUFR_TABLES dir that may have been created by a previous run
os.system('\\rm -rf tmp_BUFR_TABLES')
os.system('\\rm -rf /tmp/pybufr_ecmwf_temporary_files_*/tmp_BUFR_TABLES')

# this just runs all tests
print("Running unit tests:")
test_result = unittest.main(exit=False)
test_success = test_result.result.wasSuccessful()

# this will exit and not run any code following the next line!
# unittest.main()
# so we canot rely on the removal of the symlink below.

# unittest.main(verbosity=2)

# Problem: unittest.main() seems to call sys.exit()
# and does not return (even in case of no errors!)
# The exit=False switch ensures the module rename gets restored again.

# restore the original directory structure when all testing is done
if PYBUFR_ECMWF_MODULE_WAS_RENAMED:
    # safety check
    if os.path.islink('pybufr_ecmwf'):
        print('removing symlink pybufr_ecmwf')
        os.remove('pybufr_ecmwf')
        print('renaming pybufr_ecmwf.renamed to pybufr_ecmwf')
        shutil.move('pybufr_ecmwf.renamed', 'pybufr_ecmwf')

# print('done with unit testing')
# print('python_major_minor: ', python_major_minor)

print('just before exit: success = ', test_success)
sys.exit(not test_success)

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
# print(bf.get_num_bufr_msgs())
# ==> 3
# print(len(bf))
# ==> 3
#
# for msg in bf:
#    print(msg)
#    ==> BUFR msg holding 361 subsets of 44 descriptors
#    print(len(msg))
#    ==>361
#    for subset in msg:
#      print(subset)
#      ==>BUFR MSG SUBSET holding 44 descriptors
#      print(len(subset))
#      ==>44
#      for item in subset:
#         if item['name'] == 'LATITUDE (COARSE ACCURACY)':
#            print(item.value)
#            ==>-2.91
#
#    x = msg.get_values('LATITUDE (COARSE ACCURACY)')
#    print(x)
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
