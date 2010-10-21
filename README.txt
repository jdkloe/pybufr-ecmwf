The pybufr_ecmwf module provides functionality to read and write files in 
BUFR format. 
The API consists of several layers:
-the raw/bare c API that connects python to the fortran library
-an intermediate python API around this raw layer
-[not yet finished] a high level API which should allow a pythonic object 
 oriented usage

For examples on its usage see the file USAGE.txt

For building and installation use the setup.py script.
Explanations about some non-standard options can be found in
the setup.cfg file, where things like which fortran compiler te use for
building the interface can be choosen.

For manual building outside the setup.py script you can manually execute 
the build_interface.py script.
For manual testing go to the software root (where this readme file in located)
and execute the run_example_program.sh script and/or the unittests.py script.
To execute the pylint testing run the pylint/run_pylint.py script.

For more information on this module please consult the wiki at:
http://code.google.com/p/pybufr-ecmwf/

If you have any questions feel free to contact me by email.

Jos de Kloe, 21-Oct-2010.

