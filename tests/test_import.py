#!/usr/bin/env python

import unittest   # import the unittest functionality
import sys
import pytest

def test_importing_pybufr_ecmwf(setup):
    from pybufr_ecmwf.custom_exceptions import EcmwfBufrTableError
    from pybufr_ecmwf.ecmwfbufr import bufrex
    err = EcmwfBufrTableError()
    assert isinstance(err, Exception)
