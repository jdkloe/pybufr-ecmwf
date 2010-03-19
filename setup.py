#!/usr/bin/env python

# NOTE: for debugging of this setup.py script
# set the DISTUTILS_DEBUG environment variable to TRUE
# (or any other non-empty string)

#  #[ imported modules
import os
import sys
from distutils.core import setup, Extension
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

# modify the build class to allow some custom commandline
# and setup.cfg options to the build stage
class build(_build):
    #  #[
    """Adapted Python binary builder."""
    user_options = _build.user_options
    user_options.append(("preferred-fortran-compiler",None,
                         "name of preferred fortran compiler to be used"))
    user_options.append(("preferred-c-compiler",None,
                         "name of preferred c compiler to be used"))
    user_options.append(("fortran-compiler",None,
                         "name and full path of fortran compiler to be used"))
    user_options.append(("fortran-ld-library-path",None,
                         "path in which shared objects can be found that "+\
                         "are needed by the choosen fortran compiler"))
    user_options.append(("fortran-flags",None,
                         "flags to be passed to the fortran compiler"))
    user_options.append(("c-compiler",None,
                         "name and full path of c compiler to be used"))
    user_options.append(("c-ld-library-path",None,
                         "path in which shared objects can be found that "+\
                         "are needed by the choosen c compiler"))
    user_options.append(("c-flags",None,
                         "flags to be passed to the c compiler"))

    def initialize_options(self):
        # initialise the additional options 
        self.preferred_fortran_compiler = None
        self.preferred_c_compiler = None
        self.fortran_compiler = None
        self.fortran_ld_library_path = None
        self.fortran_flags = None
        self.c_compiler = None
        self.c_ld_library_path = None
        self.c_flags = None
        _build.initialize_options(self)

    def run(self):
        # some test prints:
        #print "build: self.user_options = ",self.user_options
        #print "build: self.preferred_fortran_compiler = ",\
        #      self.preferred_fortran_compiler
        #print "build: self.preferred_c_compiler = ",\
        #      self.preferred_c_compiler

        # call the run command of the default build
        _build.run(self)
    #  #]

# modify the build_ext class to allow some custom commandline
# and setup.cfg options to the build_ext stage
class build_ext(_build_ext):
    #  #[
    """Specialized Python extension builder."""
    # implement whatever needs to be different...
    # see the original build_ext.py in:
    #    /usr/lib64/python2.6/distutils/command/build_ext.py
    # see also the instructions in:
    #    http://docs.python.org/distutils/extending.html

    user_options = _build_ext.user_options
    user_options.append(("preferred-fortran-compiler",None,
                         "name of fortran compiler to be used"))
    user_options.append(("preferred-c-compiler",None,
                         "name of c compiler to be used"))
    user_options.append(("fortran-compiler",None,
                         "name and full path of fortran compiler to be used"))
    user_options.append(("fortran-ld-library-path",None,
                         "path in which shared objects can be found that "+\
                         "are needed by the choosen fortran compiler"))
    user_options.append(("fortran-flags",None,
                         "flags to be passed to the fortran compiler"))
    user_options.append(("c-compiler",None,
                         "name and full path of c compiler to be used"))
    user_options.append(("c-ld-library-path",None,
                         "path in which shared objects can be found that "+\
                         "are needed by the choosen c compiler"))
    user_options.append(("c-flags",None,
                         "flags to be passed to the c compiler"))

    def initialize_options(self):
        # initialise the additional options 
        self.preferred_fortran_compiler = None
        self.preferred_c_compiler = None
        self.fortran_compiler = None
        self.fortran_ld_library_path = None
        self.fortran_flags = None
        self.c_compiler = None
        self.c_ld_library_path = None
        self.c_flags = None
        _build_ext.initialize_options(self)

    def finalize_options (self):
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
                                   ('c_compiler','c_compiler'),
                                   ('c_ld_library_path',
                                    'c_ld_library_path'),
                                   ('c_flags','c_flags')
                                   )
        _build_ext.finalize_options(self)
        
    def run(self):
        # call the run command of the default build_ext
        # (actually I dont know how to build fortran this way,
        #  so I'll use my own build script here in stead
        #  _build_ext.run(self)  )

        print "python executable: ",sys.executable

        # for now, this import triggers the build of the ecmwfbufr.so
        # shared-object file needed by this module
        import pybufr_ecmwf

        # test prints
        #print "build_ext: self.user_options = ",self.user_options
        print "build_ext: self.preferred_fortran_compiler = ",\
              self.preferred_fortran_compiler
        print "build_ext: self.preferred_c_compiler = ",\
              self.preferred_c_compiler
        print "build_ext: self.fortran_compiler = ",\
              self.fortran_compiler
        print "build_ext: self.fortran_ld_library_path = ",\
              self.fortran_ld_library_path
        print "build_ext: self.fortran_flags = ",\
              self.fortran_flags
        print "build_ext: self.c_compiler = ",\
              self.c_compiler
        print "build_ext: self.c_ld_library_path = ",\
              self.c_ld_library_path
        print "build_ext: self.c_flags = ",\
              self.c_flags
    #  #]
        
descr="a python interface around the ECMWF-BUFR library."
long_descr="""a python interface around the Fortran90 ECMWF-BUFR library
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
cl = ["Development Status :: Alpha",
      "Environment :: Console"
      "Intended Audience :: Developers"
      "Intended Audience :: System Administrators"
      "Operating System :: POSIX"
      ]

Ext=Extension('pybufr_ecmwf.ecmwfbufr',[])

setup(cmdclass={'build': build,
                'build_ext': build_ext},
      name='pybufr-ecmwf',
      version='0.1',
      description='Python wrapper around the ECMWF BUFR library',
      long_description=long_descr,
      author='Jos de Kloe',
      author_email='josdekloe@gmail.com',
      url='http://code.google.com/p/pybufr-ecmwf/',
      download_url="http://code.google.com/p/pybufr-ecmwf/source/checkout",
      classifiers=cl,
      platforms=["POSIX"],
      license="GPLv2",
      packages=['pybufr_ecmwf'],
      ext_modules=[Ext],
      requires=["numpy","numpy.f2py","subprocess"],
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
#  File not found: /nobackup/users/kloedej/temp_mercurial_repos/pybufr_ecmwf_copy/build/bdist.linux-i686/rpm/BUILD/pybufr-ecmwf-root/nobackup/users/kloedej/software_installed/scipy_numpy/lib/python2.6/site-packages/pybufr_ecmwf/ecmwfbufr.so

# build by an end user
# ==>python setup.py build

# installation by an end-user
# ==>python setup.py install

#  #]
