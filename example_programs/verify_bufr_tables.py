#!/usr/bin/env python

"""
this small example program loads the BUFR B- and D-tables
and reports any inconsistencies it finds in the table definitions
"""

import sys
from pybufr_ecmwf.bufr_table import BufrTable

if len(sys.argv)<3:
    print 'please give 2 BUFR TABLE files as argument'
    sys.exit(1)

BTABLE_FILE = sys.argv[1]
DTABLE_FILE = sys.argv[2]

#BT = bufr.BufrTable(tables_dir="my_BUFR_TABLES")
#BT = bufr.BufrTable(tables_dir="../ecmwf_bufrtables")
BT = BufrTable()
BT.load(BTABLE_FILE)
BT.load(DTABLE_FILE)
