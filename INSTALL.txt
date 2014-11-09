To install the pybufr-ecmwf python module you have several options:

First install the needed dependencies:
* the python module numpy, and its f2py tool
  (for some linux distributions they are in separate packages)
* the presence of a Fortran compiler (gfortran from the gcc compiler 
  collection is recommended)
* the presence of a c-compiler (gcc is recommened)

Then choose one of these:

1) Download and install the latest tarball:
   -visit https://code.google.com/p/pybufr-ecmwf/
    and download the latest software version
   -unpack the software: tar zxvf pybufr-ecmwf-$VERSION.tar.gz
   -cd pybufr-ecmwf-$VERSION
   -python setup.py build
   -[local install:]       python setup.py install --user
   -[system wide install:] python setup.py install

  A copy of a recent ECMWF BUFR library source tar file is provided with
  the software and will be used by the build stage.
  If you know an update is available from the ECMWF website
  you could try to run this build command in stead of the above one:
   -python setup.py build --download-library-sources=true

2) Use virtualenv and pip
   -virtualenv myenv --system-site-packages
   -[bash] source myenv/bin/activate
   -[csh] source myenv/bin/activate.csh
   -pip install pybufr-ecmwf

3) Check out this mercurial repository and run setup.py:
   -hg clone https://code.google.com/p/pybufr-ecmwf/
   -cd pybufr-ecmwf
   -python setup.py build
   -[local install:]       python setup.py install --user
   -[system wide install:] python setup.py install

To my knowledge no prepackaged versions are available yet. If you wish
to package this software please drop me a note and I'll work with you
to make this as easy as possible.

Note that this module has been developed using Fedora Linux and will
probably compile and run on any modern Linux distribution.
It may run on MacOS, Unix or BSD as well, but has not been tested there yet
(if you have tried this please let me know).

The software has not been adapted to any windows version. Since the build
system of the ECMWF BUFR library does not support any windows version, no
effort has been put into windows portability yet.
You could try to install the ECMWF BUFR library in the cygwin or mingw 
environments in windows. If you succeeded doing this, please let me know.
Any reports on your experience here are welcome.

Jos de Kloe, 9-Nov-2014.

