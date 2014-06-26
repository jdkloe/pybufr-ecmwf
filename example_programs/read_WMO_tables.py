#!/usr/bin/env python

'''
a simple example script that shows how to load WMO csv formatted
BUFR tables, and write them to the ECMWF specific format.
'''

import os # , csv
from pybufr_ecmwf.bufr_table import BufrTable

# testwed with files from the BUFRCREX_21_0_0.zip package
# downloaded from the WMO website.
# see:
# http://www.wmo.int/pages/prog/www/WMOCodes/WMO306_vI2/LatestVERSION/LatestVERSION.html
# and
# http://www.wmo.int/pages/prog/www/WMOCodes/WMO306_vI2/PrevVERSIONS/PreviousVERSIONS.html

wmo_tabledir = 'BUFRCREX_21_0_0'
wmo_b_file = 'BUFRCREX_21_0_0_TableB_en.txt'
wmo_d_file = 'BUFR_21_0_0_TableD_en.txt'

set_of_bufr_tables = BufrTable()

filename = os.path.join(wmo_tabledir, wmo_b_file)
set_of_bufr_tables.read_WMO_csv_table_b(filename)

filename = os.path.join(wmo_tabledir, wmo_d_file)
set_of_bufr_tables.read_WMO_csv_table_d(filename)

set_of_bufr_tables.write_tables('_WMO_BUFR_TABLE.txt')
