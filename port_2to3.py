#!/usr/bin/env python

"""
a little script to use the 2to3 conversion tool on this
source code, to allow easier porting to python3
"""

import os, sys
import subprocess  # support running additional executables

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
        print "Executing command: ", cmd
        
    if (catch_output):
        # print 'env[PYTHONPATH] = ',env['PYTHONPATH']
        subpr = subprocess.Popen(cmd,
                                 shell  = True,
                                 env    = env,
                                 stdout = subprocess.PIPE,
                                 stderr = subprocess.PIPE)
        
        # wait until the child process is done
        # subpr.wait() # seems not necessary when catching stdout and stderr
            
        lines_stdout = subpr.stdout.readlines()
        lines_stderr = subpr.stderr.readlines()
        
        #print "lines_stdout: ", lines_stdout
        #print "lines_stderr: ", lines_stderr
        
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
    for tool_to_check in tools_to_check:
        cmd = 'which '+tool_to_check
        (lines_stdout, lines_stderr) = run_shell_command(cmd, verbose=False)

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
    (lines_stdout, lines_stderr) = run_shell_command(cmd, verbose=False)
    if len(lines_stderr)>0:
        print 'sorry, failed command: ', cmd
        for line in lines_stderr:
            print line,
        sys.exit(1)

    # do the actual conversion
    print 'converting sources to python3'
    cmd = '2to3 -w tmp_2to3_converted_sources'
    (lines_stdout, lines_stderr) = run_shell_command(cmd, verbose=False)
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
