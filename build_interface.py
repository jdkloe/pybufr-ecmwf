#!/usr/bin/env python
"""
This module implements building the ECMWF BUFR library and creation of
a python interface around the BUFR library provided by
ECMWF to allow reading and writing the WMO BUFR file standard.
"""

#  #[ documentation
#
# Note about the use of the "#  #[" and "#  #]" comments:
#   these are folding marks for my favorite editor, emacs, combined with its
#   folding mode
#   (see http://www.emacswiki.org/emacs/FoldingMode for more details)
# Please do not remove them.
#
# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI (www.knmi.nl),
#
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html
#
#  #]
#  #[ imported modules
from __future__ import (absolute_import, division,
                        print_function) # , unicode_literals)
import os          # operating system functions
import sys         # operating system functions
import glob        # allow for filename expansion
import tarfile     # handle tar archives
import shutil      # portable file copying functions
import subprocess  # support running additional executables
import stat        # handling of file stat data
import datetime    # date handling functions

from pybufr_ecmwf.helpers import (get_and_set_the_module_path,
                                  get_software_root)
from pybufr_ecmwf.custom_exceptions import (ProgrammingError,
                                            LibraryBuildError,
                                            InterfaceBuildError)
# not used: BuildException
#  #]
#  #[ constants

# the first one found will be used, unless a preferred one is specified.
POSSIBLE_F_COMPILERS = ['gfortran', 'g95', 'g77',
                        'f90', 'f77', 'ifort', 'pgf90', 'pgf77']
POSSIBLE_C_COMPILERS = ['gcc', 'icc', 'cc']
# define common compiler flags for each compiler
# (also used for the custom case)
FFLAGS_COMMON = ['-O', '-Dlinux', '-fPIC']
CFLAGS_COMMON = ['-O', '-fPIC']
# define specific compiler flags for each compiler
# needed to build the ECMWF BUFR library
FFLAGS_NEEDED = {'g95': ['-i4', '-r8', '-fno-second-underscore'],
                 'gfortran': ['-fno-second-underscore', ],
                 'gfortran_10': ['-fno-second-underscore',
                                 '-fallow-argument-mismatch',],
                 'g77': ['-i4', ],
                 'f90': ['-i4', ],
                 'f77': ['-i4', ],
                 'pgf90': ['-i4', ],
                 'pgf77': ['-i4', ],
                 'ifort': ['-i4', ]}
CFLAGS_NEEDED = {'gcc': [],
                 'icc': [],
                 'cc':  []}

for k in FFLAGS_NEEDED:
    FFLAGS_NEEDED[k].extend(FFLAGS_COMMON)
for k in CFLAGS_NEEDED:
    CFLAGS_NEEDED[k].extend(CFLAGS_COMMON)

SO_FILE_PATTERN = 'ecmwfbufr.cpython*.so'

#  #]

#  #[ some helper functions
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
    new_mode = None
    if mode == 'r':
        new_mode = current_mode | int("444", 8)
    if mode == 'w':
        new_mode = current_mode | int("222", 8)
    if mode == 'x':
        new_mode = current_mode | int("111", 8)
    if mode == 'rx':
        new_mode = current_mode | int("555", 8)
    if new_mode:
        os.chmod(filename, new_mode)
    else:
        print('ERROR in ensure_permissions: unknown mode string: ', mode)
        raise ProgrammingError
    #  #]
