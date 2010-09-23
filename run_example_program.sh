#!/bin/sh

PYTHONPATH='./':$PYTHONPATH
export PYTHONPATH

# some test input BUFR files
TESTINPUTFILE='example_programs/testdata/Testfile.BUFR'
CORRUPTEDTESTINPUTFILE='example_programs/testdata/Testfile3CorruptedMsgs.BUFR'

# NOTE: this testfile: Testfile3CorruptedMsgs.BUFR holds 3 copies of 
# Testfile.BUFR catted together, and was especially modified using hexedit 
# to have false end markers (7777) halfway the 2nd and 3rd message. 
# These messages are therefore corrupted and decoding them will probably
# result in garbage, but they are very usefull to test the algorithms for
# splitting the file in BUFR messages as is done in the
# BUFRFile.split() method and the ecmwfbufr.pbbufr subroutine.
# Note also that the current runtime error that exists in 
# example_for_using_pb_routines.py has nothing to do with this file corruption

# some output BUFR filenames
TESTOUTPUTFILE1='example_programs/testdata/Testoutputfile1.BUFR'
TESTOUTPUTFILE2='example_programs/testdata/Testoutputfile2.BUFR'
TESTOUTPUTFILE3='example_programs/testdata/Testoutputfile3.BUFR'

# some BUFR tables to be verified
BTABLE='pybufr_ecmwf/ecmwf_bufrtables/B_default.TXT'
DTABLE='pybufr_ecmwf/ecmwf_bufrtables/D_default.TXT'

if [ "$1" == "1" ] ;  then \
    ./example_programs/example_for_using_bufrinterface_ecmwf_for_decoding.py \
    $TESTINPUTFILE; \
    exit;
fi;

if [ "$1" == "2" ] ;  then \
    ./example_programs/example_for_using_bufrinterface_ecmwf_for_encoding.py \
    $TESTOUTPUTFILE1; \
    exit;
fi;

if [ "$1" == "3" ] ;  then \
    ./example_programs/example_for_using_ecmwfbufr_for_decoding.py \
    $TESTINPUTFILE; \
    exit;
fi;

if [ "$1" == "4" ] ;  then \
    ./example_programs/example_for_using_ecmwfbufr_for_encoding.py \
    $TESTOUTPUTFILE2; \
    exit;
fi;

if [ "$1" == "5" ] ;  then \
    ./example_programs/example_for_using_pb_routines.py \
    $CORRUPTEDTESTINPUTFILE; \
    exit;
fi;


if [ "$1" == "6" ] ;  then \
    ./example_programs/example_for_using_rawbufrfile.py \
    $CORRUPTEDTESTINPUTFILE  $TESTOUTPUTFILE3; \
    exit;
fi;

if [ "$1" == "7" ] ;  then \
    ./example_programs/verify_bufr_tables.py \
    $BTABLE $DTABLE; \
    exit;
fi;

echo
echo this script takes a number to choose which test program to run
echo
echo 1: example_for_using_bufrinterface_ecmwf_for_decoding.py
echo 2: example_for_using_bufrinterface_ecmwf_for_encoding.py
echo 3: example_for_using_ecmwfbufr_for_decoding.py
echo 4: example_for_using_ecmwfbufr_for_encoding.py
echo 5: example_for_using_pb_routines.py [has known problems]
echo 6: example_for_using_rawbufrfile.py
echo 7: verify_bufr_tables.py
echo 
echo please choose one of them and run again like this:
echo ./run_example_program.sh 2
echo

