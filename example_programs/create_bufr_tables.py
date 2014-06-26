#!/usr/bin/env python
"""
a small example program to demonstrate how a new set of BUFR tables
can be created from scratch, using the BufrTable class.
"""

from pybufr_ecmwf.bufr_table \
     import BufrTable, Descriptor, CompositeDescriptor, FlagDefinition

def create_bufr_tables():
    #  #[
    """
    a small function to hold the actual code to create a set of BUFR tables
    """

    # bt1 = BufrTable(autolink_tablesdir = "tmp_BUFR_TABLES")
    bt1 = BufrTable()

    # explanation on the reference number:
    # F=0 indicates this is a B-table entry
    # XX indicates the class or category within the table.
    # Private/local definitions should always be between 48 and 63
    # to avoid clashing with standard WMO descriptors
    # (see WMO_BUFR_Guide_Layer3-English-only section 3.1.2.1)
    # YYY should be in the range 000 to 255, but if a standard WMO class
    # is used it should be between 192 and 255 for local use.

    #            FXXYYY
    reference = '048001'
    name = 'my test variable A' # max. 64 characters
    unit = 'm/s' # SI units are recommended here. max.
    unit_scale = 3 # the power of 10 by which the element has to be
    #              # multiplied prior to encoding, or divided after
    #              # decoding.
    unit_reference = 1250 # the number to be subtracted from the element, after
    #                       scaling (if any) and prior to encoding (or added
    #                       after decoding)
    data_width = 4 # the number of bits used to store the data, which will
    #                always be converted to an integer (using the above
    #                scaling and reference subtraction)

    # NOTE: on linux the ECMWF BUFR library is always compiled using 32-bits
    # integers, so the max. data_width is 32 and the maximum unit_reference
    # is 2147483647 (2^31-1)

    descr_048001 = Descriptor(reference, name, unit, unit_scale,
                              unit_reference, data_width)
    bt1.add_to_B_table(descr_048001)

    #                 FXXYYY
    reference = '048002'
    name = 'my test variable B' # max. 64 characters
    unit = 'kg/m' # SI units are recommended here. max.
    unit_scale = 12
    unit_reference = 3456
    data_width = 5
    descr_048002 = Descriptor(reference, name, unit, unit_scale,
                              unit_reference, data_width)
    bt1.add_to_B_table(descr_048002)

    #            FXXYYY
    reference = '048003'
    name = 'a dummy counter' # max. 64 characters
    unit = 'FLAG TABLE 048003'
    unit_scale = 0
    unit_reference = 0
    data_width = 10
    descr_048003 = Descriptor(reference, name, unit, unit_scale,
                              unit_reference, data_width)
    bt1.add_to_B_table(descr_048003)

    #            FXXYYY
    reference = '048003'
    fldef = FlagDefinition(reference)
    fldef.flag_dict[0] = 'zero'
    fldef.flag_dict[1] = 'one'
    fldef.flag_dict[2] = 'two'
    fldef.flag_dict[3] = 'a very long line to describe the number 3; '*10
    fldef.flag_dict[4] = 'four'
    fldef.flag_dict[999] = 'missing'
    bt1.table_c[int(reference)] = fldef

    reference = '348001'
    descriptor_list = [descr_048001, descr_048002]
    comment = 'a small test D entry' # not written to file
    bufr_table_set = bt1
    descr_348001 = CompositeDescriptor(reference, descriptor_list,
                                       comment, bufr_table_set)

    bt1.add_to_D_table(descr_348001)

    print '='*50
    print "B-table:"
    print '='*50
    bt1.print_B_table()
    print '='*50
    print "C-table:"
    print '='*50
    bt1.print_C_table()
    print '='*50
    print "D-table:"
    print '='*50
    bt1.print_D_table()
    print '='*50

    # define the table name without preceding 'B' or 'D' character
    # (which will be prepended by the below write method)
    table_name = '_my_test_BUFR_table.txt'
    bt1.write_tables(table_name)
    #  #]

create_bufr_tables()
# end of this test program
