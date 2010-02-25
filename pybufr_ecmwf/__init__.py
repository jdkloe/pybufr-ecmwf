"""A module to allow access (read/write/composing) to the
BUFR format as defined by the WMO, by interfacing to the
Fortran BUFR library made available by ECMWF.

Author:  J. de Kloe, KNMI
Created: 04-Feb-2010
"""

from pybufr_ecmwf import *
from bufr import *

# the next ecmwfbufr include will only work after having initialised
# the class BUFRInterfaceECMWF defined in pybufr_ecmwf at least once,
# since that will automatically create the interface.
# Later some reorganisation is probably needed, especially
# if people wish to distribute this module.
# For my own use, instantiate the class to trigger the build here:

import os
cwd = os.getcwd()
if __name__ != "__main__":
    print "changing dir to: ",__name__
    os.chdir(__name__)
BI = BUFRInterfaceECMWF(verbose=True)
del(BI)
os.chdir(cwd)

from ecmwfbufr import *
