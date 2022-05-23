#!/usr/bin/env python

import os         # operating system functions
import sys        # operating system functions
import unittest   # import the unittest functionality
from .shared_setup import (call_cmd_and_verify_output,
                           TESTDATADIR, EXAMPLE_PROGRAMS_DIR)

"""
tests to check the BUFRReader class
"""
# common settings for the following tests
testinputfileERS = os.path.join(
    TESTDATADIR, 'ISXH58EUSR199812162225')

testinputfileGOME = os.path.join(TESTDATADIR,
    'S-O3M_GOME_NOP_02_M02_20120911034158Z_20120911034458Z_' +
                                 'N_O_20120911043724Z.bufr')

testinputfileGRAS = os.path.join(TESTDATADIR,
    'S-GRM_-GRAS_RO_L12_20120911032706_001_METOPA_2080463714_DMI.BUFR')

# taken from development branch nl8_CY45R1_May23
testinputfileAEOLUS = os.path.join(TESTDATADIR, "aeolus_l2b.bufr")

def test_run_decoding_example_message_iter_ERS(setup):
    #  #[
    """
    test the decoding example program
    """

    # run the provided example code and verify the output
    testprog = "example_for_using_bufr_message_iteration.py"
    cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
    cmd = cmd + ' ' + testinputfileERS

    testname = 'CheckBUFRReader.test_run_decoding_example_message_iter_ERS'
    success = call_cmd_and_verify_output(cmd, testname)
    assert success
    #  #]

def test_run_decoding_example_message_iter_GOME(setup):
    #  #[
    """
    test the decoding example program
    """

    # run the provided example code and verify the output
    testprog = "example_for_using_bufr_message_iteration.py"
    cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
    cmd = cmd + ' ' + testinputfileGOME

    testname = 'CheckBUFRReader.test_run_decoding_example_message_iter_GOME'
    success = call_cmd_and_verify_output(cmd, testname)
    assert success
    #  #]

def test_run_decoding_example_message_iter_GRAS(setup):
    #  #[
    """
    test the decoding example program
    """

    # run the provided example code and verify the output
    testprog = "example_for_using_bufr_message_iteration.py"
    cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
    cmd = cmd + ' ' + testinputfileGRAS

    testname = 'CheckBUFRReader.test_run_decoding_example_message_iter_GRAS'
    success = call_cmd_and_verify_output(cmd, testname)
    assert success
    #  #]

def test_run_decoding_example_message_iter_AEOLUS(setup):
    #  #[
    """
    test the decoding example program
    """

    # run the provided example code and verify the output
    testprog = "example_for_using_bufr_message_iteration.py"
    cmd = os.path.join(EXAMPLE_PROGRAMS_DIR, testprog)
    cmd = cmd + ' ' + testinputfileAEOLUS

    testname = 'CheckBUFRReader.test_run_decoding_example_message_iter_AEOLUS'
    success = call_cmd_and_verify_output(cmd, testname)
    assert success
    #  #]
