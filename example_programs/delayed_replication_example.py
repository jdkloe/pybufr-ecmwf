#!/usr/bin/env python

'''
some python code to generate BUFR tables needed to
test delayed replication encoding and decoding
'''
from __future__ import print_function

import numpy

# import pybufr_ecmwf
from pybufr_ecmwf.bufr_table import Descriptor
from pybufr_ecmwf.bufr_table import CompositeDescriptor
from pybufr_ecmwf.bufr_table import Replicator
from pybufr_ecmwf.bufr_table import BufrTable
from pybufr_ecmwf.bufr_template import BufrTemplate
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr import BUFRReader

var1, var2, var3, D_363192 = (None, )*4 # dummy defs for pylint

# varname, reference, name, unit, unit_scale, unit_reference, data_width
B_entries = [
    ('var1', '063250', 'TEST VARIABLE 1', 'UNIT 1', 0, 0, 10),
    ('var2', '063251', 'TEST VARIABLE 2', 'UNIT 2', 1, 0, 15),
    ('var3', '063252', 'TEST VARIABLE 3', 'UNIT 3', 2, 0, 20),
    ('delrepl', '031001', 'DELAYED DESCRIPTOR REPLICATION FACTOR',
     'NUMERIC', 0, 0, 8),
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

# reference, descriptor_list, comment
# note: codes 348001 and above don't work as expected. No idea why.
D_entries = [
    ('363192', [var2, # variable 2
                Replicator(7, [var3,]), # 7 repeats for variable 3
                ],
     "dummy test template"),
    ]

for (reference, descriptor_list, comment) in D_entries:
    varname = 'D_'+reference
    setattr(g, varname, CompositeDescriptor(reference, descriptor_list,
                                            comment, bufr_table_set))
    Ddescr = getattr(g, varname)
    bufr_table_set.add_to_D_table(Ddescr)

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
max_nr_of_repeats = 5
template = BufrTemplate()
template.add_descriptor(var1) # 1 item
template.add_delayed_replic_descriptors(max_nr_of_repeats,
                                        D_363192) # max. 1 + 5*5 items

# and use this BUFR template to create a test BUFR message
bufr = BUFRInterfaceECMWF(verbose=True)

# fill sections 0, 1, 2 and 3
num_subsets = 3
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
# 2 + max_nr_of_repeats*8 = 42
bufr.register_and_expand_descriptors(template)
# retrieve the length of the expanded descriptor list
exp_descr_list_length = bufr.ktdexl
print("exp_descr_list_length = ", exp_descr_list_length)

# fill the values array with some dummy varying data
num_values = num_subsets*bufr.max_nr_expanded_descriptors
values = numpy.zeros(num_values, dtype=numpy.float64) # this is the default

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

    num_replications = subset+1
    i = subset*exp_descr_list_length

    # fill var1
    values[i] = 12.345
    i = i+1

    # set actual delayed replication repeats
    values[i] = num_replications
    i = i+1
    repl_counts.append(num_replications)

    for j in range(num_replications):
        # fill the D363192 item, which defines 1x 63251 and 7x63252
        values[i] = 2.345
        i = i+1
        for k in range(7):
            values[i] = 1.5*i+0.1*j+0.01*k
            i = i+1

# do the encoding to binary format
bufr.kdata = numpy.array(repl_counts)
print('bufr.kdata = ', bufr.kdata)
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
bob = BUFRReader(input_bufr_file, warn_about_bufr_size=False)
bob.setup_tables(table_b_to_use='B'+table_name,
                 table_d_to_use='D'+table_name)

# just 1 msg in this test file, so no looping needed
bob.get_next_msg()
nsubsets = bob.get_num_subsets()
print('num_subsets = ', nsubsets)
for subs in range(1, nsubsets+1):
    # add header strings
    (list_of_names, list_of_units) = bob.get_names_and_units(subs)
    data = bob.get_subset_values(subs)
    print('"subset nr"'+','+','.join(list_of_names))
    print('""'+','+','.join(list_of_units))
    print(str(subs)+','+','.join(str(val) for val in data[:]))

bob.close()

######################################################
# reopen the BUFR file as test an try message iterator
######################################################


print('*'*50)

input_bufr_file = output_bufr_file
bob = BUFRReader(input_bufr_file, warn_about_bufr_size=False)
bob.setup_tables(table_b_to_use='B'+table_name,
                 table_d_to_use='D'+table_name)

for data, names, units in bob.messages():
    print(data)
    print(names)
    print(units)

bob.close()
