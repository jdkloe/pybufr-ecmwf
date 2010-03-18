#!/usr/bin/env python

# NOTE: for debugging of this setup.py script
# set the DISTUTILS_DEBUG environment variable to TRUE
# (or any other non-empty string)

import os
import sys
from distutils.core import setup, Extension
# import build_ext using a different name,
# to allow subclassing it
from distutils.command.build_ext import build_ext as _build_ext

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
from sys import version
if version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

class build_ext(_build_ext):
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

    def initialize_options(self):
        # initialise the additional options 
        self.preferred_fortran_compiler = None
        self.preferred_c_compiler = None
        _build_ext.initialize_options(self)

    def finalize_options (self):
        # this copies the user_options from the build
        # to the build_ext class, so I'll have to modify
        # the build class as well to allow new options
        self.set_undefined_options('build',
                                   ('preferred_fortran_compiler', 'preferred_fortran_compiler'),
                                   ('preferred_c_compiler', 'preferred_c_compiler'),
                                   )
        _build_ext.finalize_options(self)
        
    def run(self):
        # call the run command of the default build_py
        # (actually I dont know how to build fortran this way,
        #  so I'll use my own build script here in stead
        #_build_ext.run(self)

        # for now, this import triggers the build of the ecmwfbufr.so
        # shared-object file needed by this module
        import pybufr_ecmwf

        print "self.user_options = ",self.user_options
        print "self.preferred_fortran_compiler = ",\
              self.preferred_fortran_compiler
        print "self.preferred_c_compiler = ",\
              self.preferred_c_compiler
        
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
      "Operating System :: POSIX",
      ""]

Ext=Extension('pybufr_ecmwf.ecmwfbufr',[])

setup(cmdclass={'build_ext': build_ext},
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

# creation of an rpm file: [works]
# ==>python setup.py bdist_rpm

# build by an end user
# ==>python setup.py build

# installation by an end-user
# ==>python setup.py install

