"""A module to allow access (read/write/composing) to the
BUFR format as defined by the WMO, by interfacing to the
Fortran BUFR library made available by ECMWF.

Author:  J. de Kloe, KNMI
Created: 04-Feb-2010
"""

#__all__ = ['bufr_template',
#           'raw_bufr_file',
#           'bufr_interface_ecmwf',
#           'bufr',
#           'helpers']

try:
    import pybufr_ecmwf.ecmwfbufr
except ImportError as imperr:
    print "===="
    print "Sorry, this module needs to be build before you can use it !"
    print "===="
    raise imperr

from pybufr_ecmwf.bufr_template import *
from pybufr_ecmwf.raw_bufr_file import *
from pybufr_ecmwf.bufr_interface_ecmwf import *
from pybufr_ecmwf.bufr import *

