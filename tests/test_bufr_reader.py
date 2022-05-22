#!/usr/bin/env python

import os         # operating system functions
import sys        # operating system functions
import unittest   # import the unittest functionality
from shared_setup import (call_cmd_and_verify_output,
                          TESTDATADIR, EXAMPLE_PROGRAMS_DIR)

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
