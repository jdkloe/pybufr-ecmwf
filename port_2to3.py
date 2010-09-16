#!/usr/bin/env python

"""
a little script to use the 2to3 conversion tool on this
source code, to allow easier porting to python3
"""

import os, sys
from pybufr_ecmwf import helpers

def port_2to3():
    #  #[
    '''
    a routine try to automatically convert the whole source code
    of this module to python3 
    '''
    # first see if python3 and the 2to3 tool are available
    tools_to_check = ['2to3', 'python3', 'hg']
    for tool_to_check in tools_to_check:
        cmd = 'which '+tool_to_check
        (lines_stdout, lines_stderr) = helpers.run_shell_command(cmd,
                                                                 verbose=False)

        if len(lines_stderr)>0:
            print 'sorry, the '+tool_to_check+' tool seems not installed'
            print 'num lines stderr/stdout = ', \
                  len(lines_stderr), len(lines_stdout)
            sys.exit(1)
        else:
            print 'tool found: ', tool_to_check
            
    # create the testdir
    testdir = 'tmp_2to3_converted_sources'
    if os.path.exists(testdir):
        print 'ERROR: testdir: ', testdir, ' already exists'
        print 'please first run the clean.py tool before trying to run'
        print 'this conversion script'
        sys.exit(1)
    os.mkdir(testdir)
    
    # clone the repository to the testdir
    print 'cloning the repository'
    cmd = 'hg clone . '+testdir
    (lines_stdout, lines_stderr) = helpers.run_shell_command(cmd,
                                                             verbose=False)
    if len(lines_stderr)>0:
        print 'sorry, failed command: ', cmd
        for line in lines_stderr:
            print line,
        sys.exit(1)

    # do the actual conversion
    print 'converting sources to python3'
    cmd = '2to3 -w tmp_2to3_converted_sources'
    (lines_stdout, lines_stderr) = helpers.run_shell_command(cmd,
                                                             verbose=False)
    # this next check is not usefull, since the 2to3 tool issues
    # several messages to stderr even if all runs well
    # if len(lines_stderr)>0:
    #    print 'sorry, failed command: ', cmd
    #    for line in lines_stderr:
    #        print line,
    #    sys.exit(1)
    
    print 'conversion done'
    #  #]

# run the conversion tool
port_2to3()

# todo: try to run the build and test stages
