#!/usr/bin/env python

"""
this small example program loads the BUFR B- and D-tables
and reports any inconsistencies it finds in the table definitions
"""

# import some home made helper routines
from helpers import call_cmd_and_verify_output, set_python_path
set_python_path()

from pybufr_ecmwf import bufr

TABLE_CODE = "0000000000098000000"

#BT = bufr.BufrTable(tables_dir="my_BUFR_TABLES")
BT = bufr.BufrTable(tables_dir="../ecmwf_bufrtables")
BT.load("B"+TABLE_CODE+".TXT")
BT.load("D"+TABLE_CODE+".TXT")
