#!/usr/bin/env python

# NOTE: for debugging of this setup.py script
# set the DISTUTILS_DEBUG environment variable to TRUE
# (or any other non-empty string)

"""
This setup script can be used to build and install the pybufr-ecmwf
module on your system.
"""

#  #[ imported modules
import os
import sys
from distutils.core import setup, Extension
from distutils import log
from distutils.errors import DistutilsSetupError
# see: /usr/lib64/python2.6/distutils/errors.py
# for all available error classes

# import build and build_ext using a different name,
# to allow subclassing them
from distutils.command.build import build as _build
from distutils.command.build_ext import build_ext as _build_ext

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
from sys import version
if version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None
#  #]

# an alternative might be to use a setup version that seems present
# in the numpy module, see:
# http://www2-pcmdi.llnl.gov/cdat/tutorials/f2py-wrapping-fortran-code/\
#   part-4-packaging-all-this-into-something-that-can-be-distributed-\
#   very-advanced
# and http://www.scipy.org/Documentation/numpy_distutils
# the import would then be
# from numpy.distutils.core import setup, Extension

# suppres some pylint warnings caused by the internal implementation
# of the build class
#pylint: disable-msg=W0201,R0902,R0904

# note that pylint still complains about not being able to load the
# build_interface module, even though the setup routine itself
# seems to handle it just fine.

# modify the build class to allow some custom commandline
# and setup.cfg options to the build stage
class Build(_build):
    #  #[
    """Adapted Python binary builder."""
    user_options = _build.user_options
    user_options.append(("preferred-fortran-compiler", None,
                         "name of preferred fortran compiler to be used"))
    user_options.append(("preferred-c-compiler", None,
                         "name of preferred c compiler to be used"))
    user_options.append(("fortran-compiler", None,
                         "name and full path of fortran compiler to be used"))
    user_options.append(("fortran-ld-library-path", None,
                         "path in which shared objects can be found that "+\
                         "are needed by the choosen fortran compiler"))
    user_options.append(("fortran-flags", None,
                         "flags to be passed to the fortran compiler"))
    user_options.append(("c-compiler", None,
                         "name and full path of c compiler to be used"))
    user_options.append(("c-ld-library-path", None,
                         "path in which shared objects can be found that "+\
                         "are needed by the choosen c compiler"))
    user_options.append(("c-flags", None,
                         "flags to be passed to the c compiler"))

    def initialize_options(self):
        #  #[ initialise the additional options 
        """ initialise custom defined options """
        self.preferred_fortran_compiler = None
        self.preferred_c_compiler = None
        self.fortran_compiler = None
        self.fortran_ld_library_path = None
        self.fortran_flags = None
        self.c_compiler = None
        self.c_ld_library_path = None
        self.c_flags = None
        _build.initialize_options(self)
        #  #]
    #def run(self):
        #  #[ modified run (for debugging only)
        # some test prints:
        #print "build: self.user_options = ", self.user_options
        #print "build: self.preferred_fortran_compiler = ",\
        #      self.preferred_fortran_compiler
        #print "build: self.preferred_c_compiler = ",\
        #      self.preferred_c_compiler

        # call the run command of the default build
        #_build.run(self)
        #  #]
    #  #]

