#!/usr/bin/env python

""" a small script to make it easier for me to run pylint
on the python code in the pybufr_ecmwf module"""

import sys, os
from pylint import lint

# this commandline option:
#        '--init-hook=\'import sys;sys.path.append(\"pybufr_ecmwf\")\'',
# is equivalent to:
sys.path.append("pybufr_ecmwf")

# see: the Run class in:
# /usr/lib/python2.6/site-packages/pylint/lint.py
# for examples on how to run the checkers manually

def check(msg, pycode):
    #  #[
    """ a little helper function to run pylint on a python
    script or module directory """
    print msg+pycode
    args = ['--rcfile', 'pylint/pylintrc', pycode]
    try:
        # note: the Run method always ends with a sys.exit() call
        # so the except clause seems always to be called when
        # the checking is done
        lint.Run(args)
    except SystemExit as sysexit:
        if (sysexit.args[0] == 0):
            print 'all seems fine'
            return 0
        else:
            print "exception occurred; exit status: ", sysexit.args[0]
            return 1
    #  #]

EX_PROGR_PATH = 'pybufr_ecmwf/example_programs'
EX_FILES = ['example_for_using_bufrinterface_ecmwf_for_decoding.py',
            'example_for_using_bufrinterface_ecmwf_for_encoding.py',
            'example_for_using_ecmwfbufr_for_decoding.py',
            'example_for_using_ecmwfbufr_for_encoding.py',
            'example_for_using_pb_routines.py',
            'example_for_using_rawbufrfile.py',
            'verify_bufr_tables.py']

result = []
result.append(check('checking module: ', 'pybufr_ecmwf'))
result.append(check('checking script: ', 'clean.py'))
result.append(check('checking script: ', 'setup.py'))
result.append(check('checking script: ', 'pylint/run_pylint.py'))
for ex_file in EX_FILES:
    result.append(check('checking script: ',
                        os.path.join(EX_PROGR_PATH, ex_file)))

num_not_ok = sum(result)
num_ok     = len(result)-num_not_ok

print "done; nr of modules/scripts checked: ",len(result)
print "number of well validated modules/scripts: ",num_ok
print "number of problematic    modules/scripts: ",num_not_ok
