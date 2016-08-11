#pybufr_ecmwf

## Introduction

Python module for reading van writing BUFR files and composing BUFR templates.

BUFR is the World Meteorological Organization (WMO) standard
file format for the exchange of weather observations.

The pybufr_ecmwf module provides a python interface to the ECMWF bufrdc
library and allows to read and write files in 
BUFR format, and to create BUFR tables and templates.

The API consists of several layers:
* the raw/bare c API that connects python to the fortran library
  (pybufr_ecmwf.ecmwfbufr)

* an intermediate python API around this raw layer
  (pybufr_ecmwf.bufr_interface_ecmwf)
  
* a high level API which allows a pythonic object 
 oriented usage. (pybufr_ecmwf.bufr)
 (for now, only for reading of BUFR files,
  for writing the intermediate layer is still needed.)

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
the setup.cfg file, where things like which fortran compiler te use for
building the interface can be choosen.
Use 'setup.py --help' to get a list of all possibilities.

For manual building outside the setup.py script you can manually execute 
the build_interface.py script. This is mainly intended for testing
and debugging purposes.

For manual testing go to the software root (where this readme file in located)
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