# modify the build_ext class to allow some custom commandline
# and setup.cfg options to the build_ext stage
class BuildExt(_build_ext):
    #  #[
    """Specialized Python extension builder."""
    # implement whatever needs to be different...
    # see the original build_ext.py in:
    #    /usr/lib64/python2.6/distutils/command/build_ext.py
    # see also the instructions in:
    #    http://docs.python.org/distutils/extending.html

    # todo: see if I can modify any of the compiler classes
    # like /usr/lib64/python2.6/distutils/*compiler.py
    # to handle fortran as well

    user_options = _build_ext.user_options
    user_options.append(("preferred-fortran-compiler", None,
                         "name of fortran compiler to be used"))
    user_options.append(("preferred-c-compiler", None,
                         "name of c compiler to be used"))
    user_options.append(("fortran-compiler", None,
                         "name and full path of fortran compiler to be used"))
    user_options.append(("fortran-ld-library-path", None,
                         "path in which shared objects can be found that "+\
                         "are needed by the choosen fortran compiler"))
    user_options.append(("fortran-flags", None,
                         "flags to be passed to the fortran compiler"))
    user_options.append(("c-compiler", None,
                         "name and full path of c compiler to be used"))
    user_options.append(("c-ld-library-path", None,
                         "path in which shared objects can be found that "+\
                         "are needed by the choosen c compiler"))
    user_options.append(("c-flags", None,
                         "flags to be passed to the c compiler"))
    def initialize_options(self):
        #  #[ initialise the additional options 
        """ initialise custom defined options """
        self.preferred_fortran_compiler = None
        self.preferred_c_compiler = None
        self.fortran_compiler = None
        self.fortran_ld_library_path = None
        self.fortran_flags = None
        self.c_compiler = None
        self.c_ld_library_path = None
        self.c_flags = None
        _build_ext.initialize_options(self)
        #  #]
    def finalize_options (self):
        #  #[ make settings available
        """ copy user defined options from the build to the
        build_ext class instance """
        # this copies the user_options from the build
        # to the build_ext class, so I'll have to modify
        # the build class as well to allow new options
        self.set_undefined_options('build',
                                   ('preferred_fortran_compiler',
                                    'preferred_fortran_compiler'),
                                   ('preferred_c_compiler',
                                    'preferred_c_compiler'),
                                   ('fortran_compiler',
                                    'fortran_compiler'),
                                   ('fortran_ld_library_path',
                                    'fortran_ld_library_path'),
                                   ('fortran_flags',
                                    'fortran_flags'),
                                   ('c_compiler',
                                    'c_compiler'),
                                   ('c_ld_library_path',
                                    'c_ld_library_path'),
                                   ('c_flags',
                                    'c_flags')
                                   )
        _build_ext.finalize_options(self)
        #  #]
    #def run(self):
        #  #[ modified run (for debugging only)
        # (actually I dont know how to build fortran this way,
        #  so I'll use my own build script here in stead
        #  _build_ext.run(self)  )

        # test prints
        #print "python executable: ", sys.executable
        #print "build_ext: self.user_options = ", self.user_options
        #print "build_ext: self.preferred_fortran_compiler = ",\
        #      self.preferred_fortran_compiler
        #print "build_ext: self.preferred_c_compiler = ",\
        #      self.preferred_c_compiler
        #print "build_ext: self.fortran_compiler = ",\
        #      self.fortran_compiler
        #print "build_ext: self.fortran_ld_library_path = ",\
        #      self.fortran_ld_library_path
        #print "build_ext: self.fortran_flags = ",\
        #      self.fortran_flags
        #print "build_ext: self.c_compiler = ",\
        #      self.c_compiler
        #print "build_ext: self.c_ld_library_path = ",\
        #      self.c_ld_library_path
        #print "build_ext: self.c_flags = ",\
        #      self.c_flags

        # this run command in turn runs the build_extension method
        #_build_ext.run(self) 
        #  #]
    def build_extension(self, ext):
        #  #[ the actual build
        """ initiate building the extension module """
        self.preferred_fortran_compiler = None
        self.preferred_c_compiler = None
        self.fortran_compiler = None
        self.fortran_ld_library_path = None
        self.fortran_flags = None
        self.c_compiler = None
        self.c_ld_library_path = None
        self.c_flags = None
        #fullname = self.get_ext_fullname(ext.name)
        #print "trying to build extension: ", fullname
        log.info("building '%s' extension", ext.name)

        #print "ext.sources = ", ext.sources

        # this does not work properly yet for setup.py bdist
        # since in that case the pybufr_ecmwf/ecmwfbufr.so
        # needs to be created below build/lib.linux-i686-2.6/
        # so inspect the path settings for the build:

        build_dir = os.path.join(self.build_lib, "pybufr_ecmwf")
        build_dir = os.path.abspath(build_dir)
        #print "self.build_lib = ", self.build_lib
        print "initiating build in dir: ", build_dir
        
        #if os.path.isdir(build_dir):
        #    sys.path.append(build_dir)
        if os.path.isdir(build_dir):
            sys.path.append(build_dir)
        else:
            raise DistutilsSetupError, \
                  ("could not find directory in which the module should"
                   "be build. Something seems wrong in setup.py."
                   "Please report this to the developer of this module.")

        # this enters the automatic build system, which is what I don't
        # want at the moment, since it seems not to handle fortran
        #_build_ext.build_extension(self, ext)

        cwd = os.getcwd()
        os.chdir(build_dir)

        #print "TESTJOS: sys.path = ", sys.path
        #print "TESTJOS: cwd = ", os.getcwd()
        
        from build_interface import InstallBUFRInterfaceECMWF
        # this will fail, because it loads the __init__.py inside
        # the pybufr_ecmwf directory, which in turn tries to load the
        # ecmwfbufr module, and that one does not yet exist, but will be
        # created by the ibi.build() call below.
        #from pybufr_ecmwf.build_interface import InstallBUFRInterfaceECMWF

        # run the build method from the InstallBUFRInterfaceECMWF class
        # defined in the custom build script, to build the extension module
        ibi = InstallBUFRInterfaceECMWF(verbose = True,
                                        preferred_fortran_compiler = \
                                        self.preferred_fortran_compiler,
                                        preferred_c_compiler = \
                                        self.preferred_c_compiler,
                                        fortran_compiler = \
                                        self.fortran_compiler,
                                        fortran_ld_library_path = \
                                        self.fortran_ld_library_path,
                                        fortran_flags = self.fortran_flags,
                                        c_compiler = self.c_compiler,
                                        c_ld_library_path = \
                                        self.c_ld_library_path,
                                        c_flags = self.c_flags,
                                        debug_f2py_c_api = False)
        
        # Build ecmwfbufr.so interface
        ibi.build()   

        # remove all object files to prevent them from ending up
        # in the binary or rpm distribution packages
        ibi.clean()
        
        os.chdir(cwd)

        #print "self.distribution.dist_files = ", self.distribution.dist_files
        #print "self.extensions[0].name = ", self.extensions[0].name
        #print "dir(self.extensions[0]) = ", dir(self.extensions[0])
        #sys.exit(1)
        #  #]
    #  #]

