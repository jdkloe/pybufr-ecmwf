#!/usr/bin/env python

"""
a small script to clean the source code from everything that can be
generated during building and testing.
(mostly usefull for re-testing over and over again during development)
"""

from __future__ import print_function
import os, glob #, sys

# delete these dirs
DIRS_GLOB_PATTERNS = ['pybufr_ecmwf/ecmwf_bufr_lib/bufr_000*',
                      'pybufr_ecmwf/ecmwf_bufr_lib/bufrdc_000*',
                      'pybufr_ecmwf/ecmwf_bufr_lib/000*',
                      'ecmwf_bufr_lib/bufr_000*',
                      'ecmwf_bufr_lib/bufrdc_000*',
                      'ecmwf_bufr_lib/000*']
DIRS_TO_DELETE = ['pybufr_ecmwf/example_programs/tmp_BUFR_TABLES',
                  'pybufr_ecmwf/tmp_BUFR_TABLES', 'tmp_BUFR_TABLES',
                  'ecmwf_bufrtables', 'pybufr_ecmwf/ecmwf_bufrtables',
                  'pybufr_ecmwf/f2py_build', 'build', 'dist',
                  'pybufr_ecmwf/__pycache__', '__pycache__',
                  'tmp_2to3_converted_sources',
                  'example_programs/tmp_BUFR_TABLES',
                  'test/actual_test_outputs']

# delete these files
FILE_GLOB_PATTERNS = ['*~', '*/*~', '*/*/*~', '*.pyc', '*/*.pyc',
                      '*/Testfile3Msgs.BUFR', '*/*/Testfile3Msgs.BUFR',
                      'pybufr_ecmwf/expected_test_outputs/*.actual_std*',
                      'pybufr_ecmwf/GetByteSize*',
                      'pylint_*.txt']
FILES_TO_DELETE = ['pybufr_ecmwf/libbufr.a', 'libbufr.a', 'MANIFEST',
                   'pybufr_ecmwf/ecmwfbufr.so', 'ecmwfbufr.so',
                   'ecmwfbufr.so', 'pybufr_ecmwf/ecmwf_bufr_lib/config_file',
                   'ecmwf_bufr_lib/config_file', 'pybufr_ecmwf/ecmwfbufr.so',
                   'pybufr_ecmwf/ecmwfbufr_parameters.py',
                   'pybufr_ecmwf/version.py',
                   'test/testdata/Testoutputfile1u.BUFR',
                   'test/testdata/Testoutputfile2u.BUFR',
                   'test/testdata/Testoutputfile3u.BUFR']

#pylint: disable=C0103
dirs_to_delete = []
#pylint: enable=C0103
dirs_to_delete.extend(DIRS_TO_DELETE)
for pattern in DIRS_GLOB_PATTERNS:
    dirs_to_delete.extend(glob.glob(pattern))

#pylint: disable=C0103
files_to_delete = []
#pylint: enable=C0103
files_to_delete.extend(FILES_TO_DELETE)
for pattern in FILE_GLOB_PATTERNS:
    files_to_delete.extend(glob.glob(pattern))

for d in dirs_to_delete:
    if os.path.exists(d):
        if os.path.isdir(d):
            print('deleting dir: ', d)
            os.system(r'\rm -rf '+d)
    # this only works if the dirs are empty!
    #os.removedirs(d)

for f in files_to_delete:
    if os.path.exists(f):
        print('deleting file: ', f)
        os.remove(f)
    if os.path.islink(f):
        print('deleting symlink: ', f)
        os.remove(f)

print('done')
