# pybufr_ecmwf

## Introduction

BUFR is the World Meteorological Organization (WMO) standard
file format for the exchange of weather observations.
Pybufr_ecmwf is a python module for reading and of writing BUFR files
and for composing BUFR templates.

The pybufr_ecmwf module provides a python interface to the ECMWF bufrdc
library and allows to read and write files in BUFR format.
On top of the functionality provided by the bufrdc fortran library,
this python module also adds the possibility to create BUFR templates
and write the results as BUFR tables that can be used by the
ECMWF BUFRDC library

The API consists of several layers:
* the raw/bare fortran/c API that connects python to the fortran library
  (pybufr_ecmwf.ecmwfbufr)

* an intermediate python API around this raw layer
  (pybufr_ecmwf.bufr_interface_ecmwf)
  
* a high level API which allows a pythonic object 
  oriented usage. (pybufr_ecmwf.bufr)
  (for now, only for reading of BUFR files,
   for writing and template creation the intermediate layer is still needed.)

It is recommended to only use the high level API whenever possible,
This should be the easiest interface to use.
Also, ECMWF is in the middle of a transition to a new library
called ecCodes (which is currently in beta stage).
The plan is to include an interface to this new library as well in this
python module, with identical high level python interface, so you don't
need to adapt your scripts.
However, to enable this the lower level python routines
may change significantly.

Also please note that this new ecCodes library implements its own
python API which is significantly different from the interface
implemented by the pybufr_ecmwf module.
Details can be found on the ECMWF website:
https://software.ecmwf.int/wiki/display/ECC/ecCodes+Home

## Requirements

* python 3.x

* numpy (and its f2py component)
  (note that on linux they may be packaged separately, for example
   Fedora splits them in python3-numpy and python3-numpy-f2py)

* gcc and gfortran

## Compatibility

This module should work and has CI tests on
[travis](https://travis-ci.org/jdkloe/pybufr-ecmwf) for:

* linux (any recent version should work)

* Mac OSX + homebrew

If you manage to get it working on other types of systems please tell me.

## Installation

Installation details are given in these files:
* for Linux see:   [docs/INSTALL_LINUX.md](docs/INSTALL_LINUX.md)
* for MacOSX see:  [docs/INSTALL_MACOSX.md](docs/INSTALL_MACOSX.md)

Unfortunately Windows is currently not supported.
For details why see: [docs/NOTES_WINDOWS.md](docs/NOTES_WINDOWS.md)

## Documentation

For usage examples for pybufr_ecmwf see the file [docs/USAGE.md](docs/USAGE.md)

For more information on this module please consult the documentation at:
... [to be written]

Some details on how to start testing with the optional
ecCodes interface can be found here ... [to be written]

The World Meteorological Organization (WMO) has a set of webpages
describing the meteorological codes:
http://www.wmo.int/pages/prog/www/WMOCodes.html

The file format standard is described in the official WMO documentation
which can be downloaded from:
http://www.wmo.int/pages/prog/www/WMOCodes/Guides/BUFRCREXPreface_en.html
A direct link to the file format standard is in pdf format:
http://www.wmo.int/pages/prog/www/WMOCodes/Guides/BUFRCREX/Layer3-English-only.pdf

The ECMWF BUFRDC library documentation is available at the ECMWF website at
https://software.ecmwf.int/wiki/display/BUFR/BUFRDC+Home
A link to the bufr_user_guide.pdf document is available on this page.

The new ecCodes library can be downloaded from the ECMWF website:
https://software.ecmwf.int/wiki/display/ECC/ecCodes+Home

## Copyright

The python source code for this module
is copyright (c) 2009-2022 by Jos de Kloe
and placed under the LGPLv3 license.
The included unaltered copy of the ECMWF bufrdc library source code
is copyright (c) 1981-2016 ECMWF and is Apache v2.0 licensed.

## Contact

Questions, issues and requests for new features can be posted
on the issues page: https://github.com/jdkloe/pybufr-ecmwf/issues
or directly emailed to me at josdekloe@gmail.com

Jos de Kloe, 20-May-2022.
