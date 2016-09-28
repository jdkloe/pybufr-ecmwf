#!/usr/bin/env python

'''
some python code to demonstrate the simples way to create
a new bufr message using a template from the official WMO
tables (i.e. 305038 in table D; moored buoys)
'''
from __future__ import print_function
from pybufr_ecmwf.bufr import BUFRReader, BUFRWriter

output_bufr_file = 'dummy_bufr_file.bfr'

bwr = BUFRWriter()
bwr.open(output_bufr_file)

msg = bwr.add_new_msg(num_subsets=3)
msg.set_template('301033')
print('number of fields per subset is: ', msg.num_fields)

names = msg.get_field_names()
print('='*25+'\navailable field names: '+
      '\n'.join(n for n in names)+'\n'+'='*25)

msg['IDENTIFIER'] = [12345, 23456, 34567]
msg['TYPE'] = 0 # AUTOMATIC
msg['YEAR'] = 2016
msg['MONTH'] = 9
msg['DAY'] = 30
msg['HOUR'] = 17
msg['MINUTE'] = 18
msg['LATI'] = [55.2, 66.3, 77.4]
msg['LONG'] = [5.1, 6.2, 7.3]

# debug
print('values: ', list(msg.values))

msg.write_msg_to_file()
bwr.close()

##############################
# reopen the BUFR file as test
##############################

print('*'*50)

input_bufr_file = output_bufr_file
bufr = BUFRReader(input_bufr_file, warn_about_bufr_size=False)

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
