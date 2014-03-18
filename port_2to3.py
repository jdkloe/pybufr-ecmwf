#!/usr/bin/env python

"""
a little script to use the 2to3 conversion tool on this
source code, to allow easier porting to python3

WARNING:
numpy for python3 is still very new, so may not be available
as default package from your favourite linux distribution for some time.
Therefore you need to install a 3rd party numpy rpm/deb package or install
numpy from source first, before you can use the python3 version of this
pybufr_ecmwf module. JK, 22-Apr-2011.
"""
from __future__ import (absolute_import, division,
                        print_function) # , unicode_literals)
import os, sys
import subprocess  # support running additional executables

PY3_CONVERTED_PATH = 'tmp_2to3_converted_sources'

def run_shell_command(cmd, libpath = None, catch_output = True,
                      module_path = './', verbose = True):
    #  #[
    """ a wrapper routine around subprocess.Popen intended
    to make it a bit easier to call this functionality.
    Options:
    -libpath: add this path to the LD_LIBRARY_PATH environment variable
     before executing the subprocess
    -catch_output: if True, this function returns 2 lists of text lines
     containing the stdout and stderr of the executed subprocess
    -verbose: give some feedback to the user while executing the
     code (usefull for debugging)"""

    # get the list of already defined env settings
    env = os.environ
    if (libpath):
        # add the additional env setting
        envname = "LD_LIBRARY_PATH"
        if (env.has_key(envname)):
            env[envname] = env[envname] + ":" + libpath
        else:
            env[envname] = libpath

    if (env.has_key('PYTHONPATH')):
        env['PYTHONPATH'] = env['PYTHONPATH']+':'+module_path
    else:
        env['PYTHONPATH'] = module_path

    if (verbose):
        print("Executing command: ", cmd)

    if (catch_output):
        # print('env[PYTHONPATH] = ',env['PYTHONPATH'])
        subpr = subprocess.Popen(cmd,
                                 shell  = True,
                                 env    = env,
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE)

        # wait until the child process is done
        # subpr.wait() # seems not necessary when catching stdout and stderr

        lines_stdout = subpr.stdout.readlines()
        lines_stderr = subpr.stderr.readlines()

        #print("lines_stdout: ", lines_stdout)
        #print("lines_stderr: ", lines_stderr)

        return (lines_stdout, lines_stderr)

    else:
        subpr = subprocess.Popen(cmd, shell = True, env = env)

        # wait until the child process is done
        subpr.wait()
        return
    #  #]

def port_2to3():
    #  #[
    '''
    a routine try to automatically convert the whole source code
    of this module to python3
    '''
    # first see if python3 and the 2to3 tool are available
    tools_to_check = ['2to3', 'python3', 'hg']

    # note: normally, if you have a recent python2 installed
    # (and on some systems maybe the python-tools package as well)
    # the 2to3 tool will be available in: /usr/bin/2to3
    #
    # However, if you have only python3 installed then (on my fedora14
    # system) 2to3 is installed in: /usr/lib64/python3.1/Tools/scripts/2to3
    # In my case 2to3 is part of the python3-tools package.

    for tool_to_check in tools_to_check:
        cmd = 'which '+tool_to_check
        (lines_stdout, lines_stderr) = run_shell_command(cmd, verbose=False)

        if len(lines_stderr)>0:
            print('sorry, the '+tool_to_check+' tool seems not installed')
            print('num lines stderr/stdout = ', \
                  len(lines_stderr), len(lines_stdout))
            sys.exit(1)
        else:
            print('tool found: ', tool_to_check)

    # create the testdir
    if os.path.exists(PY3_CONVERTED_PATH):
        print('ERROR: testdir: ', PY3_CONVERTED_PATH, ' already exists')
        print('please first run the clean.py tool before trying to run')
        print('this conversion script')
        sys.exit(1)
    os.mkdir(PY3_CONVERTED_PATH)

    # clone the repository to the testdir
    print('cloning the repository')
    cmd = 'hg clone . '+PY3_CONVERTED_PATH
    (lines_stdout, lines_stderr) = run_shell_command(cmd, verbose=False)
    if len(lines_stderr)>0:
        print('sorry, failed command: ', cmd)
        for line in lines_stderr:
            print(line, end='')
        sys.exit(1)

    # do the actual conversion
    print('converting sources to python3')
    cmd = '2to3 -w '+PY3_CONVERTED_PATH
    (lines_stdout, lines_stderr) = run_shell_command(cmd, verbose=False)
    # this next check is not usefull, since the 2to3 tool issues
    # several messages to stderr even if all runs well
    # if len(lines_stderr)>0:
    #    print('sorry, failed command: ', cmd)
    #    for line in lines_stderr:
    #        print(line, end='')
    #    sys.exit(1)

    # walk along all python files and fix the shebang/hashbang line
    # since the 2to3 tool seems to not fix this one.
    for walk_result in os.walk(PY3_CONVERTED_PATH):
        dirpath   = walk_result[0]
        filenames = walk_result[2]
        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext == '.py':
                path_and_file = os.path.join(dirpath, filename)
                print('fixing: ', path_and_file)

                fdb = open(path_and_file) #, 'rt')
                lines = fdb.readlines()
                fdb.close()

                fda = open(path_and_file, 'w')
                for line in lines:
                    if '#!' in line:
                        print('shebang line found: ', line.replace('\n',''))
                        fda.write('#!/usr/bin/env python3\n')
                    else:
                        fda.write(line)
                fda.close()

    # commit the modified code to allow usage by my automatic test
    # system, which copies the module by taking a clone of the repository.
    cmd = 'cd '+PY3_CONVERTED_PATH+';'+\
          'hg commit -m "automatic commit by the port_2to3.py tool"'
    (lines_stdout, lines_stderr) = run_shell_command(cmd, verbose=False)

    print('conversion done')
    #  #]

# run the conversion tool
port_2to3()

# todo: try to run the build and test stages
