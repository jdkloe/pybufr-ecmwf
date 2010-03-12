#!/usr/bin/env python
import os
import sys
from distutils.core import setup #, Extension

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

#Ext=Extension('ecmwfbufr',[''])

setup(name='pybufr-ecmwf',
      version='0.1',
      description='Python wrapper around the ECMWF BUFR library',
      long_description=long_descr,
      author='Jos de Kloe',
      author_email='josdekloe@gmail.com',
      url='http://code.google.com/p/pybufr-ecmwf/',
      platforms=["POSIX"],
      license="GPLv2",
      packages=['pybufr_ecmwf'],
      scripts=['clean.py',
               'pybufr_ecmwf/example_programs/example_for_using_ecmwfbufr_for_decoding.py'],
      package_data={'pybufr_ecmwf':['ecmwf_bufrtables/*.TXT','testdata/*.BUFR']}
      )
#packages = ['pybufr-ecmwf'])
#,
#ext_modules = [ ecmwfbufr, ]
#)

# (see: http://docs.python.org/distutils/introduction.html)
# possible uses of this setup script:

#create a source distribution tar file:
#==>python setup.py sdist
# this creates a tarfile:  dist/pybufr-ecmwf-0.1.tar.gz
# and a MANIFEST file with a listing of all included files

#installation by an end-user
#==>python setup.py install
#creation of an rpm file
#==>python setup.py bdist_rpm
