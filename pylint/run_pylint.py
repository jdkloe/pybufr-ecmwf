#!/usr/bin/env python

""" a small script to make it easier for me to run pylint
on the python code in the pybufr_ecmwf module"""

import sys
from pylint import lint

# this commandline option:
#        '--init-hook=\'import sys;sys.path.append(\"pybufr_ecmwf\")\'',
# is equivalent to:
sys.path.append("pybufr_ecmwf")

# see: the Run class in:
# /usr/lib/python2.6/site-packages/pylint/lint.py
# for examples on how to run the checkers manually

def check(msg, pycode):
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
        else:
            print "exception occurred; exit status: ", sysexit.args[0]
            
check('checking module: ','pybufr_ecmwf')
check('checking script: ','clean.py')
check('checking script: ','setup.py')
check('checking script: ','pylint/run_pylint.py')

print "done"
