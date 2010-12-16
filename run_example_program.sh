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
    ../BUFR_test_files2/noaa_mos/sn.0082.bin; \
    exit;
fi;
#    $TESTINPUTFILE; \
# available testfiles:
#    ../BUFR_test_files2/noaa_mos/sn.0082.bin; \
#    ../BUFR_test_files2/noaa_mos/sn.0001.bin; \
#ok  ../BUFR_test_files2/ers12/ERS19930120.coll.bufr; \
#ok  ../BUFR_test_files2/ers12/pscat96021703.pp; \
#x   ../BUFR_test_files2/ers12/pscat2000013121.pp; \
#bt  ../BUFR_test_files2/MSS_S327121011_200_PAAL31_EGRR_231200; \ # has delayed replication
#    ../BUFR_test_files2/qscat/QS_D07060_S1821_E2002_B4009191_025.genws; \ 
#    ../BUFR_test_files2/qscat/S1L2B2009313_00683_00684.bufr; \
#    ../BUFR_test_files2/ascat/ascat_20100924_063000_metopa_20395_eps_o_125.l1_bufr;\
#    ../BUFR_test_files2/ascat/ascat_20100920_003901_metopa_20335_eps_o_125_ovw.l2_bufr; \
#    ../BUFR_test_files2/ascat/ascat_20100920_003901_metopa_20335_eps_o_250_ovw.l2_bufr; \
#    ../BUFR_test_files2/ascat/ascat_20100920_003901_metopa_20335_eps_t_coa_ovw.l2_bufr; \

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

if [ "$1" == "9" ] ;  then \
    ./example_programs/bufr_to_ascii.py \
    $TESTINPUTFILE
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
echo 8: bufr_count_msgs.py
echo 9: bufr_to_ascii.py
echo 
echo please choose one of them and run again like this:
echo ./run_example_program.sh 2
echo
