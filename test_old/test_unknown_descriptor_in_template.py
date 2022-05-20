#!/usr/bin/env python

'''
some python code to test what happens if you try to use an invalud
(local) BUFR descriptor when composing a BUFR message.
'''
from __future__ import print_function
from pybufr_ecmwf.bufr import BUFRReader, BUFRWriter

output_bufr_file = 'dummy_bufr_file.bfr'

bwr = BUFRWriter()
bwr.open(output_bufr_file)
msg = bwr.add_new_msg(num_subsets=3)
B_entries = ['040239', '040240']
msg.set_template(B_entries)

#msg['040239'] = [5.1, 6.2, 7.3]
#msg.write_msg_to_file()
#bwr.close()

