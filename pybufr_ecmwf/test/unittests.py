#!/usr/bin/env python

"""
the file contains a collection of unittests to verify the correct
implementation of the several pieces of code in this module.
"""

import unittest  # import the unittest functionality

# set the python path to find the (maybe not yet installed) module files
# (not needed if the module is installed in the default location)
import helpers
helpers.set_python_path()

import pybufr_ecmwf.bufr

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
