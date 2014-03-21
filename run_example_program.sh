#!/bin/sh

# perform some searches to ensure the PYTHONPATH points to a directory
# that holds the compiled version of the pybufr-ecmwf module.

MODULELOCATION1='./'
if test -e build; then
  MODULELOCATION2=`find build | grep ecmwfbufr.so | awk -F/ '{ print $1 "/" $2  "/"}'`
fi

# safety check
if test -e $MODULELOCATION1/'pybufr_ecmwf/ecmwfbufr.so'; then
   echo found compiled interface module: $MODULELOCATION1/pybufr_ecmwf/ecmwfbufr.so
   PYTHONPATH=$MODULELOCATION1:$PYTHONPATH
   export PYTHONPATH
fi

if test -e build; then
   if test -e $MODULELOCATION2/'pybufr_ecmwf/ecmwfbufr.so'; then
      echo found compiled interface module: $MODULELOCATION2/pybufr_ecmwf/ecmwfbufr.so
      PYTHONPATH=$MODULELOCATION2:$PYTHONPATH
      export PYTHONPATH
   fi
fi

python -c 'import sys;del sys.path[0];import pybufr_ecmwf.ecmwfbufr'
if [ $? -ne 0 ]; then
   echo 'could not find compiled interface module:'
   echo '     pybufr_ecmwf/ecmwfbufr.so'
   echo 'or'
   echo '     build/lib*/pybufr_ecmwf/ecmwfbufr.so'
   echo 'or'
   echo '     a local or system wide installed copy'
   echo ''
   echo 'This script only runs when the software is build and/or installed.'
   echo ''
   echo 'Before using this test script you could try to manually build this'
   echo 'software first using this method:'
   echo '    python ./build_interface.py'
   echo ''
   exit 1
fi

# some test input BUFR files
TESTINPUTFILE='test/testdata/Testfile.BUFR'
CORRUPTEDTESTINPUTFILE='test/testdata/Testfile3CorruptedMsgs.BUFR'

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
TESTOUTPUTFILE1='test/testdata/Testoutputfile1.BUFR'
TESTOUTPUTFILE2='test/testdata/Testoutputfile2.BUFR'
TESTOUTPUTFILE3='test/testdata/Testoutputfile3.BUFR'

# some BUFR tables to be verified
BTABLE='pybufr_ecmwf/ecmwf_bufrtables/B_default.TXT'
DTABLE='pybufr_ecmwf/ecmwf_bufrtables/D_default.TXT'

if [ "$1" == "1" ] ;  then \
    ./example_programs/example_for_using_bufrinterface_ecmwf_for_decoding.py \
    $TESTINPUTFILE; \
    exit;
fi;
#    $TESTINPUTFILE; \
# available testfiles:
#ok  ../BUFR_test_files2/noaa_mos/sn.0082.bin; \
#x   ../BUFR_test_files2/noaa_mos/sn.0001.bin; \
#ok  ../BUFR_test_files2/ers12/ERS19930120.coll.bufr; \
#ok  ../BUFR_test_files2/ers12/pscat96021703.pp; \
#ok  ../BUFR_test_files2/ers12/pscat2000013121.pp; \
#bt  ../BUFR_test_files2/MSS_S327121011_200_PAAL31_EGRR_231200; \ # has delayed replication
#ok  ../BUFR_test_files2/qscat/QS_D07060_S1821_E2002_B4009191_025.genws; \
#ok  ../BUFR_test_files2/qscat/S1L2B2009313_00683_00684.bufr; \
#x   ../BUFR_test_files2/ascat/ascat_20100924_063000_metopa_20395_eps_o_125.l1_bufr;\
#ok  ../BUFR_test_files2/ascat/ascat_20100920_003901_metopa_20335_eps_o_125_ovw.l2_bufr; \
#ok  ../BUFR_test_files2/ascat/ascat_20100920_003901_metopa_20335_eps_o_250_ovw.l2_bufr; \
#ok  ../BUFR_test_files2/ascat/ascat_20100920_003901_metopa_20335_eps_t_coa_ovw.l2_bufr; \

# notes on failing tests:
# sn.0001.bin failes because I have no BUFR table that defines table B descriptor 011200
# ascat_*_metopa_*.l1_bufr failes because bufrex returns with the error "KELEMARGUMENT TOO SMALL"
# which I don't understand because the nr of descriptors of 117 and the number of
# subsets of 1722 seems to be determined correctly.

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
    echo 
    echo 
    echo "Note that an error is expected for this program on some platforms"
    echo "Seems especially the case on 64-bit linux)"
    echo 
    echo 
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

if [ "$1" == "8" ] ;  then \
    ./example_programs/bufr_count_msgs.py \
    $CORRUPTEDTESTINPUTFILE
    exit;
fi;

if [ "$1" == "9a1" ] ;  then \
    ./example_programs/bufr_to_ascii.py -a -1 -i \
    $TESTINPUTFILE
    exit;
fi;

if [ "$1" == "9a2" ] ;  then \
    ./example_programs/bufr_to_ascii.py -a -2 -i \
    $TESTINPUTFILE
    exit;
fi;

if [ "$1" == "9a3" ] ;  then \
    ./example_programs/bufr_to_ascii.py -a -3 -i \
    $TESTINPUTFILE
    exit;
fi;

if [ "$1" == "9c1" ] ;  then \
    ./example_programs/bufr_to_ascii.py -c -1 -i \
    $TESTINPUTFILE
    exit;
fi;

if [ "$1" == "9c2" ] ;  then \
    ./example_programs/bufr_to_ascii.py -c -2 -i \
    $TESTINPUTFILE
    exit;
fi;

if [ "$1" == "9c3" ] ;  then \
    ./example_programs/bufr_to_ascii.py -c -3 -i \
    $TESTINPUTFILE
    exit;
fi;

echo
echo 'this script takes a number/switch to choose which test program to run'
echo
echo '1: example_for_using_bufrinterface_ecmwf_for_decoding.py'
echo '2: example_for_using_bufrinterface_ecmwf_for_encoding.py'
echo '3: example_for_using_ecmwfbufr_for_decoding.py'
echo '4: example_for_using_ecmwfbufr_for_encoding.py'
echo '5: example_for_using_pb_routines.py [has known problems]'
echo '6: example_for_using_rawbufrfile.py'
echo '7: verify_bufr_tables.py'
echo '8: bufr_count_msgs.py'
echo '9a1: bufr_to_ascii.py -a -1 -i <file>'
echo '9a2: bufr_to_ascii.py -a -2 -i <file>'
echo '9a3: bufr_to_ascii.py -a -3 -i <file>'
echo '9c1: bufr_to_ascii.py -c -1 -i <file>'
echo '9c2: bufr_to_ascii.py -c -2 -i <file>'
echo '9c3: bufr_to_ascii.py -c -3 -i <file>'
echo 
echo 'please choose one of them and run again like this:'
echo './run_example_program.sh 2'
echo
