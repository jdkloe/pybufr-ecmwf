#!/usr/bin/env python
import os
import sys
from distutils.core import setup #, Extension

# for now, this import triggers the build of the ecmwfbufr.so
# shared-object file needed by this module
# (an ugly hack, I know, it will be cleaned as soon as I have figured
#  out how to do this properly from this setup.py script)
import pybufr_ecmwf

setup(name='pybufr-ecmwf',
      version='0.1',
      description='Python wrapper around the ECMWF BUFR library',
      author='Jos de Kloe',
      author_email='josdekloe@gmail.com',
      url='http://code.google.com/p/pybufr-ecmwf/',
      packages=['pybufr_ecmwf'],
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
