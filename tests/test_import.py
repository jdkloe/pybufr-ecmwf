#!/usr/bin/env python

import unittest   # import the unittest functionality

class CheckImport(unittest.TestCase):
    def test_importing_pybufr_ecmwf(self):
        from pybufr_ecmwf.custom_exceptions import EcmwfBufrTableError
        err = EcmwfBufrTableError()
        self.assertIsInstance(err, Exception)

