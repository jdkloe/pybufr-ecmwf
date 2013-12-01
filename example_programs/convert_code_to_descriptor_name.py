#!/usr/bin/env python

'''a simple example script showing how to retrieve a description name
from a descroptor code.'''

from pybufr_ecmwf.bufr_table import BufrTable

BT = BufrTable()
BTABLE = 'pybufr_ecmwf/ecmwf_bufrtables/B2550000000098006001.TXT'
BT.load(BTABLE)

OBJ = BT.get_descr_object(int('001001', 10))
print 'OBJ: ', OBJ
print 'OBJ.name: ', OBJ.name
