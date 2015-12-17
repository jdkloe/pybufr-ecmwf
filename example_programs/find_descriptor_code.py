#!/usr/bin/env python

'''a simple example script showing how to retrieve a descriptor code
when you only know (part of) a description name'''

# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

from __future__ import print_function
from pybufr_ecmwf.bufr_table import BufrTable

BTABLE = 'pybufr_ecmwf/ecmwf_bufrtables/B2550000000098006001.TXT'
SEARCH_STRING = 'WMO'

BT = BufrTable()
BT.load(BTABLE)

print('seaching for descriptors that contain substring: ', SEARCH_STRING)

KEYS = BT.table_b.keys()
for k in sorted(KEYS):
    obj = BT.get_descr_object(k)
    if SEARCH_STRING in obj.name:
        # this is not python 2.6 compatible
        #print('descriptor: {:06d} name: {}'.format(k, obj.name))
        # so use this in stead
        print('descriptor: %06d name: %s' % (k, obj.name))

