#!/usr/bin/env python

# this example code demonstrates how to:
# -compose a custom BUFR template
# -generate minimal private BUFR tables to encode this template
# -use the template and BUFR tables to encode and decode a BUFR message

# import pybufr_ecmwf
from pybufr_ecmwf.bufr_table import Descriptor
from pybufr_ecmwf.bufr_table import CompositeDescriptor
from pybufr_ecmwf.bufr_table import Replicator
from pybufr_ecmwf.bufr_table import BufrTable
import numpy, sys

# see: WMO_BUFR_Guide_Layer3-English-only.pdf
#
# p.25 (L3-23)
# for F=0 (table B entries) and F=3 (table D entries)
# classes x=48 to 63 are reserved for local use
# entries y=192-255 within all classes are reserved for local use
#
# it would be best to reusing existing WMO approved descriptors
# as much as possible

# varname, reference, name, unit, unit_scale, unit_reference, data_width
B_entries = [
    ('year', '004001', 'YEAR', 'YEAR', 0, 0, 12),
    ('month', '004002', 'MONTH', 'MONTH', 0, 0, 4),
    ('day', '004003', 'DAY', 'DAY', 0, 0, 6),
    ('lat', '005001', 'LATITUDE (HIGH ACCURACY)', 'DEGREE', 5, -9000000, 25),
    ('lon', '006001', 'LONGITUDE (HIGH ACCURACY)', 'DEGREE', 5, -18000000, 26),
    ('variable1', '048001', 'SOME VARIABLE', 'M', 0, 0, 13),
    ('variable2', '048002', 'SOME OTHER VARIABLE', 'S', 2, 500, 13),
    ('product_name', '048003', 'PRODUCT NAME', 'CCITT IA5', 0, 0, 64*8),
    ('variable3', '048004', 'REPL. VARIABLE', 'KG', 2, -1000, 13),
    ('delrepl', '031001', 'DELAYED DESCRIPTOR REPLICATION FACTOR', 'NUMERIC', 0, 0, 8),
    ]

bufr_table_set = BufrTable()

# import global namespace __main__ as g
import __main__ as g
for (varname, reference, name, unit, unit_scale,
     unit_reference, data_width) in B_entries:
    reference_nr = int(reference,10)
    setattr(g, varname, Descriptor(reference_nr, name, unit, unit_scale,
                                   unit_reference, data_width))
    Bdescr = getattr(g, varname)
    bufr_table_set.add_to_B_table(Bdescr)

# reference, descriptor_list, comment
# note: codes 348001 and above don't work as expected. No idea why.
D_entries = [
    ('301192',[year, month, day,      # reference date
               product_name],         # product name
     "header information"),
    ('301193',[lat,        # Latitude
               lon,        # Longitude
               variable1,  # first variable
               Replicator(3,[variable2,]),  # second variable, 3 times repeated
               ],
    "measurement information"),
    ]

for (reference, descriptor_list, comment) in D_entries:
    varname = 'D_'+reference
    setattr(g, varname, CompositeDescriptor(reference, descriptor_list,
                                            comment, bufr_table_set))
    Ddescr = getattr(g, varname)
    bufr_table_set.add_to_D_table(Ddescr)

print '='*50
print "B-table:"
print '='*50
bufr_table_set.print_B_table()
print '='*50
print "D-table:"
print '='*50
bufr_table_set.print_D_table()
print '='*50

# define the table name without preceding 'B' or 'D' character
# (which will be prepended by the below write method)
table_name = '_private_BUFR_table.txt'
bufr_table_set.write_tables(table_name)

# now use these definitions to create a BUFR template
from pybufr_ecmwf.bufr_template import BufrTemplate

# include delayed replication in the test or not?
#use_delayed_replication = False
use_delayed_replication = True

template = BufrTemplate()
template.add_descriptor(D_301192) # 4 items
template.add_descriptor(D_301193) # 6 items
if use_delayed_replication:
    max_nr = 5 # max. 5*1 items
    template.add_delayed_replic_descriptors(max_nr,[variable3,])


# and use this BUFR template to create a test BUFR message
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
bufr = BUFRInterfaceECMWF(verbose=True)

