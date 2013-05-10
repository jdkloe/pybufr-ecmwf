#!/usr/bin/env python

# a simple example script showing how to retrieve a descriptor code
# when you only know (part of) a description name

from pybufr_ecmwf.bufr_table import BufrTable

btable = 'pybufr_ecmwf/ecmwf_bufrtables/B2550000000098006001.TXT'
search_string = 'WMO'

BT = BufrTable()
BT.load(btable)

print 'seaching for descriptors that contain substring: ', search_string

keys = BT.table_b.keys()
for k in sorted(keys):
    obj = BT.get_descr_object(k)
    if search_string in obj.name:
        print 'descriptor: {:06d} name: {}'.format(k, obj.name)

