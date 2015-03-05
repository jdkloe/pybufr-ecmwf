#!/usr/bin/env python

'''
a simple example script that shows how to load WMO csv formatted
BUFR tables, and write them to the ECMWF specific format.
'''

# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

import os # , csv
from pybufr_ecmwf.bufr_table import BufrTable

# tested with files from the BUFRCREX_21_0_0.zip package
# downloaded from the WMO website.
# see:
# http://www.wmo.int/pages/prog/www/WMOCodes/WMO306_vI2/LatestVERSION/LatestVERSION.html
# and
# http://www.wmo.int/pages/prog/www/WMOCodes/WMO306_vI2/PrevVERSIONS/PreviousVERSIONS.html

WMO_TABLEDIR = 'BUFRCREX_21_0_0'
WMO_B_FILE = 'BUFRCREX_21_0_0_TableB_en.txt'
WMO_D_FILE = 'BUFR_21_0_0_TableD_en.txt'

SET_OF_BUFR_TABLES = BufrTable()

FILENAME = os.path.join(WMO_TABLEDIR, WMO_B_FILE)
SET_OF_BUFR_TABLES.read_WMO_csv_table_b(FILENAME)

FILENAME = os.path.join(WMO_TABLEDIR, WMO_D_FILE)
SET_OF_BUFR_TABLES.read_WMO_csv_table_d(FILENAME)

SET_OF_BUFR_TABLES.write_tables('_WMO_BUFR_TABLE.txt')
