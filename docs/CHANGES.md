upcoming release:
-move to library version bufrdc_000409
-make all code portable between python2 and python3 to remove the
 need to run the 2to3 tool
-introduce travis testing for linux and MacOSX+Homebrew
-addition of a simple read interface in BUFRReader
 (thanks to Christoph Paulik)
-reorganize documentation files
-addition of a first few lines to start building an interface
 to the new ECMWF ecCodes library

Release 0.81 (19-Feb-2015)
-license change to LGPLv3
-move to library version bufrdc_000403
-split download tool to its own file

Release 0.80 (13-Nov-2014)
-do no longer download the latest library version from ECMWF, to prevent
 breakage in case they redesign their website or software package,
 just use the packed tar file (the option to download can still be used though)
-updated to build and use the new BUFRDC series of the ECMWF library
 including the latest versions 000400 and  000401.
-add reading, writing and using the C-BUFR tables which allows expanding
 numerical flag values to the corresponding text values.
-fix a bug that happens if multiple bufr files using different templates
 from different bufr table files are used in the same script.
-fase out the singletom trick since it made things too complicated
 (and was only experimnental anyway)

Release 0.73 (08-Dec-2013)
-fix pip install issue and add pip install test to build_test.py 
-fix a whole bunch of new pylint warnings
 (since pylint now also complains about whitespace)

Release 0.72 (14-May-2013):
-add a safety check to bufr_to_ascii.py and add a little sorting script
 named sort_bufr_msgs.py, to prevent trouble in case bufr_to_ascii.py is
 used on a file that contains mixed BUFR messages using different templates

Release 0.71 (14-May-2013):
-fix a mistake in the manifest file

Release 0.7 (May-2013):
-fix a few python3 compatibility issues
-fix issue 4 (warning on max bufr message size had wrong threshold)
-add a simple example program to request a name for a descriptor number
-make bufr table copying code more efficient

Release 0.6 (May-2013):
-move to ECMWF BUFR version bufrdc_000400
-reorganise custom fortran code added to the ECMWF library 
 to allow easier interfacing by this module
-split test data from example_programs dir, and move to separate test dir
-fix a number of python3 compatibility issues

Release 0.5 (25-Sep-2012):

Contains mainly small bug fixes and updates the build script to the 
latest library version.

Release 0.4 (06-Sep-2011):

Several fixes have been added in the handling of the BUFR tables, which
now should also work if you provide custom BUFR table names or a custom
BUFR tables directory (as parameter or through the BUFR_TABLES environment
setting) to the module.
In addition functionality to create new BUFR tables from scratch has been
added, including an example script to demonstrate this.

Release 0.3 (22-Apr-2011):

The top level interface for reading a BUFR message is in place now.
Still the code only works properly when you use the BUFR tables
provided by the ECMWF BUFR library.
Compilation with python3 seems to have some difficulties.
The dependency on numpy is no problem anymore, since that one is now
fully ported to python3, but the f2py tool that comes with numpy
seems broken somehow, and crashes during the build process.
The problem has been reported to the numpy developers (see
http://projects.scipy.org/numpy/ticket/1932), so for the moment
I'll wait for a bugfix from the numpy team before continuing
the python3 porting effort.

Release 0.2 (21-Oct-2010):

A next wrapper interface is in place now, and a start for the top-level
interface is implemented.
Also, the module can now be converted and compiled using python3.

Release 0.1 (10-Jun-2010):

A first rough test version of this module. The f2py wrapper generation and 
compilation works for me.
Decoding and encoding of BUFR messages already is possible with this
version, if you know what you are doing.
Today I submitted this version to the pypi index, see:
http://pypi.python.org/pypi/pybufr-ecmwf/0.1
so hopefully I will get some feedback on the functioning and coding 
of this module.
Don't hesitate to contact me if you have any questions or remarks!

---
Jos de Kloe.
---
