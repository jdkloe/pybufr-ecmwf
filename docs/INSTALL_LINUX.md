## Installation on Linux machines

To install the pybufr-ecmwf python module you have several options:

First install the needed dependencies:
* the python module numpy, and its f2py tool
  (for some linux distributions they are in separate packages,
   for example
   Fedora splits them in python2-numpy and python2-numpy-f2py)
* the presence of a Fortran compiler (gfortran from the gcc compiler 
  collection is recommended)
* the presence of a c-compiler (gcc is recommened)
* note that the c-comppiler MUST BE identical to the one that was
  used to compile the python interpreter, otherwise it will not work

Then choose one of these:

## Use pip

The easiest method is using pip.
Use this command to install using pip for python2:
```bash
pip install pybufr-ecmwf
```
or this command to install using pip for python3:
```bash
pip3 install pybufr-ecmwf
```

This will download and install the latest release version
from pypi and compiles and installs it for you.
(see https://pypi.python.org/pypi/pybufr-ecmwf/)

You can use options like --user to install in your own
user account, or --prefix to relocate the module.
To get a list of all options issue:
```
pip install --help
```

## Use virtualenv and pip

Virtualenv is a very nice little tool that allows you to do a test
installation, without affecting your normal python environment.
After finishing your test, it is easy to delete the test directory with
all its contents, and your normal python setup should be unchanged.
Use these commands to install it in this way:
```bash
virtualenv myenv --system-site-packages
. myenv/bin/activate
pip install pybufr-ecmwf
```
If you prefer csh above bash, activate virtualenv with:
```csh
source myenv/bin/activate.csh
```

and clean up afterwards with:
```
deactivate
rm -rf myenv
```

## Manually download and install the latest tarball:

* visit https://pypi.python.org/pypi/pybufr-ecmwf/
  and download the latest software version.
  Then unpack the software.
  This will get you the latest released version.
```bash
tar zxvf pybufr-ecmwf-$VERSION.tar.gz
cd pybufr-ecmwf-$VERSION
```
* OR visit https://github.com/jdkloe/pybufr-ecmwf
  then use the "Clone or Download" button button,
  and then the "Download ZIP" button to do the actual download.
  Finally unpack the software.
  This will get you the latest development version.
```bash
unzip pybufr-ecmwf-master.tar.gz
cd pybufr-ecmwf-master
```
* then build, test and install the software using:
```bash
python2 setup.py build
python2 unittest.py
sudo python2 setup.py install
```
* for a local install in an unprivileged user account use:
```bash
python2 setup.py install --user
```
* for an install in a non-default location, for example a network
  disk, so other users in your network can use the module as well, use:
```bash
python2 setup.py install --prefix=/some/dir
```

For installation of the python3 version simply replace
all python2 commands by python3.

WARNING for python3 users:
the f2py tool that comes with numpy was broken, and crashed during 
the build process.
The problem has been reported to the numpy developers (see
http://projects.scipy.org/numpy/ticket/1932 and
https://github.com/numpy/numpy/pull/3230), and the bug was fixed
in may 2013. However, if your numpy version is older than that this 
may still be a problem.

## Check out this mercurial repository and run setup.py:

Also this will get you the latest development version.
This method assumes you have the git tool installed

```bash
git clone https://github.com/jdkloe/pybufr-ecmwf.git
cd pybufr-ecmwf
```
then continue with the instructions given above for
"Manually download and install the latest tarball".

## Customised builds

Explanations about some non-standard options can be found in
the setup.cfg file, where things like which fortran compiler to use for
building the interface can be choosen.
Use 'setup.py build --help' to get a list of all possibilities.

For manual building outside the setup.py script you can manually execute 
the build_interface.py script. This is mainly intended for testing
and debugging purposes.

For manual testing after you have build the software
go to the software root and execute the run_example_program.sh script.

## Advanced options

It is possible to manually download a different version of the
bufrdc library from ECMWF and have the pybufr-ecmwf module use it.
To do this, copy the tarball of the bufrdc source code
into the pybufr_ecmwf/ecmwf_bufr_lib/ directory before starting
the build stage (and remove possible other tar files that may be located
in that directory).

Please note that the bufrdc library needs to be compiled using
the -fPIC option to both the gfortran and gcc compilers
to generate position independent code.
This is needed to allow linking the library into a shared object file,
which in turn is needed to create a binary python module on linux.
For this reason using a pre-installed bufrdc version on your
machine will probably not work, since the default bufrdc build
system does not apply the -fPIC option.
The build stage of the pybufr-ecmwf module therefore contains its
own build of the bufrdc library, and takes care of this.

## Packaged versions

The following pre-packaged version is available:

Christoph Paulik provides a conda package:
* https://anaconda.org/cpaulik/pybufr-ecmwf

If you also wish to package this software please drop me a note
and I'll work with you to make this as easy as possible.

## Final remarks

Note that this module has been developed using Fedora Linux and will
probably compile and run on any modern Linux distribution.
It has been tested and works well on MacOSX.
See 
It may run on Unix or BSD as well, but has not been tested there yet
(if you have tried this, please let me know).

Jos de Kloe, 18-Aug-2016.
