#!/usr/bin/env python

'''
some python code to generate BUFR tables needed to
test delayed replication encoding and decoding
'''
from __future__ import print_function

import numpy

from pybufr_ecmwf.bufr_table import Descriptor
from pybufr_ecmwf.bufr_table import CompositeDescriptor
from pybufr_ecmwf.bufr_table import ExtendedDelayedReplicator as EDR1
from pybufr_ecmwf.bufr_table import BufrTable
from pybufr_ecmwf.bufr_template import BufrTemplate
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr import BUFRReader

# varname, reference, name, unit, unit_scale, unit_reference, data_width
B_entries = [
    ('dummy1', '063251', 'DUMMY VARIABLE', 'DUMMY UNIT', 0, 0, 25),
    ('extdelrepl', '031002', 'EXTENDED DELAYED DESCRIPTOR REPLICATION FACTOR',
     'NUMERIC', 0, 0, 16),
    ]

bufr_table_set = BufrTable()

# import global namespace __main__ as g
import __main__ as g
for (varname, reference, name, unit, unit_scale,
     unit_reference, data_width) in B_entries:
    reference_nr = int(reference, 10)
    setattr(g, varname, Descriptor(reference_nr, name, unit, unit_scale,
                                   unit_reference, data_width))
    Bdescr = getattr(g, varname)
    bufr_table_set.add_to_B_table(Bdescr)

# compose the D table entry (the actual template to be used)
# EDR1 = ExtendedDelayedReplicator

# reference, descriptor_list, comment
D_363192 = CompositeDescriptor(363192,
                               [dummy1,
                                EDR1([dummy1,
                                      ])
                                ],
                               "test delayed replication", bufr_table_set)

bufr_table_set.add_to_D_table(D_363192)

print('='*50)
print("B-table:")
print('='*50)
bufr_table_set.print_B_table()
print('='*50)
print("D-table:")
print('='*50)
bufr_table_set.print_D_table()
print('='*50)

# define the table name without preceding 'B' or 'D' character
# (which will be prepended by the below write method)
table_name = '_test_table.txt'
bufr_table_set.write_tables(table_name)

# now use these definitions to create a BUFR template
max_nr_of_replications = 3
num_subsets = 3
num_replications = [1, 2, 3]

template = BufrTemplate(verbose=True)
template.add_descriptor(D_363192) # 1 item
template.del_repl_max_nr_of_repeats_list = [max_nr_of_replications,]*num_subsets

# and use this BUFR template to create a test BUFR message
bufr = BUFRInterfaceECMWF(verbose=True)

# fill sections 0, 1, 2 and 3
bufr.fill_sections_0123(bufr_code_centre=0,
                        bufr_obstype=0,
                        bufr_subtype=0,
                        bufr_table_local_version=0,
                        bufr_table_master=0,
                        bufr_table_master_version=0,
                        bufr_code_subcentre=0,
                        num_subsets=num_subsets,
                        bufr_compression_flag=0)
                        # 64=compression/0=no compression

# determine information from sections 0123 to construct the BUFR table
# names expected by the ECMWF BUFR library and create symlinks to the
# default tables if needed
bufr.setup_tables(table_b_to_use='B'+table_name,
                  table_d_to_use='D'+table_name)

# expected nr of descriptors is:
# (1 + 1 + 3) = 5

bufr.register_and_expand_descriptors(template)
# retrieve the length of the expanded descriptor list
exp_descr_list_length = bufr.ktdexl
print("exp_descr_list_length = ", exp_descr_list_length)
#print("exp_descr_list = ",  bufr.ktdexp)

# fill the values array with some dummy varying data
num_values = num_subsets*bufr.max_nr_expanded_descriptors
values = numpy.zeros(num_values, dtype=numpy.float64) # this is the default
print("num_values = ", num_values)

# note: these two must be identical for now, otherwise the
# python to fortran interface breaks down. This also ofcourse is the
# cause of the huge memory use of cvals in case num_values is large.
num_cvalues = num_values
cvals = numpy.zeros((num_cvalues, 80), dtype=numpy.character)
cvals_index = 0
repl_counts = []

for subset in range(num_subsets):
    # note that python starts counting with 0, unlike fortran,
    # so there is no need to take (subset-1)
    i = subset*exp_descr_list_length

    # fill dummy var
    values[i] = 12345.
    i = i+1

    # set actual delayed replication number
    values[i] = num_replications[subset]
    i = i+1
    repl_counts.append(num_replications[subset])

    for j in range(num_replications[subset]):

        # fill dummy var
        values[i] = 23456.
        i = i+1

# debug
print('values[:25]: ', values[:25].tolist()) #numpy.where(values != 0)]))
print('values[-25:]: ', values[-25:].tolist())

# do the encoding to binary format
bufr.kdata = numpy.array(repl_counts)
print('bufr.kdata = ', bufr.kdata.tolist())
bufr.encode_data(values, cvals)

# get an instance of the RawBUFRFile class
bf1 = RawBUFRFile()

output_bufr_file = 'dummy_bufr_file.bfr'
# open the file for writing
bf1.open(output_bufr_file, 'wb')
# write the encoded BUFR message
bf1.write_raw_bufr_msg(bufr.encoded_message)
# close the file
bf1.close()

##############################
# reopen the BUFR file as test
##############################

print('*'*50)

input_bufr_file = output_bufr_file
bufr = BUFRReader(input_bufr_file, warn_about_bufr_size=False)
bufr.setup_tables(table_b_to_use='B'+table_name,
                  table_d_to_use='D'+table_name)

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
