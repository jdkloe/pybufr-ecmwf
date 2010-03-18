#!/usr/bin/env python

# NOTE: for debugging of this setup.py script
# set the DISTUTILS_DEBUG environment variable to TRUE
# (or any other non-empty string)

import os
import sys
from distutils.core import setup, Extension

# patch distutils if it can't cope with the "classifiers" or
# "download_url" keywords
from sys import version
if version < '2.2.3':
    from distutils.dist import DistributionMetadata
    DistributionMetadata.classifiers = None
    DistributionMetadata.download_url = None

# for now, this import triggers the build of the ecmwfbufr.so
# shared-object file needed by this module
# (an ugly hack, I know, it will be cleaned as soon as I have figured
#  out how to do this properly from this setup.py script)
import pybufr_ecmwf

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

setup(name='pybufr-ecmwf',
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

# create a source distribution tar file:
# ==>python setup.py sdist
# this creates a tarfile:  dist/pybufr-ecmwf-0.1.tar.gz
# and a MANIFEST file with a listing of all included files

# compile the extension module pybufr_ecmwf/ecmwfbufr.so like this:
# ==>python setup.py build_ext

# build by an end user
# ==>python setup.py build

# installation by an end-user
# ==>python setup.py install

# creation of an rpm file
# ==>python setup.py bdist_rpm
# NOTE: this actually seems to work already!
# it does create rpm's that do contain the correct python files
# and builds the needed ecmwfbufr.so files, and packs that one as well ...
