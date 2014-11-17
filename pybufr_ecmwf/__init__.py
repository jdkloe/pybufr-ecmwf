"""A module to allow access (read/write/composing) to the
BUFR format as defined by the WMO, by interfacing to the
Fortran BUFR library made available by ECMWF.

Author:  J. de Kloe, KNMI
Created: 04-Feb-2010
"""

# I can't get this to work properly, so skip this for now.
# if anyone knows how to do this, please drop me a note.

## ensure version details are easy to find
## but allow these imports to fail as well, since the version.py file
## is a generated file, and noy yet available when the build_interface.py
## script is launched (which also needs to import some items from the
## pybufr_ecmwf module dir, especially the helpers.py file)
#
#try:
#    from .version import version as __version__
#    from .version import hg_version, install_date, software_version
#except:
#    # print 'not imported version info'
#    pass


#__all__ = ['bufr_template',
#           'raw_bufr_file',
#           'bufr_interface_ecmwf',
#           'bufr',
#           'helpers']

#try:
#    import pybufr_ecmwf.ecmwfbufr
#except ImportError as imperr:
#    print "===="
#    print "Sorry, this module needs to be build before you can use it !"
#    print "===="
#    raise imperr

#from pybufr_ecmwf.bufr_template import *
#from pybufr_ecmwf.raw_bufr_file import *
#from pybufr_ecmwf.bufr_interface_ecmwf import *
#from pybufr_ecmwf.bufr import *

