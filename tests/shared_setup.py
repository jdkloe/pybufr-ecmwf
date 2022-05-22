#!/usr/bin/env python

#  #[ imported modules
import os         # operating system functions
import sys        # operating system functions
import shutil     # operating system functions
import subprocess # support running additional executables

from pybufr_ecmwf.helpers import get_and_set_the_module_path

#  #]
#  #[ path handling
DUMMY_SYS_PATH = sys.path[:] # provide a copy
(DUMMY_SYS_PATH, MY_MODULE_PATH) = get_and_set_the_module_path(DUMMY_SYS_PATH)
# print '(sys.path, MY_MODULE_PATH) = ',(sys.path, MY_MODULE_PATH)

# in case the build is done by setup.py, the created ecmwfbufr.so module will
# be in a path like SWROOT/build/lib.linux-x86_64-2.7/pybufr_ecmwf/
# To ensure the unittests find it, temporarily rename SWROOT/pybufr_ecmwf/
# and create a symlink to SWROOT/build/lib.linux-x86_64-2.7/pybufr_ecmwf/
PYBUFR_ECMWF_MODULE_WAS_RENAMED = False
if 'build/lib' in MY_MODULE_PATH:
    print('renaming pybufr_ecmwf to pybufr_ecmwf.renamed')
    shutil.move('pybufr_ecmwf', 'pybufr_ecmwf.renamed')
    print('creating symlink pybufr_ecmwf')
    os.symlink(os.path.join(MY_MODULE_PATH, 'pybufr_ecmwf'), # source
               'pybufr_ecmwf') # destination
    PYBUFR_ECMWF_MODULE_WAS_RENAMED = True
#else:
#    print('MY_MODULE_PATH = ', MY_MODULE_PATH)

#  #]
#  #[ some constants
EXAMPLE_PROGRAMS_DIR = 'example_programs'
TEST_DIR = 'test_old'
TESTDATADIR = os.path.join(TEST_DIR, 'testdata')
EXP_OUTP_DIR = os.path.join(TEST_DIR, 'expected_test_outputs')
ACT_OUTP_DIR = os.path.join(TEST_DIR, 'actual_test_outputs')

if not os.path.exists(ACT_OUTP_DIR):
    os.mkdir(ACT_OUTP_DIR)

use_eccodes = False # not yet default
if '--eccodes' in sys.argv:
    use_eccodes = True
    sys.argv.remove('--eccodes')
    print('using eccodes for unittest run')
else:
    print('using bufrdc for unittest run')
#  #]


