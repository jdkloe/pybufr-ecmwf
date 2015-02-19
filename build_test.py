#!/usr/bin/env python

""" a script to automatically try and verify the different
build options with the on the current system available
fortran compilers.
"""

# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

#  #[ plan:
# search for available fortran (and c?) compilers
#
# for each compiler
# -clone the repository
# -edit the setup.cfg file to choose the compiler
# -build the software
# -run the manual build step
# -run the unit tests
# -convert source code to python3
# -do the build test again
#
#  #]
#  #[ imported modules
from __future__ import (absolute_import, division,
                        print_function) # , unicode_literals)
import os, sys, glob
import subprocess  # support running additional executables
#  #]
#  #[ settings
REPODIR = '../pybufr-ecmwf'
TESTDIR = '../pybufr_ecmwf_test_builds'
DO_MANUAL_TESTS = True
DO_SETUP_BUILD_TESTS = True
DO_SETUP_SDIST_TESTS = True
DO_PIP_INSTALL_TESTS = True
DO_MANUAL_PY3_TESTS = False # True

#  #]
#  #[ helper functions
def run_shell_command(cmd_to_run, sp_env=None):
    #  #[
    """ a wrapper routine around subprocess.Popen intended
    to make it a bit easier to call this functionality.
    """
    #print("Executing command: ", cmd_to_run)
    this_env = sp_env
    if sp_env is None:
        this_env = os.environ
    subpr = subprocess.Popen(cmd_to_run, shell=True, env=this_env,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    ls_stdout = subpr.stdout.readlines()
    ls_stderr = subpr.stderr.readlines()
    return (ls_stdout, ls_stderr)
    #  #]
#  #]
#  #[ init
if not os.path.exists(REPODIR):
    print('ERROR: could not find REPODIR: '+REPODIR)
    sys.exit(1)

if not os.path.exists(TESTDIR):
    os.mkdir(TESTDIR)

# search for available fortran (and c?) compilers
POSSIBLE_FORTRAN_COMPILERS = ['g95', 'gfortran', 'ifort', 'pgf90', 'f90']
AVAILABLE_POSSIBLE_COMPILERS = []
for fc in POSSIBLE_FORTRAN_COMPILERS:
    cmd = 'which '+fc
    # print('running: ',cmd)
    (lines_stdout, lines_stderr) = run_shell_command(cmd)
    # print('(lines_stdout, lines_stderr) = ',(lines_stdout, lines_stderr))
    if len(lines_stderr) == 0:
        AVAILABLE_POSSIBLE_COMPILERS.append(fc)

print('available fortran compilers: ',
      ', '.join(fc for fc in AVAILABLE_POSSIBLE_COMPILERS))
#  #]
TESTRESULTS = []
for fc in AVAILABLE_POSSIBLE_COMPILERS:
    if DO_MANUAL_TESTS:
        #  #[ build using the manual build script and check the result
        # -create a temporary working dir for the build
        build_dir_name = 'manual_build_'+fc
        temp_build_dir = os.path.join(TESTDIR, build_dir_name)
        if os.path.exists(temp_build_dir):
            print('dir: ', temp_build_dir, ' exists; removing it first')
            cmd = '\\rm -rf '+temp_build_dir
            os.system(cmd)

        # not needed, the clone command creates the dir
        # print('creating dir: ', temp_build_dir)
        # os.mkdir(temp_build_dir)

        # -clone the repository
        cmd = 'cd '+TESTDIR+'; hg clone '+REPODIR+' '+build_dir_name
        print("Executing command: ", cmd)
        os.system(cmd)

        # step into the test dir
        saved_cwd = os.getcwd()
        os.chdir(temp_build_dir)

        print('saved_cwd   = ', saved_cwd)
        print('os.getcwd() = ', os.getcwd())

        # -build the software
        sys.path.append(os.getcwd())
        # print('sys.path = ', sys.path)

        from build_interface import InstallBUFRInterfaceECMWF, BuildException
        BI = InstallBUFRInterfaceECMWF(verbose=True,
                                       preferred_fortran_compiler=fc,
                                       download_library_sources=False)

        # make sure we are in the right directory
        BUILD_DIR = 'pybufr_ecmwf'
        os.chdir(BUILD_DIR)

        this_result = []
        build_succesfull = True
        try:
            BI.build()
        except BuildException:
            this_result.append('manual build failed for compiler: '+fc)
            build_succesfull = False

        del BI

        # restore the original directory
        os.chdir(saved_cwd)

        # -verify the presence of the generated ecmwfbufr.so file
        so_files = glob.glob(os.path.join(temp_build_dir, BUILD_DIR,
                                          'ecmwfbufr.so'))

        this_result.append('test results for manual build for: '+fc)
        if len(so_files) > 0:
            this_result.append('so file found: '+so_files[0])
        else:
            this_result.append('ERROR: so file NOT found!')

        if build_succesfull:
            # -run the unit tests
            cmd = 'cd '+temp_build_dir+';'+\
                  'python ./unittests.py'
            # os.system(cmd)
            (lines_stdout, lines_stderr) = run_shell_command(cmd)
            for l in lines_stdout:
                this_result.append('STDOUT: '+l.replace('\n', ''))
            for l in lines_stderr:
                this_result.append('STDERR: '+l.replace('\n', ''))
        else:
            this_result.append('unittests skipped')

        TESTRESULTS.append(this_result)

        #  #]
    if DO_SETUP_BUILD_TESTS:
        #  #[ build using the setup tool and check the result
        # -create a temporary working dir for the build
        build_dir_name = 'build_'+fc
        temp_build_dir = os.path.join(TESTDIR, build_dir_name)
        if os.path.exists(temp_build_dir):
            print('dir: ', temp_build_dir, ' exists; removing it first')
            cmd = '\\rm -rf '+temp_build_dir
            os.system(cmd)

        # -clone the repository
        cmd = 'cd '+TESTDIR+'; hg clone '+REPODIR+' '+build_dir_name
        print("Executing command: ", cmd)
        os.system(cmd)

        # -edit the setup.cfg file to choose the compiler
        #  and to prevent the library download
        cfg_file = os.path.join(temp_build_dir, 'setup.cfg')

        cfg_lines = open(cfg_file).readlines()

        # save a backup copy by moving the original
        # os.rename(cfg_file, cfg_file+'.orig')

        fd = open(cfg_file, 'w')
        for l in cfg_lines:
            if 'preferred_fortran_compiler' in l:
                fd.write('preferred_fortran_compiler='+fc+'\n')
            elif 'download_library_sources' in l:
                fd.write('download_library_sources = False\n')
            else:
                fd.write(l)
        fd.close()

        # commit the modified code, to track what happended incase
        # I would pull from this modified repository by mistake.
        cmd = 'cd '+temp_build_dir+';'+\
              'hg commit -m "automatic commit by the build_test tool"'
        (lines_stdout, lines_stderr) = run_shell_command(cmd)

        # -build the software
        cmd = 'cd '+temp_build_dir+';'+\
              'python ./setup.py build'
        os.system(cmd)

        # -verify the presence of the generated ecmwfbufr.so file
        so_files = glob.glob(os.path.join(temp_build_dir,
                                      'build/lib*/pybufr_ecmwf/ecmwfbufr.so'))

        this_result = []
        this_result.append('test results for build for: '+fc)
        if len(so_files) > 0:
            this_result.append('so file found: '+so_files[0])
        else:
            this_result.append('ERROR: so file NOT found!')

        # -run the unit tests
        try:
            env = os.environ
            env['PYTHONPATH'] = os.path.split(so_files[0])[0]

            cmd = 'cd '+temp_build_dir+';'+\
                  'python ./unittests.py'
            # os.system(cmd)
            (lines_stdout, lines_stderr) = run_shell_command(cmd, sp_env=env)
            for l in lines_stdout:
                this_result.append('STDOUT: '+l.replace('\n', ''))
            for l in lines_stderr:
                this_result.append('STDERR: '+l.replace('\n', ''))
        except IndexError:
            this_result.append('skipping unittests')

        TESTRESULTS.append(this_result)
    #  #]
    if DO_SETUP_SDIST_TESTS:
        #  #[ build a tarfile using setup sdist, unpack, build and check
        # -create a temporary working dir for the build
        build_dir_name = 'build_sdist_'+fc
        temp_build_dir = os.path.join(TESTDIR, build_dir_name)
        if os.path.exists(temp_build_dir):
            print('dir: ', temp_build_dir, ' exists; removing it first')
            cmd = '\\rm -rf '+temp_build_dir
            os.system(cmd)

        # -clone the repository
        cmd = 'cd '+TESTDIR+'; hg clone '+REPODIR+' '+build_dir_name
        print("Executing command: ", cmd)
        os.system(cmd)

        # -edit the setup.cfg file to choose the compiler
        #  and to prevent the library download
        cfg_file = os.path.join(temp_build_dir, 'setup.cfg')

        cfg_lines = open(cfg_file).readlines()

        # save a backup copy by moving the original
        # os.rename(cfg_file, cfg_file+'.orig')

        fd = open(cfg_file, 'w')
        for l in cfg_lines:
            if 'preferred_fortran_compiler' in l:
                fd.write('preferred_fortran_compiler='+fc+'\n')
            elif 'download_library_sources' in l:
                fd.write('download_library_sources = False\n')
            else:
                fd.write(l)
        fd.close()

        # commit the modified code, to track what happended incase
        # I would pull from this modified repository by mistake.
        cmd = 'cd '+temp_build_dir+';'+\
              'hg commit -m "automatic commit by the build_test tool"'
        (lines_stdout, lines_stderr) = run_shell_command(cmd)

        # -build the software
        cmd = 'cd '+temp_build_dir+';'+\
              'python ./setup.py sdist'
        os.system(cmd)

        # -verify the presence of the generated tar file
        pattern = os.path.join(temp_build_dir, 'dist/pybufr-ecmwf*gz')
        tar_files = glob.glob(pattern)

        this_result = []
        this_result.append('test results for setup sdist test for: '+fc)
        if len(tar_files) > 0:
            this_result.append('tar file found: '+tar_files[0])
        else:
            this_result.append('ERROR: tar file NOT found!')

        # create a test directory
        test_dir = os.path.join(temp_build_dir, 'temp_test')
        os.makedirs(test_dir)

        # split path and filename
        (tar_path, tar_file) = os.path.split(tar_files[0])

        # unpack the created ter file
        cmd = 'cd '+test_dir+'; tar zxvf ../dist/'+tar_file
        os.system(cmd)

        pattern = os.path.join(test_dir, 'pybufr-ecmwf-*')
        unpacked_sdist_path = glob.glob(pattern)[0]
        # print('TESTJOS: unpacked_sdist_path = ', unpacked_sdist_path)

        # -edit the setup.cfg file to choose the compiler
        #  and to prevent the library download
        cfg_file = os.path.join(unpacked_sdist_path, 'setup.cfg')

        cfg_lines = open(cfg_file).readlines()

        # save a backup copy by moving the original
        #os.rename(cfg_file, cfg_file+'.orig')

        # this mod is not needed since the sdist takes the
        # modification made before running the setup sdist
        # command with it.
        fd = open(cfg_file, 'w')
        for l in cfg_lines:
            if 'preferred_fortran_compiler' in l:
                fd.write('preferred_fortran_compiler='+fc+'\n')
            elif 'download_library_sources' in l:
                fd.write('download_library_sources = False\n')
            else:
                fd.write(l)
        fd.close()

        # -build the software
        cmd = 'cd '+unpacked_sdist_path+';'+\
              'python ./setup.py build'
        os.system(cmd)

        # -verify the presence of the generated ecmwfbufr.so file
        so_files = glob.glob(os.path.join(unpacked_sdist_path,
                                      'build/lib*/pybufr_ecmwf/ecmwfbufr.so'))

        this_result.append('test results for sdist build for: '+fc)
        if len(so_files) > 0:
            this_result.append('so file found: '+so_files[0])
        else:
            this_result.append('ERROR: so file NOT found!')

        # -run the unit tests
        cmd = 'cd '+unpacked_sdist_path+';'+\
              'python ./unittests.py'
        # os.system(cmd)
        (lines_stdout, lines_stderr) = run_shell_command(cmd)
        for l in lines_stdout:
            this_result.append('STDOUT: '+l.replace('\n', ''))
        for l in lines_stderr:
            this_result.append('STDERR: '+l.replace('\n', ''))

        TESTRESULTS.append(this_result)
        #  #]
    if DO_PIP_INSTALL_TESTS:
        #  #[ build a tarfile using setup sdist, unpack, build and check
        # -create a temporary working dir for the build
        build_dir_name = 'build_pip_'+fc
        temp_build_dir = os.path.join(TESTDIR, build_dir_name)
        if os.path.exists(temp_build_dir):
            print('dir: ', temp_build_dir, ' exists; removing it first')
            cmd = '\\rm -rf '+temp_build_dir
            os.system(cmd)

        # -clone the repository
        cmd = 'cd '+TESTDIR+'; hg clone '+REPODIR+' '+build_dir_name
        print("Executing command: ", cmd)
        os.system(cmd)

        # -edit the setup.cfg file to choose the compiler
        #  and to prevent the library download
        cfg_file = os.path.join(temp_build_dir, 'setup.cfg')

        cfg_lines = open(cfg_file).readlines()

        # save a backup copy by moving the original
        # os.rename(cfg_file, cfg_file+'.orig')

        fd = open(cfg_file, 'w')
        for l in cfg_lines:
            if 'preferred_fortran_compiler' in l:
                fd.write('preferred_fortran_compiler='+fc+'\n')
            elif 'download_library_sources' in l:
                fd.write('download_library_sources = False\n')
            else:
                fd.write(l)
        fd.close()

        # commit the modified code, to track what happended incase
        # I would pull from this modified repository by mistake.
        cmd = 'cd '+temp_build_dir+';'+\
              'hg commit -m "automatic commit by the build_test tool"'
        (lines_stdout, lines_stderr) = run_shell_command(cmd)

        # -build the software
        cmd = 'cd '+temp_build_dir+';'+\
              'python ./setup.py sdist'
        os.system(cmd)

        # -verify the presence of the generated tar file
        pattern = os.path.join(temp_build_dir, 'dist/pybufr-ecmwf*gz')
        tar_files = glob.glob(pattern)

        this_result = []
        this_result.append('test results for pip test for: '+fc)
        if len(tar_files) > 0:
            this_result.append('tar file found: '+tar_files[0])
        else:
            this_result.append('ERROR: tar file NOT found!')

        # create a test directory
        test_dir = os.path.join(temp_build_dir, 'temp_test')
        os.makedirs(test_dir)

        # split path and filename
        (tar_path, tar_file) = os.path.split(tar_files[0])

        # setup a virtualenv and try to install the package in it
        cmds = ['cd '+test_dir,
                'virtualenv myenv --system-site-packages',
                'source myenv/bin/activate',
                'pip install pybufr-ecmwf --no-index '+\
                '--find-links '+\
                os.path.abspath(os.path.join(temp_build_dir, 'dist')),
                'python -c "import pybufr_ecmwf;'+\
                'print \'pybufr_ecmwf.__file__ = \', pybufr_ecmwf.__file__"',
                'deactivate',
                'rm -rf myenv/']

        cmd = ';'.join(c for c in cmds)
        print('executing cmd: [{}]'.format(cmd))
        (lines_stdout, lines_stderr) = run_shell_command(cmd)

        # -verify the output
        module_properly_loaded = False
        for l in  lines_stdout:
            if (('pybufr_ecmwf.__file__' in l) and
                ('__init__.py' in l)):
                module_properly_loaded = True
        if module_properly_loaded:
            this_result.append('module_properly_loaded.')
        else:
            this_result.append('ERROR: something seems wrong: '+\
                               'module not properlyloaded!')
        TESTRESULTS.append(this_result)
        #  #]
    if DO_MANUAL_PY3_TESTS:
        #  #[ convert to python3, and test the manual build

        # -create a temporary working dir for the build
        build_dir_name = 'py3_manual_build_'+fc
        temp_build_dir = os.path.join(TESTDIR, build_dir_name)
        if os.path.exists(temp_build_dir):
            print('dir: ', temp_build_dir, ' exists; removing it first')
            cmd = '\\rm -rf '+temp_build_dir
            os.system(cmd)

        # not needed, the clone command creates the dir
        # print('creating dir: ', temp_build_dir)
        # os.mkdir(temp_build_dir)

        # -clone the repository
        cmd = 'cd '+TESTDIR+'; hg clone '+REPODIR+' '+build_dir_name
        print("Executing command: ", cmd)
        os.system(cmd)

        # step into the test dir
        saved_cwd = os.getcwd()
        os.chdir(temp_build_dir)

        print('temp_build_dir = ', temp_build_dir)
        print('saved_cwd   = ', saved_cwd)
        print('os.getcwd() = ', os.getcwd())

        # convert the source code to python3
        cmd = './port_2to3.py'
        print("Executing command: ", cmd)
        os.system(cmd)

        temp_py3_build_dir = 'tmp_2to3_converted_sources'

        os.chdir(temp_py3_build_dir)

        print('temp_py3_build_dir = ', temp_py3_build_dir)
        print('os.getcwd() = ', os.getcwd())

        # -build the software
        sys.path.append(os.getcwd())
        # print('sys.path = ', sys.path)

        # note: this re-import is intentional, since this should be a
        # different copy, then the one used by DO_MANUAL_TESTS,
        # so temporarily disable the re-import pylint warning
        #pylint: disable=W0404
        from build_interface import InstallBUFRInterfaceECMWF
        #pylint: enable=W0404

        BI = InstallBUFRInterfaceECMWF(verbose=True,
                                       preferred_fortran_compiler=fc,
                                       download_library_sources=False)

        # make sure we are in the right directory
        BUILD_DIR = 'pybufr_ecmwf'
        os.chdir(BUILD_DIR)

        BI.build()
        del BI

        # the py3 test almost works now. It fails in the f2py stage
        # in the post-processing (stage 2) with this message:
        # (seems to me this is a bug in f2py)

        # Post-processing (stage 2)...
        # Saving signatures to file "f2py_build/signatures.pyf"
        # Traceback (most recent call last):
        #  File "./run_f2py_tool.py", line 11, in <module>
        #    main()
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/f2py2e.py", line 563, in main
        #    run_main(sys.argv[1:])
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/f2py2e.py", line 342, in run_main
        #    postlist=callcrackfortran(files,options)
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/f2py2e.py", line 279, in callcrackfortran
        #    pyf=crackfortran.crack2fortran(postlist)
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/crackfortran.py", line 2693, in crack2fortran
        #    pyf=crack2fortrangen(block)+'\n'
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/crackfortran.py", line 2465, in crack2fortrangen
        #    ret=ret+crack2fortrangen(g,tab)
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/crackfortran.py", line 2505, in crack2fortrangen
        #    body=crack2fortrangen(block['body'],tab+tabchar)
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/crackfortran.py", line 2465, in crack2fortrangen
        #    ret=ret+crack2fortrangen(g,tab)
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/crackfortran.py", line 2505, in crack2fortrangen
        #    body=crack2fortrangen(block['body'],tab+tabchar)
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/crackfortran.py", line 2465, in crack2fortrangen
        #    ret=ret+crack2fortrangen(g,tab)
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/crackfortran.py", line 2506, in crack2fortrangen
        #    vars=vars2fortran(block,block['vars'],al,tab+tabchar)
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/crackfortran.py", line 2655, in vars2fortran
        #    lst = true_intent_list(vars[a])
        #  File "/usr/lib64/python3.2/site-packages/numpy/f2py/crackfortran.py", line 2557, in true_intent_list
        #    if c:
        # UnboundLocalError: local variable 'c' referenced before assignment
        # ERROR: build of python wrapper failed
        # the signatures file could not be found
        # Traceback (most recent call last):
        #  File ".//build_test.py", line 388, in <module>
        #    BI.build()
        #  File "/home/jos/werk/pybufr_ecmwf_interface/pybufr-ecmwf/build_interface.py", line 543, in build
        #    self.generate_python_wrapper(source_dir)
        #  File "/home/jos/werk/pybufr_ecmwf_interface/pybufr-ecmwf/build_interface.py", line 1667, in generate_python_wrapper
        #    raise InterfaceBuildError
        # build_interface.InterfaceBuildError
        #

        # this bug in f2py has been reported here:
        #        http://projects.scipy.org/numpy/ticket/1932
        # and here:
        #       https://github.com/numpy/numpy/issues/3192

        #sys.exit(1)

        # restore the original directory
        os.chdir(saved_cwd)

        # -verify the presence of the generated ecmwfbufr.so file
        so_files = glob.glob(os.path.join(temp_build_dir, BUILD_DIR,
                                          'ecmwfbufr.*.so'))

        this_result = []
        this_result.append('test results for manual build for: '+fc)
        if len(so_files) > 0:
            this_result.append('so file found: '+so_files[0])
        else:
            this_result.append('ERROR: so file NOT found!')

        # -run the unit tests
        cmd = 'cd '+temp_build_dir+';'+\
              'python3 ./unittests.py'
        # os.system(cmd)
        (lines_stdout, lines_stderr) = run_shell_command(cmd)
        for l in lines_stdout:
            this_result.append('STDOUT: '+l.replace('\n', ''))
        for l in lines_stderr:
            this_result.append('STDERR: '+l.replace('\n', ''))

        TESTRESULTS.append(this_result)

        #  #]

print(50*'=')
for result in TESTRESULTS:
    #  #[ display the results
    for l in result:
        print(l)
    print(50*'=')
    #  #]
