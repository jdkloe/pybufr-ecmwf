#!/usr/bin/env python

""" a small script to make it easier for me to run pylint
on the python code in the pybufr_ecmwf module.
It is intended to be run in the software root of this project,
so in the same directory as the one that holds the setup.py script.
Launch the script like this:
      ./pylint/run_pylint.py
or like this:
      ./pylint/run_pylint.py <file1> <file2>
"""

# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

import sys, os, glob

try:
    from pylint import lint
except ImportError:
    print "Sorry, importing the pylint module failed"
    print "probably you don't have pylint installed or your python"
    print "module path needs to be set properly"
    sys.exit(1)

# this commandline option:
#        '--init-hook=\'import sys;sys.path.append(\"pybufr_ecmwf\")\'',
# is equivalent to:
#sys.path.append("./")

# see: the Run class in:
# /usr/lib/python2.6/site-packages/pylint/lint.py
# for examples on how to run the checkers manually

if len(sys.argv) > 1:
    SCRIPTS_TO_CHECK = []
    for filetocheck in sys.argv[1:]:
        if os.path.exists(filetocheck):
            SCRIPTS_TO_CHECK.append(filetocheck)
    MODULES_TO_CHECK = []
else:
    EX_PROGR_PATH = 'example_programs'
    EX_FILES = glob.glob(os.path.join(EX_PROGR_PATH, '*.py'))
    SCRIPTS_TO_CHECK = glob.glob('*.py')
    SCRIPTS_TO_CHECK.append('pylint/run_pylint.py')
    # note: pylint/pylint_numpy_test.py is omitted here on purpose.
    # it is used inside check_pylint_numpy_handling() defined above.
    # look into that routine for more details.
    SCRIPTS_TO_CHECK.extend(EX_FILES)

    # my current pylint version crashes with a runtime error when I
    # try to check this module, so its disabled for now
    MODULES_TO_CHECK = []
    #MODULES_TO_CHECK = ['pybufr_ecmwf', ]

def check(msg, pycode, additional_args):
    #  #[
    """ a little helper function to run pylint on a python
    script or module directory """
    print msg+pycode
    args = []
    args.extend(additional_args)
    args.extend(['--rcfile', 'pylint/pylintrc', pycode])
    #args.extend(['--files-output=yes', '--rcfile', 'pylint/pylintrc', pycode])
    try:
        # note: the Run method always ends with a sys.exit() call
        # so the except clause seems always to be called when
        # the checking is done

        # debug print
        # print 'launching: lint.Run('+str(args)+')'
        lint.Run(args)

        # this point is never reached ...
        print 'this point should not be used'
        return (-1, pycode)
    except SystemExit as sysexit:
        if sysexit.args[0] == 0:
            print 'all seems fine'
            return (0, pycode)
        else:
            print "exception occurred; exit status: ", sysexit.args[0]
            return (1, pycode)

    #  #]

def check_pylint_numpy_handling():
    #  #[
    """
    a dedicated (hopefully temporary) routine to try running pylint
    on a small piece of example python code using numpy.
    This is needed to allow a workaround, because at the moment (sept-2010)
    pylint seems not able to handle the way the functions, classes and types
    are defined in the numpy module (probably because some of its class
    attributes are dynamically set?)
    """

    (success, pycode) = check('checking script: ',
                              'pylint/pylint_numpy_test.py',
                              additional_args=[])
    if success == 0:
        use_numpy_checks = True
        return use_numpy_checks

    (success, pycode) = check('checking script: ',
                              'pylint/pylint_numpy_test.py',
                              additional_args=['--ignored-classes=numpy'])
    if success == 0:
        use_numpy_checks = False
        return use_numpy_checks

    # the code should not reach this point
    print "Programming problem in check_pylint_numpy_handling:"
    print "success = ", success
    print "pycode = ", pycode
    sys.exit(1)
    #  #]

def check_all_py_files():
    #  #[
    """
    a function to find all python code in this project, and run
    the pylint checker on it.
    """

    # check for problems when importing numpy
    # (since some older pylint versions cannot properly handlethis dependency)
    use_numpy_checks = check_pylint_numpy_handling()
    if use_numpy_checks:
        print '==>numpy imports can safely be checked by pylint'
        additional_args = []
    else:
        print '==>pylint does not handle numpy imports correctly'
        print '==>ignoring this module from pylint checking'
        additional_args = ['--ignored-classes=numpy']

    # check for presence of compiled ecmwfbufr.so shared object file
    # which is only present after manually building the software
    # and disable the import during the pylint checking if it is missing
    if not os.path.exists(os.path.join('pybufr_ecmwf', 'ecmwfbufr.so')):
        #additional_args.append('--ignored-classes=ecmwfbufr')
        # note: this seems not to help at the moment ...
        # workaround: do the manual build first before running pylint
        print 'Sorry, you need to manually build the ecmwfbufr.so file first'
        print 'to allow correct running of the pylint checker, using this'
        print 'command: ./build_interface.py'
        sys.exit(1)

    result = []

    for mod_to_check in MODULES_TO_CHECK:
        result.append(check('checking module: ',
                            mod_to_check, additional_args))

    for script in SCRIPTS_TO_CHECK:
        result.append(check('checking script: ',
                            script, additional_args))

    num_not_ok = sum([r[0] for r in result])
    num_ok = len(result) - num_not_ok

    print "done; nr of modules/scripts checked: ", len(result)
    print "number of well validated modules/scripts: ", num_ok
    print "number of problematic    modules/scripts: ", num_not_ok

    print '\n'.join('status: %2i file %s' % (i, f) for (i, f) in result)

    if num_not_ok > 0:
        # warning: dont use the word pylint followed by a colon ':'
        # in text strings, since pylint will interpret this as a
        # command and starts issuing warnings...
        # For this reason a space has been inserted below.
        print '\nfor more details on the detected errors and warnings, '
        print 'you can inspect the output files that have been generated'
        print 'by pylint :'
        filelist = glob.glob('pylint_*.txt')
        print '\n'.join(file for file in filelist)
    #  #]

check_all_py_files()
