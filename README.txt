The pybufr_ecmwf module provides functionality to read and write files in 
BUFR format, and to create BUFR tables.
The API consists of several layers:
-the raw/bare c API that connects python to the fortran library
-an intermediate python API around this raw layer
-[not yet finished] a high level API which should allow a pythonic object 
 oriented usage. Reading of BUFR files and creation of BUFR tables has
 been implemented, but for writing the intermediate layer is still needed.

For examples on its usage see the file USAGE.txt

For building and installation use the setup.py script.
Explanations about some non-standard options can be found in
the setup.cfg file, where things like which fortran compiler te use for
building the interface can be choosen.
Use 'setup.py --help' to get a list of all possibilities.

For manual building outside the setup.py script you can manually execute 
the build_interface.py script.

For manual testing go to the software root (where this readme file in located)
and execute the run_example_program.sh script and/or the unittests.py script.
To execute the pylint testing run the pylint/run_pylint.py script.

WARNING for python3 users:
numpy for python3 is still very new, so may not be available
as default package from your favourite linux distribution
(however note that Fedora 15 does include it now).
Therefore you may need to install a 3rd party numpy rpm/deb package or
install numpy from source first, before you can use the python3 version
of this pybufr_ecmwf module.

WARNING2 for python3 users:
the f2py tool that comes with numpy was broken, and crashed during 
the build process.
The problem has been reported to the numpy developers (see
http://projects.scipy.org/numpy/ticket/1932 and
https://github.com/numpy/numpy/pull/3230), and the bug was fixed
in may 2013. However, if your numpy version is older than that this 
may still be a problem.

For more information on this module please consult the wiki at:
http://code.google.com/p/pybufr-ecmwf/

If you have any questions feel free to contact me by email.

Jos de Kloe, 01-Dec-2013.
