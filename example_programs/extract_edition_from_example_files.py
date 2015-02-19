#!/usr/bin/env python

'''
a simple script to loop over bufr files as provided in the ecmwf bufr library
and show the bufr edition numbers for them.
'''
# ensure the pybufr-ecmwf module can be found, for exmple by setting
# from the build directory (in case you did a manual build):
#
# setenv PYTHONPATH `pwd`

# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

import os, glob
for f in glob.glob('pybufr_ecmwf/ecmwf_bufr_lib/000401/data/*.bufr'):
    cmd = 'example_programs/bufr_extract_edition.py '+f
    print f
    os.system(cmd)

