#!/usr/bin/env python

'''a simple example script showing how to retrieve a descriptor code
when you only know (part of) a description name'''

from pybufr_ecmwf.bufr_table import BufrTable

BTABLE = 'pybufr_ecmwf/ecmwf_bufrtables/B2550000000098006001.TXT'
SEARCH_STRING = 'WMO'

BT = BufrTable()
BT.load(BTABLE)

print 'seaching for descriptors that contain substring: ', SEARCH_STRING

KEYS = BT.table_b.keys()
for k in sorted(KEYS):
    obj = BT.get_descr_object(k)
    if SEARCH_STRING in obj.name:
        print 'descriptor: {:06d} name: {}'.format(k, obj.name)

