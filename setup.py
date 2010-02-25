#!/usr/bin/env python
import os
import sys
from distutils.core import setup #, Extension

import pybufr_ecmwf

sys.exit(0)

setup(name='pybufr-ecmwf',
      version='0.1',
      description='Python wrapper around the ECMWF BUFR library',
      author='Jos de Kloe',
      author_email='josdekloe@gmail.com',
      url='http://code.google.com/p/pybufr-ecmwf/',
      py_modules=['pybufr_ecmwf.py','bufr.py'],
      )
#packages = ['pybufr-ecmwf'])
#,
#ext_modules = [ ecmwfbufr, ]
#)

# (see: http://docs.python.org/distutils/introduction.html)
# possible uses of this setup script:
#create a source distribution tar file:
#==>python setup.py sdist
#installation by an end-user
#==>python setup.py install
#creation of an rpm file
#==>python setup.py bdist_rpm