def run_shell_command(cmd, libpath=None, catch_output=True,
                      module_path='./', verbose=True):
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
    if libpath:
        # add the additional env setting
        envname = "LD_LIBRARY_PATH"
        if envname in env:
            env[envname] = env[envname] + ":" + libpath
        else:
            env[envname] = libpath

    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = env['PYTHONPATH']+':'+module_path
    else:
        env['PYTHONPATH'] = module_path

    if verbose:
        print("Executing command: ", cmd)

    if catch_output:
        # print('env[PYTHONPATH] = ', env['PYTHONPATH'])
        subpr = subprocess.Popen(cmd, shell=True, env=env,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        # wait until the child process is done
        # subpr.wait() # seems not necessary when catching stdout and stderr

        if sys.version_info[0] == 2:
            lines_stdout = subpr.stdout.readlines()
            lines_stderr = subpr.stderr.readlines()
        elif sys.version_info[0] == 3:
            # in python 3 the readlines() method returns bytes,
            # so convert them to a unicode string for convenience
            tmp_lines_stdout = subpr.stdout.readlines()
            tmp_lines_stderr = subpr.stderr.readlines()
            lines_stdout = []
            lines_stderr = []
            for line in tmp_lines_stdout:
                lines_stdout.append(line.decode('utf-8'))
            for line in tmp_lines_stderr:
                lines_stderr.append(line.decode('utf-8'))
        else:
            errtxt = 'This python version is not supported: '+sys.version
            raise NotImplementedError(errtxt)

        #print("lines_stdout: ", lines_stdout)
        #print("lines_stderr: ", lines_stderr)

        return (lines_stdout, lines_stderr)

    else:
        subpr = subprocess.Popen(cmd, shell=True, env=env)

        # wait until the child process is done
        subpr.wait()
        return
    #  #]
def fortran_compile_and_execute(fcmp, fflags, f_code, f_executable, f_libpath):
    #  #[
    """ convenience routine to compile and execute a bit of fortran code,
    and to return the stdout and stderr generated by the just compiled code.
    """
    f_file = f_executable+".F90"
    tfd = open(f_file, 'w')
    tfd.write(f_code)
    tfd.close()

    # contruct the compile command
    cmd = fcmp+' '+fflags+' -o '+f_executable+' '+f_file

    # now issue the compile command
    if f_libpath == "":
        print("Executing command: ", cmd)
        os.system(cmd)
    else:
        run_shell_command(cmd, libpath=f_libpath, catch_output=False)

    # now execute the just generated test program to verify if we succeeded
    # add a './' to ensure the executable is also found for users that
    # do not have '.' in their default search path
    cmd = os.path.join('.', f_executable)
    if f_libpath == "":
        (lines_stdout, lines_stderr) = run_shell_command(cmd)
    else:
        (lines_stdout, lines_stderr) = \
                       run_shell_command(cmd, libpath=f_libpath)

    # clean up
    os.remove(f_file)

    return (lines_stdout, lines_stderr)
    #  #]
def fortran_compile_test(fcmp, fflags, f_libpath):
    #  #[
    """ a method to check if we really have some fortran compiler
    installed (it writes a few lines of fortran, tries to compile
    it, and compares the output with the expected output) """

    # Note: for now the flags are not used in these test because these
    # are specific for generating a shared-object file, and will fail to
    # generate a simple executable for testing

    fortran_test_code = \
"""
program pybufr_test_program

  print *,'Hello pybufr module:'
  print *,'Fortran compilation seems to work fine ...'

end program pybufr_test_program
"""

    # generate a testfile with a few lines of Fortran90 code
    fortran_test_executable = "pybufr_fortran_test_program"
    (lines_stdout, lines_stderr) = \
                   fortran_compile_and_execute(fcmp, fflags, fortran_test_code,
                                               fortran_test_executable,
                                               f_libpath)

    expected_output = [' Hello pybufr module:\n',
                       ' Fortran compilation seems to work fine ...\n']
    if ((expected_output[0] not in lines_stdout) or
        (expected_output[1] not in lines_stdout)):
        print("ERROR: Fortran compilation test failed; "+
              "something seems very wrong")
        print("Expected output: ", expected_output)
        print('actual output stdout = ', lines_stdout)
        print('actual output stderr = ', lines_stderr)
        raise EnvironmentError

    print("Fortran compilation test successfull...")

    # clean up
    os.remove(fortran_test_executable)
    #  #]
def c_compile_and_execute(ccmp, cflags, c_code, c_executable, c_libpath):
    #  #[
    """ convenience routine to compile and execute a bit of c code,
    and to return the stdout and stderr generated by the just compiled code.
    """
    # Note: for now the flags are not used in these test because these
    # are specific for generating a shared-object file, and will fail to
    # generate a simple executable for testing
    # libpath may point to a custom LD_LIBRARY_PATH setting
    # needed to run the compiler
    c_file = c_executable+".c"
    tfd = open(c_file, 'w')
    tfd.write(c_code)
    tfd.close()

    # contruct the compile command
    cmd = ccmp+' '+cflags+' -o '+c_executable+' '+c_file

    # now issue the compile command
    if c_libpath == "":
        print("Executing command: ", cmd)
        os.system(cmd)
    else:
        run_shell_command(cmd, libpath=c_libpath, catch_output=False)

    # now execute the just generated program
    # add a './' to ensure the executable is also found for users that
    # do not have '.' in their default search path
    cmd = os.path.join('.', c_executable)
    if c_libpath == "":
        (lines_stdout, lines_stderr) = run_shell_command(cmd)
    else:
        (lines_stdout, lines_stderr) = run_shell_command(cmd, libpath=c_libpath)

    # clean up
    os.remove(c_file)

    return (lines_stdout, lines_stderr)
    #  #]
def c_compile_test(ccmp, cflags, c_libpath):
    #  #[
    """ a method to check if we really have some c compiler
    installed (it writes a few lines of c, tries to compile
    it, and compares the output with the expected output) """

    c_test_code = \
r"""
#include <stdio.h>
int main()
{
  printf("Hello pybufr module:\n");
  printf("c compilation seems to work fine ...\n");
  return 0;
}
"""

    # generate a testfile with a few lines of Fortran90 code
    c_test_executable = "pybufr_c_test_program"
    (lines_stdout, lines_stderr) = \
                       c_compile_and_execute(ccmp, cflags, c_test_code,
                                             c_test_executable, c_libpath)

    expected_output = ['Hello pybufr module:\n',
                       'c compilation seems to work fine ...\n']
    if ((expected_output[0] not in lines_stdout) or
        (expected_output[1] not in lines_stdout)):
        print("ERROR: c compilation test failed; something seems very wrong")
        print("Expected output: ", expected_output)
        print('actual output stdout = ', lines_stdout)
        print('actual output stderr = ', lines_stderr)
        raise EnvironmentError

    print("c compilation test successfull...")

    # clean up
    os.remove(c_test_executable)
    #  #]
def retrieve_integer_sizes(ccmp, cflags, c_libpath,
                           fcmp, fflags, f_libpath):
    #  #[
    """ some trickery to retrieve the currently used integer variable
    sizes in both fortran and c
    """
    #CSIZEINT=`../support/GetByteSizeInt`
    #CSIZELONG=`../support/GetByteSizeLong`
    #F90SIZEINT=`../support/GetByteSizeDefaultInteger`

    c_code = \
r"""
#include <stdio.h>
int main()
{
  int testinteger;
  printf("%zu\n",sizeof(testinteger));
  return 0;
}
"""
    c_executable = 'GetByteSizeInt'
    lines_stdout = c_compile_and_execute(ccmp, cflags, c_code,
                                         c_executable, c_libpath)[0]
    bytesizeint = lines_stdout[0].strip()

    c_code = \
r"""
#include <stdio.h>
int main()
{
  long testinteger;
  printf("%zu\n",sizeof(testinteger));
  return 0;
}
"""
    c_executable = 'GetByteSizeLong'
    lines_stdout = c_compile_and_execute(ccmp, cflags, c_code,
                                         c_executable, c_libpath)[0]
    bytesizelong = lines_stdout[0].strip()

    f90_code = \
r"""
program GetByteSizeDefaultInteger
  integer :: default_integer, nbytes_default_integer
  inquire(iolength=nbytes_default_integer) default_integer
  print *,nbytes_default_integer
end program GetByteSizeDefaultInteger
"""
    f90_executable = 'GetByteSizeDefaultInteger'
    lines_stdout = \
        fortran_compile_and_execute(fcmp, fflags, f90_code,
                                    f90_executable, f_libpath)[0]
    try:
        bytesizedefaultinteger = lines_stdout[0].strip()
    except IndexError:
        bytesizedefaultinteger = None

    if bytesizedefaultinteger is None:
        # try again, now defining nbytes_default_integer explicitely
        # as 8-byte integer, which seems needed if you compile
        # with g95-64 bit version combined with the -i4 option
        f90_code = \
r"""
program GetByteSizeDefaultInteger
  integer :: default_integer
  integer*8 :: nbytes_default_integer
  inquire(iolength=nbytes_default_integer) default_integer
  print *,nbytes_default_integer
end program GetByteSizeDefaultInteger
"""
        f90_executable = 'GetByteSizeDefaultInteger'
        lines_stdout = \
                     fortran_compile_and_execute(fcmp, fflags, f90_code,
                                                 f90_executable, f_libpath)[0]
        try:
            bytesizedefaultinteger = lines_stdout[0].strip()
        except IndexError:
            bytesizedefaultinteger = None

    if bytesizedefaultinteger is None:
        txt = 'ERROR: could not retrieve bytesizedefaultinteger '+\
              'for this fortran compiler: '+fcmp
        raise ProgrammingError(txt)

    # print('GetByteSizeInt:  ',bytesizeint)
    # print('GetByteSizeLong: ',bytesizelong)
    # print('GetByteSizeDefaultInteger: ',bytesizedefaultinteger)

    return (bytesizeint, bytesizelong, bytesizedefaultinteger)
    #  #]
def insert_pb_interface_definition(sfd, integer_sizes):
    #  #[
    """ the pb interface routines are mostly written in c, so f2py
    will not automatically generate their signature. This
    subroutine explicitely adds these signatures.
    """

    #(ByteSizeInt, ByteSizeLong, ByteSizeDefaultInteger) = integer_sizes
    bytesizelong = integer_sizes[1]

    #intlen = None
    #if ByteSizeDefaultInteger == ByteSizeInt:
    #    intlen = ByteSizeInt # = 4 bytes
    #if ByteSizeDefaultInteger == ByteSizeLong:
    #    intlen = ByteSizeLong # = 8 bytes

    intlen = bytesizelong # = 8 bytes
    print('Using intlen = ', intlen, ' to build the pbio interface')

    indentation = 8*' '
    lines_to_add = \
         ["subroutine pbopen(cFileUnit,BufrFileName,mode,bufr_error_flag)",
          #"   intent(c) pbopen"
          #"   intent(c)"
          "   integer*"+intlen+",        intent(out) :: cFileUnit",
          "   character(len=*), intent(in)  :: BufrFileName",
          "   character(len=1), intent(in)  :: mode",
          "   integer*"+intlen+",        intent(out) :: bufr_error_flag",
          "end subroutine pbopen",
          "subroutine pbclose(cFileUnit,bufr_error_flag)",
          "   integer*"+intlen+",        intent(inplace) :: cFileUnit",
          "   integer*"+intlen+",        intent(inplace) :: bufr_error_flag ",
          "end subroutine pbclose",
# this one is implemented in Fortran, and is handled by
# adapt_f2py_signature_file defined next, so manual fix is needed for it.
#  "subroutine pbbufr(cFileUnit,Buffer,BufferSizeBytes,MsgSizeBytes,&",
#  "                  bufr_error_flag)",
#  "   integer*"+intlen+",              intent(inplace) :: cFileUnit",
#  "   integer*"+intlen+",dimension(*), intent(inplace) :: Buffer",
#  "   integer*"+intlen+",              intent(inplace) :: BufferSizeBytes",
#  "   integer*"+intlen+",              intent(inplace) :: MsgSizeBytes",
#  "   integer*"+intlen+",              intent(inplace) :: bufr_error_flag ",
#  "end subroutine pbbufr",
          "subroutine pbwrite(cFileUnit,Buffer,MsgSizeBytes,bufr_return_value)",
          "   integer*"+intlen+",              intent(inplace) :: cFileUnit",
          "   integer*"+intlen+",dimension(*), intent(inplace) :: Buffer",
          "   integer*"+intlen+",              intent(inplace) :: MsgSizeBytes",
          "   integer*"+intlen+\
          ",              intent(inplace) :: bufr_return_value",
          "end subroutine pbwrite",
          "subroutine pbseek(cFileUnit,offset,whence,bufr_return_value)",
          "   integer*"+intlen+", intent(in)  :: cFileUnit",
          "   integer*"+intlen+", intent(in)  :: offset",
          "   integer*"+intlen+", intent(in)  :: whence",
          "   integer*"+intlen+", intent(out) :: bufr_return_value",
          "end subroutine pbseek"]

    print("Inserting hardcoded interface to pbio routines in "+
          "signatures file ...")
    for lta in lines_to_add:
        sfd.write(indentation+lta+'\n')

    #  #]
def adapt_f2py_signature_file(signature_file, integer_sizes, set_jelem,
                              verbose=False):
    #  #[
    """
    some code to adapt the signature file generated by the f2py tool.
    Regrettably this is needed since this tool seems not to handle
    constant parameters defined in include files properly.
    """
    # NOTE: maybe this modification is not needed if I can get the file
    #       with the parameters included in an other way.
    #       Looking at the f2py manpage the option -include might do the
    #       trick but that one is depricated. In stead a usercode section
    #       should be used, but that again means modifying the signature
    #       file ...
    #       Also the --include_paths option might be related.
    # TODO: sort this out (handling of constant parameters by f2py)

    #signature_file = "f2py_build/signatures.pyf"

    # these values are defined in parameter.F
    # PARAMETER(JSUP =   9,
    #          JSEC0=   3,
    #          JSEC1=  40,
    #          JSEC2=4096,
    #          JSEC3=   4
    #          JSEC4=   2,
    #          JELEM=320000,
    #          JSUBS=400,
    #          JCVAL=150 ,
    #          JBUFL=512000,
    #          JBPW =  32,
    #          JTAB =3000,
    #          JCTAB=3000,
    #          JCTST=9000,
    #          JCTEXT=9000,
    #          JWORK=4096000,
    #          JKEY=46,
    #          JTMAX=10,
    #          JTCLAS=64,
    #          JTEL=255)

    # WARNING:
    # these numbers really should NOT be hardcoded here
    # but extracted from the fortran code.
    # However, at this point in time the interface to
    # fortran is not yet available, so for now use this
    # quick and dirty workaround...
    edits = {}
    edits['JSUP'] = 9
    edits['JSEC0'] = 3
    edits['JSEC1'] = 40
    edits['JSEC2'] = 4096
    edits['JSEC3'] = 4
    edits['JSEC4'] = 2
    if set_jelem is not None:
        edits['JELEM'] = str(set_jelem)
    else:
        edits['JELEM'] = 320000
    edits['JSUBS'] = 400
    edits['JCVAL'] = 150
    edits['JBUFL'] = 512000
    edits['JBPW'] = 32
    edits['JTAB'] = 3000
    edits['JCTAB'] = 3000
    edits['JCTST'] = 9000
    edits['JCTEXT'] = 9000
    edits['JWORK'] = 4096000
    edits['JKEY'] = 46
    edits['JTMAX'] = 10
    edits['JTCLAS'] = 64
    edits['JTEL'] = 255
    # edits[''] =

    # read the file
    lines = open(signature_file).readlines()

    # create a backup copy, to allow manual inspection
    source = signature_file
    destination = signature_file+".bak"
    shutil.copyfile(source, destination)

    print("Fixing array size definitions in signatures definition ...")
    sfd = open(signature_file, "w")
    inside_subroutine = False
    inside_retrieve_settings = False
    inside_pbbufr_sign = False
    for line in lines:

        mod_line = line

        if 'end subroutine' in mod_line:
            inside_subroutine = False
        elif 'subroutine' in mod_line:
            inside_subroutine = True

        if 'end subroutine retrieve_settings' in mod_line:
            inside_retrieve_settings = False
        elif 'subroutine retrieve_settings' in mod_line:
            inside_retrieve_settings = True

        if 'end subroutine pbbufr' in mod_line:
            inside_pbbufr_sign = False
        elif 'subroutine pbbufr' in mod_line:
            inside_pbbufr_sign = True

        if inside_subroutine:
            if ' ::' in mod_line:
                # Add the intent(inplace) switch to all subroutine
                # parameters.
                # This might not be very pretty, but otherwise all
                # parameters are assigned the default, which is intent(in).
                # Maybe the proper way would be to sort out for each routine
                # in this library which parameters are intent(in) and
                # which are intent(out), but this is a huge task (and
                # should be done by ECMWF rather then by us I think...)
                if not 'intent(out)' in mod_line:
                    # do this only for code that has no explicit intent(out)
                    (part1, part2) = mod_line.split(' ::')
                    if inside_retrieve_settings:
                        # explicitely add intent(out)
                        # this seems needed for the python3 case!
                        mod_line = part1+',intent(out) ::'+part2
                    else:
                        mod_line = part1+',intent(inplace) ::'+part2

        if inside_pbbufr_sign:
            # fix a bug in the pbbufr.F fortran code that causes f2py to
            # fail on interfacing to this routine
            if 'integer dimension(1),intent(inplace) :: karray' in mod_line:
                mod_line = mod_line.replace('dimension(1)', 'dimension(*)')

        if 'dimension' in mod_line:
            for edit in edits:
                # the value inside the dimension() spec
                # in the signature file sometimes has extra braces.
                # sometimes not (depending on the f2py version).
                # and in case of 2 dimensions, the value to be replaced
                # ends with a comma.
                # So at least 3 cases are to be considered here.
                txt1 = '(('+edit.lower()+'))'
                txt2 = '('+edit.lower()+')'
                txt3 = '('+edit.lower()+','
                value1 = '('+str(edits[edit])+')'
                value2 = '('+str(edits[edit])+')'
                value3 = '('+str(edits[edit])+','
                if txt1 in mod_line:
                    mod_line = mod_line.replace(txt1, value1)
                elif txt2 in mod_line:
                    mod_line = mod_line.replace(txt2, value2)
                elif txt3 in mod_line:
                    mod_line = mod_line.replace(txt3, value3)

        if mod_line.strip() == "end interface":
            # NOTE: the pb interface routines are written in c, so f2py
            # will not automatically generate their signature. This next
            # subroutine call explicitely adds these signatures.
            insert_pb_interface_definition(sfd, integer_sizes)

        if verbose:
            if mod_line != line:
                print("adapting line: ", line)
                print("to           : ", mod_line)

        sfd.write(mod_line)

    sfd.close()
    #  #]
def descend_dirpath_and_find(input_dir, glob_pattern):
    #  #[
    """
    a little helper routine that steps down the different components
    of the provided directory path, and tests for the presence of
    a file that matches the given glob pattern.
    If a match is found, the directory in which the match is present,
    and a list of matching files is returned.
    If no match is found a tuple with two None values is returned.
    """
    absdirname = os.path.abspath(input_dir)
    # print('start: absdirname = ',absdirname)
    while absdirname != "/":
        pattern = os.path.join(absdirname, glob_pattern)
        filelist = glob.glob(pattern)
        if len(filelist) > 0:
            # print('descend_dirpath_and_find succeeded: result')
            # print('(absdirname, filelist) = ',(absdirname, filelist))
            return (absdirname, filelist)
        base = os.path.split(absdirname)[0]
        absdirname = base
        # print('next: absdirname = ',absdirname)

    # print('descend_dirpath_and_find failed: no result found')
    return (None, None)
    #  #]
def extract_version():
    #  #[
    """ a little function to extract the module version from
    the setup.py script, and if present, extract the mercurial
    revision from the hg repository, and store it in a place where
    the user can access it.
    """

    # assume we are inside the pybufr_ecmwf module dir
    # when this function is executed.

    # retrieve the software version
    software_version = 'unknown'
    (setuppath, setupfiles) = descend_dirpath_and_find(os.getcwd(), 'setup.py')
    if not setuppath:
        print('ERROR: could not locate setup.py script needed to extract')
        print('ERROR: the current software version')
        raise ProgrammingError

    for line in open(os.path.join(setuppath, setupfiles[0])).readlines():
        if 'version=' in line:
            quoted_version = line.split('=')[1].replace(',', '')
            software_version = quoted_version.replace("'", '').strip()

    # retrieve mercurial revision if possible
    hg_version = 'undefined'
    if os.path.exists('.hg'):
        cmd = 'hg log -l 1'
        lines_stdout = run_shell_command(cmd)[0]
        for line in lines_stdout:
            if 'changeset:' in line:
                hg_version = line.split()[1]

    # retrieve git revision if possible
    git_version = 'undefined'
    if os.path.exists('.git'):
        cmd = 'git log -n 1'
        lines_stdout = run_shell_command(cmd)[0]
        for line in lines_stdout:
            if 'commit:' in line:
                git_version = line.split()[1]

    # retrieve the install date (i.e. todays date)
    # current date formatted as: 07-aug-2009
    install_date = datetime.date.today().strftime("%d-%b-%Y")

    # store the result
    version_file = 'version.py'
    fds = open(version_file, 'w')
    fds.write("software_version = '"+software_version+"'\n")
    fds.write("hg_version = '"+hg_version+"'\n")
    fds.write("git_version = '"+git_version+"'\n")
    fds.write("install_date = '"+install_date+"'\n")
    fds.write("version = '"+software_version+'; '+\
             hg_version+'; '+install_date+"'\n")
    fds.close()
    ensure_permissions(version_file, 'rx')
    #  #]
def symlink_to_all_files(source_dir, dest_dir):
    #  #[ create symlinks in dest_dir for all links in source_dir
    '''
    a helper routine to create symbolic links to all available
    BUFR tables in the dest_dir directory.
    '''
    filelist_b = glob.glob(os.path.join(source_dir, 'B*'))
    filelist_c = glob.glob(os.path.join(source_dir, 'C*'))
    filelist_d = glob.glob(os.path.join(source_dir, 'D*'))
    filelist = filelist_b
    filelist.extend(filelist_c)
    filelist.extend(filelist_d)

    # first copy the real files
    for fnm in filelist:
        filename = os.path.split(fnm)[1]
        if not os.path.islink(fnm):
            dest = os.path.join(dest_dir, filename)
            shutil.copy(fnm, dest)
            # and make sure they are world readable
            # to ensure the module can be used by all, even if
            # the setup.py build was done as root or using sudo
            os.chmod(dest, 0o0644)
            
    # then create all symlinks
    links = []
    for fnm in filelist:
        filename = os.path.split(fnm)[1]
        if os.path.islink(fnm):
            realname = os.path.realpath(fnm)
            realfilename = os.path.split(realname)[1]
            links.append((realfilename, filename))

    cwd = os.getcwd()
    os.chdir(dest_dir)
    for (realfilename, filename) in links:
        os.symlink(realfilename, filename)
    os.chdir(cwd)

    # print(filelist)
    # sys.exit(1)

    #  #]
def generate_c_underscore_wrapper(source_dir):
    #  #[ create macosx wrapper code
    print('starting generate_c_underscore_wrapper')
    source_file_list = source_dir+"/bufrdc/*.F "+\
                       source_dir+"/pbio/pbbufr.F"
    # print(source_file_list)
    wrapper_name = source_dir+"/pbio/c_macosx_wrapper.c"
    fd_out = open(wrapper_name,'w')
    for pattern in source_file_list.split():
        for fortran_file in glob.glob(pattern):
            cmd = 'grep -i subroutine '+fortran_file
            (lines_stdout, lines_stderr) = run_shell_command(cmd, verbose=False)
            # these lines are unicode strings in python3
            for line in lines_stdout:
                def_line = line.strip()
                #print('['+def_line+']')
                if def_line=='':
                    continue
                if def_line[0]!='C':
                    subr_name = def_line.split()[1].split('(')[0]
                    #print('file: '+fortran_file,
                    #      'subr_name: '+subr_name)
                    fd_out.write('extern void *{0}_();\n'.\
                                 format(subr_name))
                    fd_out.write('void *_{0}_() {{ return {1}_(); }}\n\n'.\
                                 format(subr_name, subr_name))

    # manually add the 4 needed c-functions from pbio.c
    for c_func in ['pbopen', 'pbclose', 'pbwrite', 'pbseek']:
        fd_out.write('extern void *{0}();\n'.\
                     format(c_func))
        fd_out.write('void *_{0}() {{ return {1}(); }}\n\n'.\
                     format(c_func, c_func))

    fd_out.close()

    print('Created wrapper: '+wrapper_name)
    return wrapper_name
    #  #]
#  #]

class InstallBUFRInterfaceECMWF(object):
    #  #[ the main builder class
    """
    a class that builds the interface between the ECMWF
    BUFR library and python,
    """
    def __init__(self, verbose=False,
                 preferred_fortran_compiler=None,
                 preferred_c_compiler=None,
                 fortran_compiler=None,
                 fortran_ld_library_path=None,
                 fortran_flags=None,
                 c_compiler=None,
                 c_ld_library_path=None,
                 c_flags=None,
                 set_jelem=None,
                 debug_f2py_c_api=False):
        #  #[

        # first remove any quotes that may be around the strings
        # (this may happen if the user uses quotes in the setup.cfg file)
        self.preferred_fortran_compiler = rem_quotes(preferred_fortran_compiler)
        self.preferred_c_compiler = rem_quotes(preferred_c_compiler)
        self.fortran_compiler = rem_quotes(fortran_compiler)
        self.fortran_ld_library_path = rem_quotes(fortran_ld_library_path)
        self.c_compiler = rem_quotes(c_compiler)
        self.c_ld_library_path = rem_quotes(c_ld_library_path)
        self.fortran_flags = rem_quotes(fortran_flags)
        self.c_flags = rem_quotes(c_flags)
        self.set_jelem = set_jelem
        self.debug_f2py_c_api = debug_f2py_c_api

        # save the verbose setting
        self.verbose = verbose

        # save the location to be used for installing the ECMWF BUFR library
        self.ecmwf_bufr_lib_dir = "./ecmwf_bufr_lib"

        # define the names of the library and shared object files
        # that will be created by this class
        self.bufr_lib_file = "libbufr.a"

        self.wrapper_build_dir = "f2py_build"
        self.wrapper_module_name = "ecmwfbufr"

        # init other module attributes to None
        self.fortran_compiler_to_use = None
        self.c_compiler_to_use = None

        # variable to store current integer sizes in c and Fortran
        self.integer_sizes = None
        #  #]
    def build(self):
        #  #[
        """a method to start building the BUFR interface"""

        bufr_was_build = False
        wrapper_was_build = False

        # check for the presence of the library
        if os.path.exists(self.bufr_lib_file):
            print("BUFR library seems present")
        else:
            print("Entering installation sequence:")
            self.install()
            print("compilation of BUFR library finished")
            bufr_was_build = True

        try:
            wrapper_name = glob.glob(SO_FILE_PATTERN)[0]
        except IndexError:
            wrapper_name = 'undefined'

        if os.path.exists(wrapper_name):
            print("python wrapper seems present")
        else:
            print("Entering wrapper generation sequence:")
            source_dir = self.get_source_dir()[0]
            self.generate_python_wrapper(source_dir)
            print("compilation of library wrapper finished")
            wrapper_was_build = True

        if (not bufr_was_build) and (not wrapper_was_build):
            print("\nNothing to do\n"+
                  "Execute the clean.py tool if you wish to start again "+
                  "from scratch.")

        print('extracting library constants')
        self.extract_constants()

        print('storing version info')
        extract_version()

        print('copying sample files')
        self.copy_sample_files()
        #  #]
    def rebuild(self):
        #  #[ rebuild the software
        """ same as install, but always run the make, even if the
        wrapper library already seems present"""
        self.install(remake=True)
        source_dir = self.get_source_dir()[0]
        self.generate_python_wrapper(source_dir, remake=True)
        #  #]
    def clean(self):
        #  #[
        """ a method to clean-up things that I don't want to have
        included in the binary/rpm distributions."""

        # if verbose is set this signals we are debugging the
        # code, so do not remove temp folders in that case
        #if self.verbose:
        return

        # this is a bit of a dirty hack.
        # It removes the subdir ecmwf_bufr_lib and everything below
        # to prevent it to be included in the binary/rpm distributions
        # There should be a nicer way to do this, but I have not
        # yet found it ...

        dirs_to_remove = [self.ecmwf_bufr_lib_dir,
                          self.wrapper_build_dir]

        for dir_to_remove in dirs_to_remove:
            if os.path.exists(dir_to_remove):
                cmd = r'\rm -rf '+dir_to_remove
                print("executing command: ", cmd)
                os.system(cmd)
        #  #]
    def use_bundled_library_copy(self):
        #  #[
        """ copy the bundled version
        of the library sources stored in ecmwf_bufr_lib_sources.
        We must descend the directory tree first to find the root
        before doing this copy. """

        # make sure the destination dir exists
        if not os.path.exists(self.ecmwf_bufr_lib_dir):
            os.makedirs(self.ecmwf_bufr_lib_dir)

        cwd = os.getcwd()
        absdirname = os.path.abspath(cwd)
        while absdirname != "/":
            files = os.listdir(absdirname)
            if "setup.cfg" in files:
                pattern = os.path.join(absdirname,
                                       'ecmwf_bufr_lib_sources',
                                       'bufrdc_000*.tar.gz')
                tgz_filelist = glob.glob(pattern)
                if len(tgz_filelist) > 0:
                    tgz_file = tgz_filelist[0]

                    cmd = 'cp '+tgz_file+' '+self.ecmwf_bufr_lib_dir
                    print("Executing command: ", cmd)
                    os.system(cmd)
                    break

            base = os.path.split(absdirname)[0]
            absdirname = base

        # return to the original location
        os.chdir(cwd)
        #  #]
    def use_bundled_tables_dir_copy(self):
        #  #[
        """ copy the bundled version of the updated bufr tables
        in ecmwf_bufr_lib_sources.
        We must descend the directory tree first to find the root
        before doing this copy. """

        # make sure the destination dir exists
        if not os.path.exists(self.ecmwf_bufr_lib_dir):
            os.makedirs(self.ecmwf_bufr_lib_dir)

        cwd = os.getcwd()
        absdirname = os.path.abspath(cwd)
        while absdirname != "/":
            files = os.listdir(absdirname)
            if "setup.cfg" in files:
                pattern = os.path.join(absdirname,
                                       'ecmwf_bufr_lib_sources',
                                       'bufrdc_tables*.tar.gz')
                tgz_filelist = glob.glob(pattern)
                if len(tgz_filelist) > 0:
                    tgz_file = tgz_filelist[-1] # take the newest file

                    cmd = 'cp '+tgz_file+' '+self.ecmwf_bufr_lib_dir
                    print("Executing command: ", cmd)
                    os.system(cmd)
                    break
                else:
                    errtxt = ('Sorry, could not find replacement bufr tables '+
                              'tar file. Something seems wrong with '+
                              'this installation.')
                    raise LibraryBuildError(errtxt)

            base = os.path.split(absdirname)[0]
            absdirname = base

        # return to the original location
        os.chdir(cwd)
        #  #]
    def get_source_dir(self):
        #  #[
        """ a method to find the name of the current BUFR library
        sources (after unpacking the tarball), and also the name
        of the current tarball."""

        # save the location to be used for installing the ECMWF BUFR library
        ecmwf_bufr_lib_dir = "./ecmwf_bufr_lib"
        list_of_bufr_tarfiles = glob.glob(os.path.join(ecmwf_bufr_lib_dir,
                                                       "bufrdc_000*.tar.gz"))

        # safety catch
        if len(list_of_bufr_tarfiles) == 0:
            return (None, None)

        # sort in reverse alphabetical order to get the newest one on top
        list_of_bufr_tarfiles.sort(reverse=True)
        if self.verbose:
            print("available library tarfiles: ", list_of_bufr_tarfiles)
            print("most recent library tarfile: ", list_of_bufr_tarfiles[0])

        tarfile_to_install = os.path.split(list_of_bufr_tarfiles[0])[1]

        # find out the actual name of the library source directory
        # after unpacking. Use the tarfile module and look inside:
        tarfile_obj = tarfile.open(list_of_bufr_tarfiles[0], 'r:gz')
        names = tarfile_obj.getnames()
        #print("names[0:5] = ", names[0:5])
        # this library holds everything in a single subdirectory named something
        # like bufr_000380, so I guess it is safe to assume that the first name
        # in the archive will be the name of this directory.
        bufr_dir = names[0]
        tarfile_obj.close()

        source_dir = os.path.join(ecmwf_bufr_lib_dir, bufr_dir)

        return (source_dir, tarfile_to_install)
        #  #]
    def get_tables_source_dir(self):
        #  #[
        """ a method to find the name of the current BUFR tables
        sources (after unpacking the tarball), and also the name
        of the current tarball."""

        # save the location to be used for installing the ECMWF BUFR library
        ecmwf_bufr_lib_dir = "./ecmwf_bufr_lib"
        list_of_bufr_tables_tarfiles = \
                     glob.glob(os.path.join(ecmwf_bufr_lib_dir,
                                            "bufrdc_tables*.tar.gz"))

        # safety catch
        if len(list_of_bufr_tables_tarfiles) == 0:
            return (None, None)

        # sort in reverse alphabetical order to get the newest one on top
        list_of_bufr_tables_tarfiles.sort(reverse=True)
        if self.verbose:
            print("available bufr tables tarfiles: ",
                  list_of_bufr_tables_tarfiles)
            print("most recent bufr_tables tarfile: ",
                  list_of_bufr_tables_tarfiles[0])

        tarfile_to_install = os.path.split(list_of_bufr_tables_tarfiles[0])[1]

        # find out the actual name of the bufr tables source directory
        # after unpacking. Use the tarfile module and look inside:
        tarfile_obj = tarfile.open(list_of_bufr_tables_tarfiles[0], 'r:gz')
        names = tarfile_obj.getnames()
        # print("names[0:5] = ", names[0:5])

        # get the dir name from the second element in the list
        bufr_tables_dir = os.path.split(names[1])[0]
        tarfile_obj.close()

        bufr_tables_dir = os.path.join(ecmwf_bufr_lib_dir, bufr_tables_dir)

        # print('bufr_tables_dir = ', bufr_tables_dir)
        # print('tarfile_to_install = ', tarfile_to_install)
        # sys.exit(1)
        
        return (bufr_tables_dir, tarfile_to_install)
        #  #]
    def install(self, remake=False):
        #  #[
        """ a method to compile the ECMWF BUFR library """

        if not remake:
            #  #[ find and unpack the ECMWF BUFR library tar file

            # first see if there is already a tarfile available
            # (the user may have provided one)
            (source_dir, tarfile_to_install) = self.get_source_dir()

            if source_dir is None:
                # copy the bundled version
                # of the library sources stored in ecmwf_bufr_lib_sources
                print('Using bundled library copy...')
                self.use_bundled_library_copy()
                
                # retry (now we should have a copy of the tarfile)
                (source_dir, tarfile_to_install) = self.get_source_dir()
            else:
                # debug print
                # print('(source_dir, tarfile_to_install) = ',
                #      (source_dir, tarfile_to_install))
                pass

            # safety catch
            if source_dir is None:
                print("ERROR: extracting source_dir failed")
                raise LibraryBuildError

            if not os.path.exists(source_dir):
                # safety catch
                if tarfile_to_install == None:
                    print("ERROR: no tarfile available for BUFR library.")
                    raise LibraryBuildError

                if self.verbose:
                    cmd = "cd "+self.ecmwf_bufr_lib_dir+\
                          ";tar zxvf "+tarfile_to_install
                else:
                    cmd = "cd "+self.ecmwf_bufr_lib_dir+\
                          ";tar zxf "+tarfile_to_install
                
                print("Executing command: ", cmd)
                os.system(cmd)
            else:
                print("path exists: ", source_dir)
                print("assuming the package is already unpacked...")

            # extract numerical BUFR library version
            # this should be something like: bufrdc_000389
            try:
                bufr_dir = os.path.split(source_dir)[1]
                parts = bufr_dir.split('_')
                if len(parts) > 1:
                    bufrdir_version = int(parts[1])
                else:
                    # exception seems needed for version 000401
                    # which unpacks as 000401 without bufrdc_ prepended
                    bufrdir_version = int(parts[0])
                # print('bufr_dir = ',bufr_dir)
                # print('bufrdir_version = ',bufrdir_version)
            except:
                print('ERROR: could not extract numerical BUFR library')
                print('version number ...')
                print('Please report this bug.')
                raise ProgrammingError
            #  #]
            #  #[ add a few small fortran routines
            add_fortran_dir_list = \
                descend_dirpath_and_find(os.getcwd(),
                                         'additional_fortran_code')[1]

            add_fortran_dir = add_fortran_dir_list[0]

            additional_fortran_files = ['handle_stdout.F',
                                        'retrieve_settings.F',
                                        #'add_debug_code.F',
                                        'reset_global_variables.F',
                                        'set_nokey.F']
            for fortr_file in additional_fortran_files:
                shutil.copy(os.path.join(add_fortran_dir, fortr_file),
                            os.path.join(source_dir, 'bufrdc', fortr_file))
                print('copied file: '+fortr_file)

            # add these new source files to the sources list to include it in
            # the compilation and library creation procedure

            sources_file = os.path.join(source_dir, 'bufrdc', 'sources')
            fds = open(sources_file, 'r')
            sources_lines = fds.readlines()
            fds.close()

            # save the original with a modified name
            os.system('mv '+sources_file+' '+sources_file+'.orig')

            fds = open(sources_file, 'w')
            fds.write(''.join(line for line in sources_lines[:5]))
            for fortr_file in additional_fortran_files:
                fds.write('   '+fortr_file+' \\\n')
                print('added file '+fortr_file+' to the sources list')
            fds.write(''.join(line for line in sources_lines[5:]))
            fds.close()
            #  #]
            #  #[ force value of jelem if desired
            if self.set_jelem is not None:
                param_file = os.path.join(source_dir, 'bufrdc',
                                          'parameter.F')
                print('paramfile: ', param_file)
                os.rename(param_file, param_file+'.orig')
                fds_in = open(param_file+'.orig', 'rb')
                fds_out = open(param_file, 'wb')
                for line in fds_in.readlines():
                    print(line)
                    if b'JELEM=' in line:
                        part1 = line.split(b'JELEM=')[0]+b'JELEM='
                        part2 = b',JSUBS='+line.split(b',JSUBS=')[1]
                        replaced_line = part1+str(self.set_jelem)+part2
                        print('Replacing line: [{}]'.format(line.strip()))
                        print('       by line: [{}]'.
                              format(replaced_line.strip()))
                        fds_out.write(replaced_line)
                    else:
                        fds_out.write(line)
                fds_in.close()
                fds_out.close()
                os.chmod(param_file, 0o755)
            #  #]
            #  #[ install bufr tables update package
            print('source_dir = ', source_dir)
            tables_dir = os.path.join(source_dir, 'bufrtables')

            #print('deleting original tables dir')
            #shutil.rmtree(tables_dir)
            print('renaming original tables dir')
            shutil.move(tables_dir, tables_dir+'.orig')

            # get a copy of the bundled replacement tables dir
            # and place it in the ecmwf_bufr_lib dir
            self.use_bundled_tables_dir_copy()

            (replacement_bufr_tables_dir, tables_tarfile_to_install) = \
                         self.get_tables_source_dir()
            print('replacement_bufr_tables_dir = ',
                  replacement_bufr_tables_dir)
            print('tables_tarfile_to_install = ',
                  tables_tarfile_to_install)

            print('unpack replacement bufr tables dir')
            ecmwf_bufr_lib_dir = "./ecmwf_bufr_lib"
            cmd = ('cd '+ecmwf_bufr_lib_dir+
                   ';tar xvfz '+tables_tarfile_to_install)
            print('Executing: ', cmd)
            os.system(cmd)

            # ensure permissions are sane
            # (version 000412 has no write permission, which
            #  breaks the clean command...)
            cmd = 'chmod -R u+w '+replacement_bufr_tables_dir
            print('Executing: ', cmd)
            os.system(cmd)
            
            # rename the bufr tables dir to put it in the right location
            cmd = 'mv '+replacement_bufr_tables_dir+' '+tables_dir
            print('Executing: ', cmd)
            os.system(cmd)
            #  #]

            #  #[ apply a smal patch to the 000409 test.sh script
            # this patch ensures the correct bufrtables directory is used
            # during execution of this test script
            # Reported to ECMWF in jira issue SUP-1727
            if tarfile_to_install == 'bufrdc_000409.tar.gz':
                scr_file = os.path.join(source_dir, 'test.sh')
                os.rename(scr_file, scr_file+'.orig')
                fds_in = open(scr_file+'.orig', 'rb')
                fds_out = open(scr_file, 'wb')
                for line in fds_in.readlines():
                    if not ( (b'set -ex' in line) or
                             (b'BUFR_TABLES=/var/tmp' in line) ):
                        fds_out.write(line)
                fds_in.close()
                fds_out.close()
                os.chmod(scr_file, 0o755)
            #  #]
            #  #[ apply a smal patch to the Makefile
            # this patch disables execution of the tables_tools/check_tables.sh
            # test script during the make stage, because it fails for
            # this bufr tables update package due to minor table formatting
            # problems (which are probably not noticed at all by the fortran
            # and python code, but the regexp in the perl check script
            # stumbles on this problem).
            # Reported to ECMWF in jira issue SUP-2096
            if tables_tarfile_to_install in \
                   ['bufrdc_tables-4.1.1-Source.tar.gz',
                    'bufrdc_tables-4.1.2.tar.gz']:
                for fn in ['Makefile', 'Makefile.in']:
                    mk_file = os.path.join(source_dir, fn)
                    if os.path.exists(mk_file):
                        print('Modifying: ', mk_file)
                        os.rename(mk_file, mk_file+'.orig')
                        fds_in = open(mk_file+'.orig', 'rb')
                        fds_out = open(mk_file, 'wb')
                        for line in fds_in.readlines():
                            if not b'check_tables.sh' in line:
                                fds_out.write(line)
                        fds_in.close()
                        fds_out.close()
                        os.chmod(mk_file, 0o755)
            #  #]
            
        #  #[ find a suitable fortran compiler to use

        #if (self.verbose):
        print('selection fortran compiler')
        print('==>input: self.fortran_compiler = ', self.fortran_compiler)
        print('==>input: self.preferred_fortran_compiler = ',
              self.preferred_fortran_compiler)

        # first check a possible custom executable, passed in
        # through the setup.cfg file or on the commandline
        is_present = self.check_presence(self.fortran_compiler)
        if is_present:
            self.fortran_compiler_to_use = 'custom'

        # the first one found will be used, unless a preferred one is specified.
        for f_compiler in POSSIBLE_F_COMPILERS:
            if self.preferred_fortran_compiler == f_compiler:
                if self.check_presence(f_compiler):
                    self.fortran_compiler_to_use = f_compiler
                    break # stop the for loop

        if self.fortran_compiler_to_use is None:
            # a sanity check
            if self.preferred_fortran_compiler is not None:
                if not (self.preferred_fortran_compiler in
                        POSSIBLE_F_COMPILERS):
                    print("ERROR: unknown preferred fortran compiler "+
                          "specified:",
                          self.preferred_fortran_compiler)
                    print("valid options are: ",
                          ", ".join(s for s in POSSIBLE_F_COMPILERS))
                    raise NotImplementedError

            print("preferred fortran compiler ["+
                  str(self.preferred_fortran_compiler)+
                  "] seems not available...")
            print("falling back to default fortran compiler")

            for f_compiler in POSSIBLE_F_COMPILERS:
                is_present = self.check_presence(f_compiler)
                if is_present:
                    self.fortran_compiler_to_use = f_compiler
                    break # stop the for loop

        if self.fortran_compiler_to_use is None:
            print("ERROR: no valid fortran compiler found,")
            print("installation is not possible")
            print("Please install a fortran compiler first.")
            print("Good options are the free GNU compilers")
            print("gfortran and g95 which may be downloaded free of charge.")
            print("(see: http://gcc.gnu.org/fortran/  ")
            print(" and: http://www.g95.org/         )")
            raise EnvironmentError

        #if (self.verbose):
        print('selection fortran compiler')
        print('==>result: self.fortran_compiler_to_use = ',
              self.fortran_compiler_to_use)

        #  #]

        #  #[ find a suitable c compiler to use

        #if (self.verbose):
        print('selection c compiler')
        print('==>input: self.c_compiler = ', self.c_compiler)
        print('==>input: self.preferred_c_compiler = ',
              self.preferred_c_compiler)

        # first check a possible custom executable, passed in
        # through the setup.cfg file or on the commandline
        is_present = self.check_presence(self.c_compiler)
        if is_present:
            self.c_compiler_to_use = 'custom'

        # the first one found will be used, unless a preferred one is specified.
        for c_compiler in POSSIBLE_C_COMPILERS:
            if self.preferred_c_compiler == c_compiler:
                if self.check_presence(c_compiler):
                    self.c_compiler_to_use = c_compiler
                    break # stop the for loop

        if self.c_compiler_to_use is None:
            # a sanity check
            if self.preferred_c_compiler is not None:
                if self.preferred_c_compiler not in POSSIBLE_C_COMPILERS:
                    print("ERROR: unknown preferred c compiler "+
                          "specified:",
                          self.preferred_c_compiler)
                    print("valid options are: ",
                          ", ".join(s for s in POSSIBLE_C_COMPILERS))
                    raise NotImplementedError

            if self.preferred_c_compiler is None:
                print("no preferred c compiler given")
            else:
                print("preferred c compiler ["+
                      str(self.preferred_c_compiler)+
                      "] seems not available...")
            print("falling back to default c compiler")

            for c_compiler in POSSIBLE_C_COMPILERS:
                is_present = self.check_presence(c_compiler)
                if is_present:
                    self.c_compiler_to_use = c_compiler
                    break # stop the for loop

        if self.c_compiler_to_use is None:
            print("ERROR: no valid c compiler found,")
            print("installation is not possible")
            print("Please install a c compiler first.")
            print("A good option is the free GNU compiler gcc")
            print("which may be downloaded free of charge.")
            print("(see: http://gcc.gnu.org/ )")
            raise EnvironmentError

        #if (self.verbose):
        print('selection c compiler')
        print('==>result: self.c_compiler_to_use = ', self.c_compiler_to_use)

        #  #]

        #  #[ add the custom LD_LIBRARY_PATH settings
        libpath = ""
        if self.fortran_ld_library_path != None:
            libpath = ";".join(s for s in
                               [libpath, self.fortran_ld_library_path]
                               if s != "")
        if self.c_ld_library_path != None:
            libpath = ";".join(s for s in
                               [libpath, self.c_ld_library_path]
                               if s != "")

        if libpath != "":
            print("Using LD_LIBRARY_PATH setting: ", libpath)
        #  #]

        if not remake:
            #  #[ generate a config file for compilation of the BUFR library

            #------------------------------------------------------------------#
            # Possible commands to the make command for the BUFR library,      #
            # in case you wish to use the config files from the ECMWF software #
            # package are: (see the README file within source_dir)             #
            # - architecture: ARCH=sgimips (or: decalpha,hppa,linux,rs6000,    #
            #                                   sun4)                          #
            # - 64 bit machine: R64=R64                                        #
            # - compiler name (only for linux or sun machines): CNAME=_gnu     #
            #                                                                  #
            #------------------------------------------------------------------#

            # NOTE that for the linux case the library has some hardcoded
            # switches to use 32-bit variables in its interfacing (at least
            # last time I looked), so DO NOT try to use the 64 bit option on
            # linux, even if you have a 64-bit processor and compiler
            # available !
            # Even if the code runs, it will fail miserably and cause
            # segmentation faults if you are lucky, or just plain nonsense
            # if you are out of luck ....
            # (see the files  bufrdc_000400/bufrdc/fortint.h and
            #  bufrdc_000400/pbio/fortint.h which hardcode JBPW_DEF to be 32
            # (JBPW defines number of bits per word to be used)

            # The following 4 settings determine the name of the config file
            # used by the Make command; look in the file
            # ecmwf_bufr_lib/bufr_000380/config/ to see all available versions.

            # ARCH="linux"
            # CNAME="_compiler"
            # R64=""
            # A64=""

            # note: usefull free compilers for linux that you can use are:
            # (at least for these config files are provided in the ECMWF BUFR
            #  package)
            # g77      : CNAME="_gnu"
            # g95      : CNAME="_g95"
            # gfortran : CNAME="_gfortran"

            # Notes on compiler switches:

            # for most compilers you should force the BUFR library to use 4 byte
            # integers as default integer. Do this by adding the "-i4" option.
            # This works for most compilers, with gfortran as known exception
            # (that one has this setting as default and does not have a
            #  commandline option to set it)

            # it seems the c compiler step needs the "-DFOPEN64" switch to be
            # set (at least it is present in most config files in the package)
            # but it is never used in the source code itself, so I guess it is
            # obsolete.

            fcmp = ''
            fflags = ''

            if self.fortran_compiler_to_use == 'custom':
                fcmp = self.fortran_compiler
                fflags = ' '.join(flags for flags in FFLAGS_COMMON)
            else:
                fcmp = self.fortran_compiler_to_use
                fflags_to_use = FFLAGS_NEEDED[fcmp]

                # exception for gfortran v10+
                if fcmp == 'gfortran':
                    version_file = 'gfortran_version.txt'
                    cmd = '{}  --version > {}'.format(fcmp, version_file)
                    os.system(cmd)
                    with open(version_file, 'rt') as fd_ver:
                        line = fd_ver.readline()
                    parts = line.split()
                    version = parts[3]
                    version_major = int(version.split('.')[0])

                    if version_major >= 10:
                        fflags_to_use = FFLAGS_NEEDED['gfortran_10']

                fflags = ' '.join(flags for flags in fflags_to_use)

            # add any custom flags given by the user
            if self.fortran_flags != None:
                fflags = fflags + ' ' + self.fortran_flags

            if self.c_compiler_to_use == 'custom':
                ccmp = self.c_compiler
                cflags = ' '.join(flags for flags in CFLAGS_COMMON)
            else:
                ccmp = self.c_compiler_to_use
                cflags = ' '.join(flags for flags in CFLAGS_NEEDED[ccmp])

            # add any custom flags given by the user
            if self.c_flags != None:
                cflags = cflags+' '+self.c_flags

            # no check implemented on the "ar" and "ranlib" commands yet
            # (easy to add if we woould need it)

            # a command to generate an archive (*.a) file
            arcmd = "ar"
            # a command to generate an index of an archive file
            rlcmd = "/usr/bin/ranlib"

            # Unfortunately, the config files supplied with this library seem
            # somewhat outdated and sometimes incorrect, or incompatible with
            # the current compiler version (since they seem based on some
            # older compiler version, used some time ago at ECMWF, and never
            # got updated). This especially is true for the g95 compiler.
            # Therefore we have decided (at KNMI) to create our own
            # custom config file in stead.
            # We just call it: config.linux_compiler
            # which seems safe for now, since ECMWF doesn't use that name.

            arch = "linux"
            cname = "_compiler"
            r64 = ""
            a64 = ""

            # construct the name of the config file to be used
            config_file = "config."+arch+cname+r64+a64
            fullname_config_file = os.path.join(source_dir, "config",
                                                config_file)

            # this check is only usefull if you use one of the existing
            # config files
            #if not os.path.exists(fullname_config_file):
            #    # see if a version with ".in" extension is present
            #    # and if so, symlink to it.
            #    if not os.path.exists(fullname_config_file+".in"):
            #        print("ERROR: config file not found: ",
            #              fullname_config_file)
            #        raise IOError
            #    else:
            #        os.symlink(config_file+".in", fullname_config_file)

            # create our custom config file:
            print("Using: "+fcmp+" as fortran compiler")
            print("Using: "+ccmp+" as c compiler")

            print("Creating ECMWF-BUFR config file: ", fullname_config_file)
            cfd = open(fullname_config_file, 'w')
            cfd.write("#   Generic configuration file for linux.\n")
            cfd.write("AR         = "+arcmd+"\n")
            cfd.write("ARFLAGS    = rv\n")
            cfd.write("CC         = "+ccmp+"\n")
            cfd.write("CFLAGS     = "+cflags+"\n")
            cfd.write("FASTCFLAGS = "+cflags+"\n")
            cfd.write("FC         = "+fcmp+"\n")
            cfd.write("FFLAGS     = "+fflags+"\n")
            cfd.write("VECTFFLAGS = "+fflags+"\n")
            cfd.write("RANLIB     = "+rlcmd+"\n")
            cfd.close()

            # create a backup copy in the ecmwf_bufr_lib_dir
            source = fullname_config_file
            destination = os.path.join(self.ecmwf_bufr_lib_dir, "config_file")
            shutil.copyfile(source, destination)
            #  #]

        if (not remake) and (bufrdir_version > 387):
            #  #[ generate fortran2c config file for newer bufr versions
            # fortran2c_compiler contains the extra libraries needed
            # to link the objects created with the current fortran
            # compiler with a main program created with the
            # current c-compiler
            fortran2c_name = 'fortran2c_compiler'
            fortran2c_target = os.path.join(source_dir, "config",
                                            fortran2c_name)
            fortran2c_source = None
            if self.fortran_compiler_to_use == 'g95':
                fortran2c_source = os.path.join(source_dir, "config",
                                                'fortran2c_g95')
                shutil.copyfile(fortran2c_source, fortran2c_target)

            if self.fortran_compiler_to_use == 'gfortran':
                fortran2c_source = os.path.join(source_dir, "config",
                                                'fortran2c_gfortran')
                # just copying the provided file fails for me
                # (gfortran 4.7.x also needs -lm during the link stage)
                #shutil.copyfile(fortran2c_source, fortran2c_target)
                fd_f2c = open(fortran2c_target, 'w')
                fd_f2c.write('FORTRAN2C = -lgfortran -lm')
                fd_f2c.close()

            if self.fortran_compiler_to_use == 'pgf90':
                fortran2c_source = os.path.join(source_dir, "config",
                                                'fortran2c')
                shutil.copyfile(fortran2c_source, fortran2c_target)

            if fortran2c_source is None:
                fortran2c_source = os.path.join(source_dir, "config",
                                                'fortran2c_gnu')
                shutil.copyfile(fortran2c_source, fortran2c_target)

            #  #]
            #  #[ generate the makefile for newer bufr versions
            # bufr library versions 000388 and newer have changed the
            # build and install procedure. They have a new 'build_library'
            # script that tries to guess system parameters and then
            # creates the Makefile from Makefile.in by applying a series
            # of 'sed' commands. However, this script is interactive and
            # asks the use several questions. Therefore this python
            # script bypasses this build_library script and tries to do
            # the same for linux without user intervention

            # makefiles are created from Makefile.in
            # in these directories:
            makefile_dirs = ['.', 'bufrdc', 'bufrtables', 'pbio', 'fortranC',
                             'examples', 'synop2bufr',
                             'synop2bufr/station_list']
            install_dir = 'dummy' # seems never used in the makefiles
            replacements = [('%reals%', r64),
                            ('%install_dir%', install_dir),
                            ('%arch%', arch),
                            ('%comp%', cname),
                            ('%plat%', a64),
                            ('%depl%', 'bufr')]
            for makefile_dir in makefile_dirs:
                makefile = os.path.join(source_dir, makefile_dir, 'Makefile')
                makefile_template = makefile+'.in'
                if os.path.exists(makefile_template):
                    print('creating: ', makefile)
                    fd_makefile = open(makefile, 'w')
                    for line in open(makefile_template).readlines():
                        line_new = line
                        # print('adapting line: ',line)
                        for (old, new) in replacements:
                            line_new = line_new.replace(old, new)
                        fd_makefile.write(line_new)
                    fd_makefile.close()
            #  #]

        #  #[ compile little pieces of Fortran and c to test the compilers
        fortran_compile_test(fcmp, fflags, libpath)
        c_compile_test(ccmp, cflags, libpath)
        #  #]

        #  #[ retrieve integer sizes for c and fortran
        self.integer_sizes = retrieve_integer_sizes(ccmp, cflags, libpath,
                                                    fcmp, fflags, libpath)
        #  #]

        #  #[ now use the make command to build the library

        # construct the compilation command:
        cmd = "cd "+source_dir+";make ARCH="+arch+" CNAME="+\
              cname+" R64="+r64+" A64="+a64
        #if not self.verbose:
        cmd += " 2>1 > bufrdc_build.log"

        # now issue the Make command
        if libpath == "":
            print("Executing command: ", cmd)
            os.system(cmd)
        else:
            #(lines_stdout, lines_stderr) = \
            #      run_shell_command(cmd, libpath = libpath)
            run_shell_command(cmd, libpath=libpath, catch_output=False)
        #  #]
        #  #[ scan the build log for possible problems
        logfile = os.path.join(source_dir, 'bufrdc_build.log')
        text = b''
        if os.path.exists(logfile):
            fds = open(logfile,'rb')
            text = fds.read()
            fds.close()            
        problem_detected = False
        if b'failed' in text:
            problem_detected = True
        if b'FAILED' in text:
            problem_detected = True

        if problem_detected:
            print('\n\n')
            print('A problem was detected in the logfile: {0}'.
                  format(os.path.join(os.getcwd(), logfile)))
            print("Please investigate it or send it to the developer of")
            print("this module for analysis.")
            print("Build failed, aborting")
            sys.exit(1)

        #  #]
        #  #[ check the result and move the library file
        fullname_bufr_lib_file = os.path.join(source_dir, self.bufr_lib_file)
        if os.path.exists(fullname_bufr_lib_file):
            print("Build seems successfull")
            # remove any old library file that might be present
            if os.path.exists(self.bufr_lib_file):
                os.remove(self.bufr_lib_file)

            # move to a more convenient location
            shutil.move(fullname_bufr_lib_file, self.bufr_lib_file)
            ensure_permissions(self.bufr_lib_file, 'r')
        else:
            print("ERROR in bufr_interface_ecmwf.install:")
            print("No libbufr.a file seems generated.")
            raise LibraryBuildError
        #  #]

        if not remake:
            #  #[ copy the bufr tables
            # copy the directory holding the provided
            # BUFR tables, to a more convenient location
            # (don't move it since this will mess-up the build system
            # for library versions 000388 and above when trying
            # to do a rebuild.)
            fullname_table_dir = os.path.join(source_dir, "bufrtables")
            table_dir = "ecmwf_bufrtables"
            #shutil.copytree(fullname_table_dir, table_dir)
            os.mkdir(table_dir)
            symlink_to_all_files(fullname_table_dir, table_dir)

            # remove some excess files from the bufr tables directory
            # that we don't need any more (symlinks, tools)
            #tdfiles = os.listdir(table_dir)
            #for tdfile in tdfiles:
            #    fullname = os.path.join(table_dir, tdfile)
            #    if os.path.islink(fullname):
            #        os.unlink(fullname)
            #    else:
            #        ext = os.path.splitext(tdfile)[1]
            #        if not ext.upper() == ".TXT":
            #            os.remove(fullname)
            #        else:
            #            ensure_permissions(fullname, 'r')

            # select the newest set of tables and symlink them
            # to a default name (making sure a matching C table
            # is provided as well)
            pattern = os.path.join(table_dir, 'C0*098*.TXT')
            c_tables = glob.glob(pattern)
            # print('pattern = ',pattern)
            # print('c_tables = ',c_tables)

            if len(c_tables) > 0:
                c_tables.sort()
                # assume the highest numbered table is the most recent one
                ct_file = os.path.split(c_tables[-1])[1]
                ct_base, ct_ext = os.path.splitext(ct_file)
                newest_table_code = ct_base[1:]
                newest_c_table = ct_file
                newest_b_table = 'B'+newest_table_code+ct_ext
                newest_d_table = 'D'+newest_table_code+ct_ext

                default_b_table = 'B_default.TXT'
                default_c_table = 'C_default.TXT'
                default_d_table = 'D_default.TXT'

                current_path = os.getcwd()
                os.chdir(table_dir)
                os.symlink(newest_b_table, default_b_table)
                os.symlink(newest_c_table, default_c_table)
                os.symlink(newest_d_table, default_d_table)
                os.chdir(current_path)
            else:
                print('WARNING: no default table B, C and D found')
            #  #]

        #  #[ some old notes

        # save the settings for later use
        #self.make_settings = (arch, cname, r64, a64)
        #self.compilers     = (fcmp, fflags, ccmp, cflags)
        #self.tools         = (ar, rl)

        # actually, this saving of settings is not the way I would
        # prefer doing this. I think it is better to keep the 2 stages
        # (installation of the BUFR library, and generation of the
        #  python interface shared object) as separate as possible.
        # This allows rerunning generation of the python interface
        # without rerunning the installation of the BUFR library
        # (which will at least save a lot of time during development)
        #
        # So the generate_python_wrapper routine should just
        # read the config file generated above, and not use these
        # settings in self, that might not always be defined.
        #  #]

        #  #]
    def check_presence(self, command):
        #  #[
        """ a method to check for the presence of executable commands
        from a user shell (using the which command) """

        if self.verbose:
            print("checking for presence of command: "+str(command))

        if command == None:
            return False

        # get the real command, in case it was an alias
        cmd = "which "+command
        lines_stdout = run_shell_command(cmd, catch_output=True)[0]

        if len(lines_stdout) == 0:
            # command is not present in default path
            return False
        else:
            # command is present in default path
            return True
        #  #]
    def generate_python_wrapper(self, source_dir, remake=False):
        #  #[
        """ a method to call f2py to create a wrapper between the fortran
        library code and python. """

        #  #[ some settings
        signatures_filename = "signatures.pyf"
        f2py_tool_name = 'python3 ./run_f2py_tool.py'

        #f2py_tool_name = 'f2py'
        #os.system('chmod u+x '+f2py_tool_name)

        # open the config file used for building the ECMWF BUFR library
        config_file = os.path.join(self.ecmwf_bufr_lib_dir, "config_file")
        lines = open(config_file).readlines()

        # extract which fortran compiler is used
        fortran_compiler = 'undefined'
        fortran_compiler_flags = 'undefined'
        for line in lines:
            parts = line.split('=')
            if parts[0].strip() == "FC":
                fortran_compiler = parts[1].strip()
            if parts[0].strip() == "FFLAGS":
                fortran_compiler_flags = parts[1].strip()

        # apply ld_library path settings
        libpath = ""
        if self.fortran_ld_library_path != None:
            libpath = ";".join(s for s in
                               [libpath, self.fortran_ld_library_path]
                               if s != "")
        if self.c_ld_library_path != None:
            libpath = ";".join(s for s in
                               [libpath, self.c_ld_library_path]
                               if s != "")
        #  #]

        if not remake:
            #  #[ create signature file
            # just take them all (this works for me)
            source_file_list = source_dir+"/bufrdc/*.F "+\
                               source_dir+"/pbio/pbbufr.F"

            # call f2py and create a signature file that defines the
            # interfacing to the fortran routines in this library
            cmd = (f2py_tool_name+
                      " --overwrite-signature "+
                      " --build-dir "+self.wrapper_build_dir+
                      " -m "+self.wrapper_module_name+
                      " -h "+signatures_filename+
                      " "+source_file_list)

            #if not self.verbose:
            cmd += " 2>1 > f2py_build.log"

            if libpath == "":
                print("Executing command: ", cmd)
                os.system(cmd)
                # (lines_stdout, lines_stderr) = \
                #       run_shell_command(cmd, catch_output = True)
            else:
                print("Using LD_LIBRARY_PATH setting: ", libpath)
                # (lines_stdout, lines_stderr) = \
                #       run_shell_command(cmd, libpath = libpath,
                #                              catch_output = True)
                run_shell_command(cmd, libpath=libpath, catch_output=False)

            # safety check: see if the signatures.pyf file really is created
            signatures_fullfilename = os.path.join(self.wrapper_build_dir,
                                                   signatures_filename)
            if not os.path.exists(signatures_fullfilename):
                print("ERROR: build of python wrapper failed")
                print("the signatures file could not be found")
                raise InterfaceBuildError

            if self.verbose:
                # display signatures file since it seems not
                # possible to extract it from the github workflow
                fd_sig = open(signatures_fullfilename, 'rb')
                text = fd_sig.read()
                print('Starting dump of ', signatures_fullfilename)
                print(text)
                print('End of dump of ', signatures_fullfilename)
                fd_sig.close()

            # adapt the signature file
            # this is needed, since the wrapper generation fails to do a number
            # of file includes that are essential for the interface definition
            # To circumvent this, remove the not-properly defined constants
            # and replace them by their numerical values
            # (maybe there is a more clever way to do this in f2py, but I have
            #  not yet found another way ...)
            adapt_f2py_signature_file(signatures_fullfilename,
                                      self.integer_sizes, self.set_jelem,
                                      verbose=self.verbose)
            #  #]

            add_macosx_wrapper = False
            if add_macosx_wrapper:
                wrapper_name = generate_c_underscore_wrapper(source_dir)
                wrapper_object = os.path.splitext(wrapper_name)[0]+'.o'

                # compile the c wrapper code
                cmd = 'gcc -c '+wrapper_name+' -o '+wrapper_object
                os.system(cmd)
                
                # options
                # -r: insert into archive with replacement
                # -l: not used
                # -c: create the archive if it does not exist
                # -s: add/update an index to the archive
                # -v: verbose output

                # update the archive
                cmd = 'ar -rlcsv {0} {1}'.\
                      format(self.bufr_lib_file, wrapper_object)
                os.system(cmd)

        #  #[ create the wrapper interface
        # it might be usefull for debugging to include this option: --debug-capi
        debug_f2py_c_api_option = ""
        if self.debug_f2py_c_api:
            debug_f2py_c_api_option = " --debug-capi "

        if self.fortran_compiler != None:
            cmd = f2py_tool_name+\
                  " --build-dir "+self.wrapper_build_dir+\
                  debug_f2py_c_api_option+\
                  " --f90exec="+fortran_compiler+\
                  " --f90flags='"+fortran_compiler_flags+"'"+\
                  " --f77flags='"+fortran_compiler_flags+"'"+\
                  " ./f2py_build/signatures.pyf -L./ -lbufr -c"
        else:
            # note: adding the fortran_compiler_flags manually like this
            # causes some of them to be included twice, but this doesn't hurt,
            # and is the only way I get the automatic compilation using the
            # g95 compiler going.
            # TODO: Maybe later I could sort out how to use the python f2py
            # module in stead of the executable, and clean-up the compiler
            # flags before starting the tool
            cmd = f2py_tool_name+\
                  " --build-dir "+self.wrapper_build_dir+\
                  debug_f2py_c_api_option+\
                  " --f90flags='"+fortran_compiler_flags+"'"+\
                  " --f77flags='"+fortran_compiler_flags+"'"+\
                  " --fcompiler="+fortran_compiler+\
                  " ./f2py_build/signatures.pyf -L./ -lbufr -c"

        if not self.verbose:
            cmd += " 2>1 >> f2py_build.log"

        if libpath == "":
            print("Executing command: ", cmd)
            os.system(cmd)
            #(lines_stdout, lines_stderr) = \
            #       run_shell_command(cmd, catch_output = False)
        else:
            #(lines_stdout, lines_stderr) = \
            #       run_shell_command(cmd, libpath = libpath,
            #                              catch_output = True)
            run_shell_command(cmd, libpath=libpath, catch_output=False)

        #  #]

        # finally, again check for the presence of the wrapper
        # to see if the build was successfull
        try:
            wrapper_name = glob.glob(SO_FILE_PATTERN)[0]
        except IndexError:
            wrapper_name = 'undefined'

        if os.path.exists(wrapper_name):
            print("a python wrapper to the ECMWF BUFR library "+
                  "has been generated")
            return
        else:
            print("ERROR: build of python wrapper failed")
            print("the compilation or linking stage failed")
            raise InterfaceBuildError

        #  #]
    def extract_constants(self):
        #  #[ extract some hardcoded constants
        '''
        extract some hardcoded constants for reuse by the python code
        the ecmwfbufr interfacing is used to retrieve them,
        so this code is run when all interface building is done
        '''
        saved_cwd = os.getcwd()
        # print('saved_cwd = ', saved_cwd)
        os.chdir('..')
        sys.path = get_and_set_the_module_path(sys.path)[0]
        #(sys.path, MY_MODULE_PATH) = get_and_set_the_module_path(sys.path)
        # print('sys.path, MY_MODULE_PATH = ',sys.path, MY_MODULE_PATH)

        #from pybufr_ecmwf import ecmwfbufr
        import ecmwfbufr

        constants = ecmwfbufr.retrieve_settings()
        os.chdir(saved_cwd)

        keys = ['JSUP', 'JSEC0', 'JSEC1', 'JSEC2', 'JSEC3',
                'JSEC4', 'JELEM', 'JSUBS', 'JCVAL', 'JBUFL',
                'JBPW', 'JTAB', 'JCTAB', 'JCTST', 'JCTEXT',
                'JWORK', 'JKEY', 'JTMAX', 'JTCLAS', 'JTEL']
        parameter_dict = {}
        for (i, key) in enumerate(keys):
            parameter_dict[key] = constants[i]

        python_parameter_file = 'ecmwfbufr_parameters.py'
        print('creating parameter python file: ', python_parameter_file)
        pfd = open(python_parameter_file, 'w')

        # write a simple doc string
        pfd.write('"""')
        pfd.write("""
This is a little generated file to hold some constant parameters
defining all array sizes in the interfaces to the ecmwf library.
These constants are not available through the f2py interface.
They are defined in file:
ecmwf_bufr_lib/bufr_000380/bufrdc/parameter.F
and are extracted from that file and stored in this python
file for convenience
""")
        pfd.write('"""\n')

        # write the retrieved parameter values to a python file
        for (key, val) in parameter_dict.items():
            txt = key+' = '+str(val)+'\n'
            pfd.write(txt)

        # add some aliasses with easier names
        aliasses = ["LENGTH_SECTION_0 = JSEC0",
                    "LENGTH_SECTION_1 = JSEC1",
                    "LENGTH_SECTION_2 = JSEC2",
                    "LENGTH_SECTION_3 = JSEC3",
                    "LENGTH_SECTION_4 = JSEC4",
                    "LENGTH_SUPPORT_DATA   = JSUP",
                    "LENGTH_ECMWF_KEY_DATA = JKEY",
                    "NUM_BITS_PER_WORD        = JBPW",
                    "MAX_BUFR_MSG_LENGTH      = JBUFL",
                    "MAX_NR_TABLE_B_D_ENTRIES = JTAB",
                    "MAX_NR_TABLE_C_ENTRIES   = JCTAB",
                    "MAX_NR_OF_EXP_DATA_DESCRIPTORS = JELEM"]
                    # JSUBS=400 # seems not used
                    # JCVAL=150 # seems not used
                    # JCTST=9000 # size of text tables from table C
                    # JCTEXT=9000 # code table size ?
                    # JWORK=4096000 # size of data buffer when encoding sec.4
                    #
                    # JTMAX=10  ## these 3 define the MTABP tabel dimensions
                    # JTEL=255  ## used for storing BUFR tables in memory
                    # JTCLAS=64 ##

        for alias in aliasses:
            pfd.write(alias+'\n')

        pfd.close()

        # make sure the file is executable for all
        ensure_permissions(python_parameter_file, 'x')

        #  #]
    def copy_sample_files(self):
        #  #[ copy sample bufr files
        ''' copy sample bufr files provided by the ECMWF library
        to ensure they are available for testing, even after the
        build directory has been deleted again.
        '''

        swroot = get_software_root()
        source_dir = self.get_source_dir()[0]

        if source_dir is None:
            # this happens when the "setup.py build" stage has run
            # since that stage removes the library sources.
            # However, a "setup.py install" command reruns the build
            # and will trigger this condition.
            # No copying is needed anymore, so just return
            return
        
        data_dir = os.path.join(source_dir, 'data')
        sapp_sample_dir = os.path.join(source_dir, 'sapp_sample')

        target_dir = os.path.join(swroot, 'sample_bufr_files')
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
            
        for sample_dir in [data_dir, sapp_sample_dir]:
            for fn in os.listdir(sample_dir):
                src = os.path.join(sample_dir, fn)
                dst = os.path.join(target_dir, fn)
                if not os.path.exists(dst):
                    #print('src: {0} dst: {1}'.format(src, dst))
                    shutil.copy(src, dst)
    #  #]

    #  #]

if __name__ == "__main__":
    print("Building ecmwfbufr interface:\n")
    #  #[ make sure we are in the right directory
    BUILD_DIR = 'pybufr_ecmwf'
    os.chdir(BUILD_DIR)
    # print('cwd = ',os.getcwd())

    #  #]
    #  #[ define how to build the library and interface

    # instantiate the class, and build library if needed
    # (4 different tests defined for this step, with 4 different compilers)

    #TESTCASE = 1 # test default (=gfortran now)
    TESTCASE = 2 # test default gfortran
    #TESTCASE = 3 # test custom gfortran [broken for now]
    #TESTCASE = 4 # test custom g95-32 bit
    #TESTCASE = 5 # test custom g95-64 bit

    if TESTCASE == 1:
        # tested at my laptop at home with a systemwide
        # gfortran v4.7.0 installed
        # successfully tested 29-Aug-2012
        BI = InstallBUFRInterfaceECMWF(verbose=True)
        #BI = InstallBUFRInterfaceECMWF(verbose=True, debug_f2py_c_api=True)
    elif TESTCASE == 2:
        # tested at my laptop at home with a systemwide
        # gfortran v4.7.0 installed
        # successfully tested 29-Aug-2012
        BI = InstallBUFRInterfaceECMWF(verbose=True,
#                                       set_jelem=800000,
                                       preferred_fortran_compiler='gfortran')
        #                               c_flags="-fleading-underscore")
    elif TESTCASE == 3:
        # note that the "-O" flag is allways set for each fortran compiler
        # so no need to specify it to the fortran_flags parameter.

        # tested at my laptop at home with a gfortran v4.4.0 installed
        # in a user account
        # successfully tested 19-Mar-2010
        # NOTE: this gfortran is no longer installed, so no new testresults
        BI = InstallBUFRInterfaceECMWF(verbose=True,
                    fortran_compiler="/home/jos/bin/gfortran_personal",
                    fortran_ld_library_path="/home/jos/bin/gcc-trunk/lib64",
                    fortran_flags="-fno-second-underscore -fPIC")
    elif TESTCASE == 4:
        # tested at my laptop at home with a g95 v0.92 (32-bit) installed
        # in a user account
        # successfully tested 29-Aug-2012
        BI = InstallBUFRInterfaceECMWF(verbose=True,
                    fortran_compiler="/home/jos/bin/g95_32",
                    fortran_flags="-fno-second-underscore -fPIC -i4 -r8")
    elif TESTCASE == 5:
        # tested at my laptop at home with a g95 v0.92 (64-bit)
        # installed in a user account
        # successfully tested 29-Aug-2012
        BI = InstallBUFRInterfaceECMWF(verbose=True,
                    fortran_compiler="/home/jos/bin/g95_64",
                    fortran_flags="-fno-second-underscore -fPIC -i4 -r8")
    #  #]

    # Build ecmwfbufr interface
    BI.build()

    #  #[ check for success
    try:
        SO_WRAPPER_NAME = glob.glob(SO_FILE_PATTERN)[0]
    except IndexError:
        SO_WRAPPER_NAME = 'undefined'

    if os.path.exists(SO_WRAPPER_NAME):
        print("successfully build:", SO_WRAPPER_NAME)
    else:
        print("cannot find a file with pattern:", SO_FILE_PATTERN)
        print("something seems wrong here ...")
        raise InterfaceBuildError
    #  #]
