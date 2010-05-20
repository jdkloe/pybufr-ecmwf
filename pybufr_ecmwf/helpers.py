#!/usr/bin/env python

"""
this module collects a number of general helper routines
and classes used on several places in the code.
"""

#  #[ documentation:
#
# this file defines some helper subroutines used in several places
# and a collection of custom exceptions
#
#
# Written by: J. de Kloe, KNMI (www.knmi.nl), Initial version 19-Mar-2010
#
# License: GPL v2.
#
#  #]
#  #[ imported modules 
import os          # operating system functions
import sys         # system functions
import subprocess  # support running additional executables
import stat        # handling of file stat data
#  #]
#  #[ exception definitions
# see: http://docs.python.org/library/exceptions.html
# for a list of already available exceptions.
# are:     IOError, EOFError
class NotYetImplementedError(NotImplementedError):
    """ an exception to indicate that a feature is not yet implemented
    (but is planned to be implemented later, therefore it differs from
    the NotImplementedError exception)
    """
    pass
class ProgrammingError(Exception):
    """ an exception to indicate that a progromming error seems
    present in the code (this should be reported to the author) """
    pass
class NetworkError(Exception):
    """ an exception to indicate that a network problem occurred """
    pass
class LibraryBuildError(Exception):
    """ an exception to indicate that building the ECMWF BUFR
    library has failed """
    pass
class InterfaceBuildError(Exception): 
    """ an exception to indicate that building the fortran-to-python
    interface has failed """
    pass
class EcmwfBufrLibError(Exception):
    """ an exception to indicate that one of the subroutines or functions
    in the ECMWF bufr library returned with an error """
    pass
#  #]

def run_shell_command(cmd, libpath = None, catch_output = True,
                      verbose = True):
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
            env[envname] = env[envname] + ";" + libpath
        else:
            env[envname] = libpath
            
    if (verbose):
        print "Executing command: ", cmd
        
    if (catch_output):
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

def call_cmd_and_verify_output(cmd):
    #  #[
    """ a wrapper around run_shell_command for easier testing.
    It automatically constructs a name for the test output based
    on the class and function name from which it was called.
    Then it executes the test function and redirects the stdout and
    stderr outputs to files with the just constructed names.
    Finally it compares the actual test outputs with expected outputs
    that should be present in the current directory.
    If the outputs are as expected the function returns True,
    otherwise False."""

    # assume at first that all will work as planned
    success = True

    #  #[ some old notes
    #print "__name__ = ", __name__
    #print "__file__ = ", __file__
    #print "self.__class__.__name__ = ", self.__class__.__name__
    #print "func_filename = ", sys._getframe().f_code.co_filename
    #print "func_name = ", sys._getframe().f_code.co_name
    #print "dir(frame) = ", dir(sys._getframe())
    #print "dir(f_code) = ", dir(sys._getframe().f_code)
    #print "0:callers name = ", sys._getframe(0).f_code.co_name
    #
    #print "2:callers name = ", sys._getframe(2).f_code.co_name
    #sys.exit(1)
    # see: http://code.activestate.com/recipes/66062/
    # for more examples on using sys._getframe()
    #  #]
    
    # determine the full path of the current python interpreter
    python_interpreter = sys.executable

    # determine the name of the calling function
    name_of_calling_function = sys._getframe(1).f_code.co_name

    # determine the name of the class that defines the calling function
    classname_of_calling_function = \
                 sys._getframe(1).f_locals['self'].__class__.__name__

    # construct filenames for the actual and expected outputs
    exp_dir = "expected_test_outputs"
    basename = os.path.join(exp_dir,
                            classname_of_calling_function+"."+\
                            name_of_calling_function)
    actual_stdout   = basename+".actual_stdout"
    actual_stderr   = basename+".actual_stderr"
    expected_stdout = basename+".expected_stdout"
    expected_stderr = basename+".expected_stderr"

    # execute the test and catch all output
    (lines_stdout, lines_stderr) = run_shell_command(python_interpreter+' '+cmd,
                                                     catch_output = True,
                                                     verbose = False)

    # write the actual outputs to file
    file_descr = open(actual_stdout, 'wt')
    file_descr.writelines(lines_stdout)
    file_descr.close()

    file_descr = open(actual_stderr, 'wt')
    file_descr.writelines(lines_stderr)
    file_descr.close()
    
    # try to read the expected outputs
    try:
        expected_lines_stdout = open(expected_stdout, 'rt').readlines()
        expected_lines_stderr = open(expected_stderr, 'rt').readlines()
    
        # compare the actual and expected outputs
        if not (lines_stdout == expected_lines_stdout):
            print "stdout differs from what was expected!!!"
            print "look at the diff of files: ", expected_stdout
            print "and: ", actual_stdout
            print "to find out what happended ..."
            success = False
            
        if not (lines_stderr == expected_lines_stderr):
            print "stderr differs from what was expected!!!"
            print "look at the diff of files: ", expected_stderr
            print "and: ", actual_stderr
            print "to find out what happended ..."
            success = False
    except IOError:
        print "ERROR: expected output not found; probably because"
        print "you just defined a new unittest case."
        print "Missing filenames:"
        if not os.path.exists(expected_stdout):
            print "expected_stdout: ", expected_stdout
            print "(actual output available in: ", actual_stdout, ")"
        if not os.path.exists(expected_stderr):
            print "expected_stderr: ", expected_stderr
            print "(actual output available in: ", actual_stderr, ")"
        success = False
        
    return success
    #  #]

def rem_quotes(txt):
    #  #[
    """ a little helper function to remove quotes from a string."""
    if txt is None:
        return txt
    elif txt[0] == "'" and txt[-1] == "'":
        return txt[1:-1]
    elif txt[0] == '"' and txt[-1] == '"':
        return txt[1:-1]
    else:
        return txt
    #  #]

def ensure_permissions(filename, mode):
    #  #[ ensure permissions for "world"
    """ a little routine to ensure the permissions for the
        given file are as expected """
    file_stat = os.stat(filename)
    current_mode = stat.S_IMODE(file_stat.st_mode)
    if mode == 'r':
        new_mode = current_mode | int("444", 8)
    if mode == 'w':
        new_mode = current_mode | int("222", 8)
    if mode == 'x':
        new_mode = current_mode | int("111", 8)
    os.chmod(filename, new_mode)
    #  #]
