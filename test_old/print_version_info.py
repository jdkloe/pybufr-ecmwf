#!/usr/bin/env python

'''
print some version details.
'''

# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html
from __future__ import print_function
import pybufr_ecmwf.version

print('-'*10)
print('pybufr_ecmwf.version.software_version = ',
      pybufr_ecmwf.version.software_version)
print('pybufr_ecmwf.version.install_date [year only] = ',
      pybufr_ecmwf.version.install_date.split('-')[-1])
print('-'*10)

# don't print these next items by default.
# They vary at each call and make it impossible
# to use this script as unit test case.
# Enable manually if you wish to test this functionality

# print('pybufr_ecmwf.version.hg_version = ', pybufr_ecmwf.version.hg_version)
# print('pybufr_ecmwf.version.install_date = ', pybufr_ecmwf.version.install_date)
