#!/usr/bin/env python

'''
some python code to demonstrate a simple way to create
a new bufr message using a template from the official WMO
tables that contains some ascii text entries
(i.e. 300004 in table D; B-table entry)
'''
from __future__ import print_function
from pybufr_ecmwf.bufr import BUFRReader, BUFRWriter

output_bufr_file = 'dummy_bufr_file.bfr'

bwr = BUFRWriter()
#bwr = BUFRWriter(verbose=True)
bwr.open(output_bufr_file)

msg = bwr.add_new_msg(num_subsets=1)
msg.set_template('300004')
print('number of fields per subset is: ', msg.num_fields)

names = msg.get_field_names()
print('='*25+'\navailable field names: '+
      '\n'.join(n for n in names)+'\n'+'='*25)

# NOTE 1: I have no experience with filling a BUFR message with
# this  kind of input, so I had to guess here.
# If anyone knows how this should be done, I would appreciate
# any feedback on mistakes I might have made.

# NOTE 2: string inputs should be of correct lenght as defined in the
# template.
#    TODO: force this by truncating or adding spaces (and align left or right)

msg['F DESCRIPTOR TO BE ADDED OR DEFINED'] = '0'
msg['X DESCRIPTOR TO BE ADDED OR DEFINED'] = '48' # local class
msg['Y DESCRIPTOR TO BE ADDED OR DEFINED'] = '192' # local entry
msg['ELEMENT NAME, LINE 1'] = '{:32s}'.format('This is a dummy element')
msg['ELEMENT NAME, LINE 2'] = '{:32s}'.format('Second line of dummy element')
msg['UNITS NAME'] = '{:24s}'.format('M/S')
msg['UNITS SCALE SIGN'] = "+"
msg['UNITS SCALE[1]'] = "  5"
msg['UNITS REFERENCE SIGN'] = "+"
msg['UNITS REFERENCE VALUE'] = '{:10s}'.format("100") # 10 chars/80 bits
msg['ELEMENT DATA WIDTH'] = " 24" # 3 chars (24 bits)

# debug
print('values: ', list(msg.values))

msg.write_msg_to_file()
bwr.close()

##############################
# reopen the BUFR file as test
##############################

print('*'*50)

input_bufr_file = output_bufr_file
bufr = BUFRReader(input_bufr_file, expand_strings=True,
                  warn_about_bufr_size=False)

# just 1 msg in this test file, so no looping needed
for msg in bufr:
    print('num_subsets = ', msg.get_num_subsets())
    for subs, msg_or_subset_data in enumerate(msg):
        list_of_names = msg_or_subset_data.names
        list_of_units = msg_or_subset_data.units
        data = msg_or_subset_data.data
        print('"subset nr"'+','+','.join(list_of_names))
        print('""'+','+','.join(list_of_units))
        print(str(subs+1)+','+','.join(str(val) for val in data[:]))

bufr.close()
