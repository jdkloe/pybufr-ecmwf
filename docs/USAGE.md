## Usage of the pybufr-ecmwf module

Pybufr_ecmwf is a python module for reading and of writing BUFR files
and for composing BUFR templates.
This file explains how the high level interface works.
The intermediate and low level interface is not documented here (only in the
code and in some example files), and their use is not recommended.

### READING

To open a bufr file, iterate over its messages, and
extract the data, you can use some python code like this:
```python
from pybufr_ecmwf.bufr import BUFRReader
with BUFRReader(input_bufr_file) as bufr:
    for data, names, units in bufr.messages():
        <some code using the data>
```
in this simple case there is no need to specify which bufr tables
to load or where they should be found.
The defaults set by the pybufr-ecmwf module are sufficient
do decode most bufr messages.
It least all official WMO templates update version 26
(released 4-May-2016, see:
 http://www.wmo.int/pages/prog/www/WMOCodes/WMO306_vI2/LatestVERSION/LatestVERSION.html),
and most local ECMWF templates should be supported.

A full example program showing decoding is included in the module:

* example_programs/example_for_using_bufr_message_iteration.py

Another example tool to demonstrate how to extract the data from a BUFR file
and convert it to ASCII of CSV format is this one:

* example_programs/bufr_to_ascii.py

In case your BUFR files are mixed and have several message types in a
single file, it is convenient to sort them first before decoding.
To do this you can use the script:
* example_programs/sort_bufr_msgs.py

### WRITING

To create new BUFR files the easy way, the BUFRWriter class can be used.
This class forms the higher level interface.
It allows you to select a default template that defines
the available fields in your file (whenever possible, try to use the
templates defined in the official WMO list).
Once this template is selected, it is very easy to fill one or
all subsets (rows) of data with numbers by providing one value
or an array of values (one for each subset for a given field).

A script to write BUFR files could like like this:
```python
from pybufr_ecmwf.bufr import BUFRWriter
bwr = BUFRWriter()
bwr.open(output_bufr_file)
msg = bwr.add_new_msg(num_subsets=3)
msg.set_template('301033')
msg['YEAR'] = 2016
msg['LATITUDE'] = [55.2, 66.3, 77.4]
msg.write_msg_to_file()
bwr.close()
```
A fully implemented example script can be found in:
* test/test_simple_wmo_template.py 

The high level interface does not yet support more advanced features
like delayed replication. If you need to use a template that uses this
then you have the option to use the intermediate level interface
which is fully implemented.
An example on how to use it can be found in this example script:

* example_programs/example_for_using_bufrinterface_ecmwf_for_encoding.py

Please take care when encoding "missing" values.
The ECMWF bufrdc software uses the special value 1.7e38 to indicate missing values,
and you should use this value when filling a bufr message with data, even if
this value is far outside the allowed value range for the parameter in question.
Starting from version 0.84 upward it will also be possible to use
the numpy.nan value to indicate missing in the pybufr-ecmwf module.

### TEMPLATE DESIGN

On top of the functionality provided by the bufrdc fortran library,
this python module also adds the possibility to create BUFR templates
and write the results as BUFR tables that can be used by the
ECMWF BUFRDC library

However, please note that the format of these bufr tables
is not regulated by any standard and will not be compatible in any
way with other bufr reading software.
Unfortunately this also includes the new ecCodes library.
A conversion to the new ECMWF ecCodes bufr tables may be provided
in a future version of this module.

higher level interface:


... [to be written] ...

currently only the intermediate level interface is fully implemented.
An example tool to demonstrate how to create a set of BUFR tables from
scratch, and another tool that uses these tables for encoding:

*  example_programs/create_bufr_tables.py

*  example_programs/use_custom_tables_for_encoding.py

### general remark

For usage examples you can take a look at the programs in the
example_programs and test directories in the source code.
The run_example_program.sh shell script allows easy testing of all of
these programs. 
All needed test data files are provided in the test/testdata directory.

If you have any questions or requests feel free to contact me by email.

Jos de Kloe, 29-Sep-2016
