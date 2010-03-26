#!/usr/bin/env python

from pybufr_ecmwf import bufr

table_code = "0000000000098000000"

BT = bufr.BufrTable(autolink_tablesdir="tmp_BUFR_TABLES")
#BT = bufr.BufrTable(tables_dir="my_BUFR_TABLES")
BT.load("B"+table_code+".TXT")
BT.load("D"+table_code+".TXT")