# fill sections 0, 1, 2 and 3
num_subsets = 2
bufr.fill_sections_0123(bufr_code_centre =  98, # ECMWF
                        bufr_obstype     =   3, # sounding
                        bufr_subtype     = 253, # L2B
                        bufr_table_local_version  =  1,
                        bufr_table_master         =  0,
                        bufr_table_master_version = 15,
                        bufr_code_subcentre = 0, # L2B processing facility
                        num_subsets = num_subsets,
                        bufr_compression_flag = 0)
                        # 64=compression/0=no compression

# determine information from sections 0123 to construct the BUFR table
# names expected by the ECMWF BUFR library and create symlinks to the
# default tables if needed
bufr.setup_tables(table_b_to_use='B'+table_name,
                  table_d_to_use='D'+table_name)
bufr.register_and_expand_descriptors(template)

# retrieve the length of the expanded descriptor list
exp_descr_list_length = bufr.ktdexl
print "exp_descr_list_length = ", exp_descr_list_length

# fill the values array with some dummy varying data
num_values = num_subsets*bufr.max_nr_expanded_descriptors
values = numpy.zeros(num_values, dtype=numpy.float64) # this is the default

# note: these two must be identical for now, otherwise the
# python to fortran interface breaks down. This also ofcourse is the
# cause of the huge memory use of cvals in case num_values is large.
num_cvalues = num_values
cvals  = numpy.zeros((num_cvalues, 80), dtype=numpy.character)
cvals_index = 0

repl_counts = []

for subset in range(num_subsets):
    # note that python starts counting with 0, unlike fortran,
    # so there is no need to take (subset-1)

    print 'subset,exp_descr_list_length = ',subset,exp_descr_list_length
    i = subset*exp_descr_list_length
    
    # fill the message with some dummy data

    # fill year, month, day
    for v in [2014, 3, 19]: # fill the header
        values[i] = v+subset
        i += 1

    # fill prod_name
    txt = 'filename{}.txt'.format(subset)
    cvals[cvals_index,:] = ' '
    for ic,c in enumerate(txt):
        cvals[cvals_index,ic] = c

    #values[i] = cvals_index * 1000 + 64 # len(txt)
    values[i] = (cvals_index+1) * 1000 + len(txt)
    i += 1
    cvals_index = cvals_index + 1

    for v in [5.1+0.1*subset, 55.2-0.01*subset, 23., 45., 73., 82.]:
        bufr.verify_in_range(i,v)
        values[i] = v
        i += 1

    if use_delayed_replication:
        # set actual delayed replication repeats
        num_repl = 3 + 2*subset
        print 'num_repl = ',num_repl
        values[i] = num_repl
        i += 1
        repl_counts.append(num_repl)
        
        # fill the replicated variable
        for ii in range(num_repl):
            v = 12.+subset*0.1 + ii*0.01
            bufr.verify_in_range(i,v)
            values[i] = v
            i += 1

# do the encoding to binary format
bufr.kdata = numpy.array(repl_counts)
print 'bufr.kdata = ',bufr.kdata
bufr.encode_data(values, cvals)

print 'DEBUG: values = ', values

from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
# get an instance of the RawBUFRFile class
bf1 = RawBUFRFile()

output_bufr_file = 'test_bufr_file.bfr'
# open the file for writing
bf1.open(output_bufr_file, 'wb')
# write the encoded BUFR message
bf1.write_raw_bufr_msg(bufr.encoded_message)
# close the file
bf1.close()

##############################
# reopen the BUFR file as test
##############################

print '*'*50
from pybufr_ecmwf.bufr import BUFRReader

input_bufr_file = output_bufr_file
bob = BUFRReader(input_bufr_file, warn_about_bufr_size=False)
bob.setup_tables(table_b_to_use='B'+table_name,
                 table_d_to_use='D'+table_name)

bob.get_next_msg()
print 'num_subsets:  ', bob.get_num_subsets()

if use_delayed_replication:
    data1 = bob.get_subset_values(0)
    print 'data1 = ',data1
    data2 = bob.get_subset_values(1)
    print 'data2 = ',data2
else:
    print 'num_elements: ', bob.get_num_elements()
    print bob.get_names()
    print bob.get_units()
    data = bob.get_values_as_2d_array()
    print data.shape
    print data
    print 'bob.bufr_obj.values = '
    print bob.bufr_obj.values

textdata = bob.get_value(3,0)
print 'textdata(3,0)', textdata
textdata = bob.get_value(3,0,get_cval=True)
print 'textdata(3,0)', textdata
textdata = bob.get_values(3,get_cval=True)
print 'textdata(3,:)', textdata


bob.close()
