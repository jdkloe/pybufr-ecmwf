#pybufr_ecmwf

## Introduction

BUFR is the World Meteorological Organization (WMO) standard
file format for the exchange of weather observations.
Pybufr_ecmwf is a python module for reading and of writing BUFR files
and for composing BUFR templates.

The pybufr_ecmwf module provides a python interface to the ECMWF bufrdc
library and allows to read and write files in BUFR format.
This python module adds the possibility to create BUFR templates
and write the results as BUFR tables that can be used by the
ECMWF BUFRDC library.

The API consists of several layers:
* the raw/bare c API that connects python to the fortran library
  (pybufr_ecmwf.ecmwfbufr)

* an intermediate python API around this raw layer
  (pybufr_ecmwf.bufr_interface_ecmwf)
  
* a high level API which allows a pythonic object 
 oriented usage. (pybufr_ecmwf.bufr)
 (for now, only for reading of BUFR files,
  for writing the intermediate layer is still needed.)

It is recommended to only use the high level API whenever possible,
This should be the easiest interface to use.
Also, ECMWF is in the middle of a transition to a new library
called ecCodes (which is currently in beta stage).
The plan is to include an interface to this new library as well in this
python model, with identical high level python interface, so you don't
need to adapt your scripts.
However, the lower level python routines may change significantly,
to enable this.
Also please note that this new ecCodes library implements its own
python API which is significantly different from the interface
implemented by the pybufr_ecmwf module.
Details can be found on the ECMWF website:
https://software.ecmwf.int/wiki/display/ECC/ecCodes+Home

## Requirements

* python 2.6 or above

* numpy (and its f2py component)

* gcc and gfortran

## Installation

For building and installation use the setup.py script.
The usual invocation should work:

### for python2 users:
```
python2 setup.py build
python2 unittest.py
python2 setup.py install --user
```
or
```
python2 setup.py build
python2 unittest.py
sudo python2 setup.py install
```
### for python3 users:
```
python3 setup.py build
python3 unittest.py
python3 setup.py install --user
```
or
```
python3 setup.py build
python3 unittest.py
sudo python3 setup.py install
```

Explanations about some non-standard options can be found in
the setup.cfg file, where things like which fortran compiler to use for
building the interface can be choosen.
Use 'setup.py --help' to get a list of all possibilities.

For manual building outside the setup.py script you can manually execute 
the build_interface.py script. This is mainly intended for testing
and debugging purposes.

For manual testing go to the software root (where this readme file is located)
and execute the run_example_program.sh script.

WARNING for python3 users:
the f2py tool that comes with numpy was broken, and crashed during 
the build process.
The problem has been reported to the numpy developers (see
http://projects.scipy.org/numpy/ticket/1932 and
https://github.com/numpy/numpy/pull/3230), and the bug was fixed
in may 2013. However, if your numpy version is older than that this 
may still be a problem.

## Documentation

For examples on its usage see the file USAGE.txt

For more information on this module please consult the documentation at:
... [to be written]

The World Meteorological Organization (WMO) has a set of webpages
describing the meteorological codes:
http://www.wmo.int/pages/prog/www/WMOCodes.html

The file format standard is described in the official WMO documentation
which can be downloaded from:
http://www.wmo.int/pages/prog/www/WMOCodes/Guides/BUFRCREXPreface_en.html
A direct link to the file format standard is:
http://www.wmo.int/pages/prog/www/WMOCodes/Guides/BUFRCREX/Layer3-English-only.pdf

The ECMWF BUFRDC library documentation is available an the ECMWF website at
https://software.ecmwf.int/wiki/display/BUFR/BUFRDC+Home
A link to the bufr_user_guide.pdf document is available on this page.

The new 
## Copyright

The python source code for this module
is copyright (c) 2009-2016 by Jos de Kloe
and placed under the LGPLv3 license.
The included unaltered copy of the ECMWF bufrdc library source code
is copyright (c) 1981-2016 ECMWF and is Apache v2.0 licensed.

## Contact

Questions, issues and requests for new features can be posted
on the issues page: https://github.com/jdkloe/pybufr-ecmwf/issues
or directly emailed to me at josdekloe@gmail.com

Jos de Kloe, 11-Aug-2016.
