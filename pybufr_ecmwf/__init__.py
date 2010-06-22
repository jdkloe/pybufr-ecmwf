"""A module to allow access (read/write/composing) to the
BUFR format as defined by the WMO, by interfacing to the
Fortran BUFR library made available by ECMWF.

Author:  J. de Kloe, KNMI
Created: 04-Feb-2010
"""

# explicit imports seem not needed at the moment

from pybufr_ecmwf import *
import bufr
import helpers

# allow this one to fail, because I wish to use the helpers.py functionality
# from the port_2to3.py script, which may be used before doing the actual
# build of ecmwfbufr.so
try:
    import ecmwfbufr
except ImportError:
    pass