def call_cmd(cmd, rundir=''):
    #  #[ do the actual call to an external test script
    """ a wrapper around run_shell_command for easier testing.
    It sets the environment setting PYTHONPATH to allow the
    code to find the current pybufr-ecmwf library"""

    # get the list of already defined env settings
    env = os.environ
    if 'PYTHONPATH' in env:
        settings = env['PYTHONPATH'].split(':')
        if not MY_MODULE_PATH in settings:
            env['PYTHONPATH'] = MY_MODULE_PATH+':'+env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = MY_MODULE_PATH

    if use_eccodes:
        env['PYBUFR_ECMWF_USE_ECCODES'] = 'True'
    else:
        env['PYBUFR_ECMWF_USE_ECCODES'] = 'False'
        

    # print('DEBUG: env[PYTHONPATH] = ',env['PYTHONPATH'])
    # print('DEBUG: env[BUFR_TABLES] = ',env.get('BUFR_TABLES','undefined'))
    # print('DEBUG: cmd = ',cmd)

    # remove the env setting to
    # /tmp/pybufr_ecmwf_temporary_files_*/tmp_BUFR_TABLES/
    # that may have been left by a previous test
    if 'BUFR_TABLES' in env:
        del env['BUFR_TABLES']

    # change dir if needed
    if rundir:
        cwd = os.getcwd()
        os.chdir(rundir)

    # execute the test and catch all output
    subpr = subprocess.Popen(cmd, shell=True, env=env,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    lines_stdout = subpr.stdout.readlines()
    lines_stderr = subpr.stderr.readlines()
    subpr.stdout.close()
    subpr.stderr.close()
    subpr.wait()

    if rundir:
        os.chdir(cwd)

    text_lines_stdout = [l.decode() for l in lines_stdout]
    text_lines_stderr = [l.decode() for l in lines_stderr]
    return (text_lines_stdout, text_lines_stderr)
    #  #]

def prune_stderr_line(line):
    #  #[ remove paths from stderr
    '''
    in case of an error the stderr lines will contain full paths
    to the problematic python files, and these may differ from
    installation to installation, so cut them away.
    '''
    search_str1 = 'File "'
    search_str2 = '", line '
    if (search_str1 in line) and (search_str2 in line):
        start_index = line.index(search_str1) + len(search_str1)
        end_index   = line.index(search_str2)
        problematic_file = line[start_index:end_index]
        # print('DEBUG: problematic_file = [{0}]'.format(problematic_file))
        # print('DEBUG: start_index = ', start_index)
        # print('DEBUG: end_index   = ', end_index)
        # print('DEBUG: line = [{0}]'.format(line))
        # print('DEBUG: line[:start_index] = [{0}]'.format(line[:start_index]))
        # print('DEBUG: line[end_index:] ) = [{0}]'.format(line[end_index:]  ))
        pruned_line = ( line[:start_index] +
                        os.path.split(problematic_file)[1] +
                        line[end_index:] )
        # print('DEBUG: pruned_line = [{0}]'.format(pruned_line))
        return pruned_line
    else:
        return line
    #  #]

#def call_cmd_and_verify_output(cmd, rundir='', verbose=False):
def call_cmd_and_verify_output(cmd, rundir='', verbose=True,
                               template_values={}):
    #  #[ call a test script and verify its output
    """ a wrapper around run_shell_command for easier testing.
    It automatically constructs a name for the test output based
    on the class and function name from which it was called.
    Then it executes the test function and redirects the stdout and
    stderr outputs to files with the just constructed names.
    Finally it compares the actual test outputs with expected outputs
    that should be present in the current directory.
    If the outputs are as expected the function returns True,
    otherwise False."""

    # disable the "Too many local variables" pylint warning
    # since I feel this helper routine really could not be
    # rewritten using less local variables
    #
    # pylint: disable=R0914

    # assume at first that all will work as planned
    success = True

    # force verbose output (usefull to see what happens if
    # travis fails for a python version I dont have locally)
    #verbose = True

    #  #[ some old notes
    #print("__name__ = ", __name__)
    #print("__file__ = ", __file__)
    #print("self.__class__.__name__ = ", self.__class__.__name__)
    #print("func_filename = ", sys._getframe().f_code.co_filename)
    #print("func_name = ", sys._getframe().f_code.co_name)
    #print("dir(frame) = ", dir(sys._getframe()))
    #print("dir(f_code) = ", dir(sys._getframe().f_code))
    #print("0:callers name = ", sys._getframe(0).f_code.co_name)
    #
    #print("2:callers name = ", sys._getframe(2).f_code.co_name)
    #sys.exit(1)
    # see: http://code.activestate.com/recipes/66062/
    # for more examples on using sys._getframe()
    #  #]

    # determine the full path of the current python interpreter
    # python_interpreter = sys.executable

    # disable the pylint warning:
    # "Access to a protected member _getframe of a client class"
    # pylint: disable=W0212

    # determine the name of the calling function
    name_of_calling_function = sys._getframe(1).f_code.co_name

    # determine the name of the class that defines the calling function
    classname_of_calling_function = \
                 sys._getframe(1).f_locals['self'].__class__.__name__

    # pylint: enable=W0212

    # construct filenames for the actual and expected outputs
    basename_exp = os.path.join(EXP_OUTP_DIR,
                                classname_of_calling_function+"."+\
                                name_of_calling_function)
    basename_act = os.path.join(ACT_OUTP_DIR,
                                classname_of_calling_function+"."+\
                                name_of_calling_function)
    actual_stdout = basename_act+".actual_stdout"
    actual_stderr = basename_act+".actual_stderr"
    expected_stdout = basename_exp+".expected_stdout"
    expected_stderr = basename_exp+".expected_stderr"

    tmp_cmd = 'python3 '+cmd
    # execute the test and catch all output
    (lines_stdout, lines_stderr) = call_cmd(tmp_cmd, rundir)

    # write the actual outputs to file
    file_descr = open(actual_stdout, 'w')
    file_descr.writelines(lines_stdout)
    file_descr.close()

    file_descr = open(actual_stderr, 'w')
    file_descr.writelines(lines_stderr)
    file_descr.close()

    # try to read the expected outputs
    try:
        fd_stdout = open(expected_stdout, 'r')
        fd_stderr = open(expected_stderr, 'r')
        expected_lines_stdout = fd_stdout.readlines()
        expected_lines_stderr = fd_stderr.readlines()
        fd_stdout.close()
        fd_stderr.close()

    except IOError:
        print("ERROR: expected output not found; probably because")
        print("you just defined a new unittest case.")
        print("Missing filenames:")
        if not os.path.exists(expected_stdout):
            print("expected_stdout: ", expected_stdout)
            print("(actual output available in: ", actual_stdout, ")")
        if not os.path.exists(expected_stderr):
            print("expected_stderr: ", expected_stderr)
            print("(actual output available in: ", actual_stderr, ")")
        success = False
        return success

    for i, line in enumerate(lines_stderr):
        lines_stderr[i] = prune_stderr_line(line)
    for i, line in enumerate(expected_lines_stderr):
        expected_lines_stderr[i] = prune_stderr_line(line)
            
    if template_values:
        for key in template_values:
            value = template_values[key]

            for i, line in enumerate(expected_lines_stdout):
                if '#'+key+'#' in line:
                    modified_line = line.replace('#'+key+'#', value)
                    expected_lines_stdout[i] = modified_line

            for i, line in enumerate(expected_lines_stderr):
                if '#'+key+'#' in line:
                    modified_line = line.replace('#'+key+'#', value)
                    expected_lines_stderr[i] = modified_line

    # since the python3 version changes much printing properties,
    # make life easier by ignoring whitespace
    lines_stdout = [l.strip() for l in lines_stdout]
    lines_stderr = [l.strip() for l in lines_stderr]
    expected_lines_stdout = [l.strip() for l in expected_lines_stdout]
    expected_lines_stderr = [l.strip() for l in expected_lines_stderr]

    # compare the actual and expected outputs
    if lines_stdout != expected_lines_stdout:
        print("stdout differs from what was expected!!!")
        print("to find out what happended execute this diff command:")
        print("xdiff "+actual_stdout+' '+expected_stdout)
        if verbose:
            nlines = max(len(lines_stdout),
                         len(expected_lines_stdout))
            for iline in range(nlines):
                try:
                    line_stdout = lines_stdout[iline]
                except:
                    line_stdout = '[empty]'

                try:
                    exp_line_stdout = expected_lines_stdout[iline]
                except:
                    exp_line_stdout = '[empty]'

                if line_stdout != exp_line_stdout:
                    print('line {0} stdout output:      [{1}]'.
                          format(iline, line_stdout[:80]))
                    print('line {0} stdout exp. output: [{1}]'.
                          format(iline, exp_line_stdout[:80]))
        success = False

    if lines_stderr != expected_lines_stderr:
        print("stderr differs from what was expected!!!")
        print("to find out what happended execute this diff command:")
        print("xdiff "+actual_stderr+' '+expected_stderr)
        if verbose:
            nlines = max(len(lines_stderr),
                         len(expected_lines_stderr))
            for iline in range(nlines):
                try:
                    line_stderr = lines_stderr[iline]
                except IndexError:
                    line_stderr = '[empty]'

                try:
                    exp_line_stderr = expected_lines_stderr[iline]
                except IndexError:
                    exp_line_stderr = '[empty]'

                if line_stderr != exp_line_stderr:
                    print('line {0} stderr output:      [{1}]'.
                          format(iline, line_stderr[:80]))
                    print('line {0} stderr exp. output: [{1}]'.
                          format(iline, exp_line_stderr[:80]))
        success = False

    return success

    # enable the "Too many local variables" warning again
    # pylint: enable=R0914
    #  #]
