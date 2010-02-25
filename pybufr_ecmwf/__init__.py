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

# these lines are temporarily here to auto-build the module when I test
# them. As soon as I have the setup.py script working they will be removed.
cwd = os.getcwd()
if __name__ != "__main__":
    try:
        builddir = __name__
        os.chdir(builddir)
    except:
        try:
            builddir = os.path.join('..',__name__)
            os.chdir(builddir)
        except:
            builddir = os.path.join('..','..',__name__)
            os.chdir(builddir)
            
BI = BUFRInterfaceECMWF(verbose=True)
del(BI)
os.chdir(cwd)

import ecmwfbufr