# enable the disabled pylint warnings again
#pylint: enable-msg=W0201,R0902,R0904

DESCR = "a python interface around the ECMWF-BUFR library."
LONG_DESCR = """a python interface around the Fortran90 ECMWF-BUFR library
constructed using the f2py interface generation tool.
For now only the equivalent subroutines to the ones in the ECMWF-BUFR
library are made available to python. In a next stage the plan is to
create also a more object-oriented/pythonic interface.
Building the interface is still a bit rough, and my require some
editing to choose the correct fortran and c-compiler.
Examples can be found in the file pybufr_ecmwf/pybufr_ecmwf.py
directly after the line: Starting test program:
"""

# define the list of classifiers
CL = ["Development Status :: Alpha",
      "Environment :: Console"
      "Intended Audience :: Developers"
      "Intended Audience :: System Administrators"
      "Operating System :: POSIX"
      ]

# passing a python file to do the build does not work, it gives this error:
# error: unknown file type '.py' (from 'pybufr_ecmwf/build_interface.py')
ECMWF_BUFR_EXT = Extension('pybufr_ecmwf.ecmwfbufr',
                           ["pybufr_ecmwf/build_interface.py"])
#ECMWF_BUFR_EXT = Extension('pybufr_ecmwf.ecmwfbufr', [])

setup(cmdclass = {'build'    : Build,
                  'build_ext': BuildExt},
      name = 'pybufr-ecmwf',
      version = '0.1',
      description = DESCR,
      long_description = LONG_DESCR,
      author = 'Jos de Kloe',
      author_email = 'josdekloe@gmail.com',
      url = 'http://code.google.com/p/pybufr-ecmwf/',
      download_url = "http://code.google.com/p/pybufr-ecmwf/source/checkout",
      classifiers = CL,
      platforms = ["POSIX"],
      license = "GPLv2",
      packages = ['pybufr_ecmwf'],
      ext_modules = [ECMWF_BUFR_EXT],
      requires = ["numpy", "numpy.f2py", "subprocess"]
      # this requires use of the setup tools which needs to be installed
      # first (i.e. it makes the setup a little bit less portable)
      # see: http://peak.telecommunity.com/DevCenter/setuptools#test
      #test_suite = "pybufr_ecmwf.tests.run_unit_tests"
      )

#  #[ usage examples for setup.py:

# (see: http://docs.python.org/distutils/introduction.html)
# possible uses of this setup script:

# see: http://docs.python.org/distutils/sourcedist.html
# for more details on sdist commands.

# create a source distribution tar file: [works]
# ==>python setup.py sdist
# this creates a tarfile:  dist/pybufr-ecmwf-0.1.tar.gz
# and a MANIFEST file with a listing of all included files

# compile only the extension module pybufr_ecmwf/ecmwfbufr.so: [works]
# ==>python setup.py build_ext

# only recreate the MANIFEST file [works]
# python setup.py sdist --manifest-only

# see: http://docs.python.org/distutils/builtdist.html
# for more details on bdist commands.

# creation of a binary distribution tgz file: [works]
# ==>python setup.py bdist

# creation of an rpm file: [works!]
# ==>python setup.py bdist_rpm
# NOTE: for a locally installed python version the command should be:
# python2.6 ./setup.py bdist_rpm --python python2.6
# but this fails due to some path problem on my KNMI machine:
#  File not found: /nobackup/users/kloedej/temp_mercurial_repos/\
#     pybufr_ecmwf_copy/build/bdist.linux-i686/rpm/BUILD/pybufr-ecmwf-root/\
#     nobackup/users/kloedej/software_installed/scipy_numpy/lib/python2.6/\
#     site-packages/pybufr_ecmwf/ecmwfbufr.so

# build by an end user
# ==>python setup.py build

# installation by an end-user
# ==>python setup.py install

#  #]
