#!/usr/bin/env python

"""
This is a small tool/example program intended to loop over all bufr messages
in a bufr file and extract all the data from it, which is then printed
to stdout or written to file, either in ascii or csv format.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 24-Sep-2010
#
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

#  #[ imported modules
from __future__ import print_function
import sys # operating system functions
import getopt # a simpler version of argparse, which was introduced in
              # python 2.7, and is not by default available for older versions
import numpy  # import numerical capabilities

# import the python file defining the RawBUFRFile class
from pybufr_ecmwf.bufr import BUFRReader
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF
from pybufr_ecmwf.helpers import python3

#  #]

def to_str(val):
    #  #[ a little conversion function
    #print('type(val) = ', type(val))
    if type(val) in [str, unicode]:
        return '"'+str(val)+'"'
    return str(val)
    #  #]

def print_bufr_content1(input_bufr_file, output_fd, separator,
                        max_msg_nr, expand_flags):
    #  #[ implementation 1
    """
    example implementation using the BUFRReader class
    combined with the get_values_as_2d_array method
    """

    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bufr = BUFRReader(input_bufr_file, warn_about_bufr_size=False,
                      expand_flags=expand_flags)
    msg_nr = -1
    for msg_nr, msg in enumerate(bufr):
        num_subsets = msg.get_num_subsets()
        list_of_unexp_descr = msg.get_unexp_descr_list()

        for subs, msg_or_subset_data in enumerate(msg):
            # get the actual values
            data = msg_or_subset_data.data

            if msg_nr == 0 and subs == 0:
                list_of_unexp_descr_first_msg = list_of_unexp_descr[:]

                # add header strings
                list_of_names = msg_or_subset_data.names
                list_of_units = msg_or_subset_data.units
                output_fd.write('"subset nr"'+separator)
                if list_of_names:
                    for name in list_of_names[:-1]:
                        output_fd.write('"'+name+'"'+separator)
                    name = list_of_names[-1]
                    output_fd.write('"'+name+'"\n')
                else:
                    output_fd.write('"[NO DATA]"\n')

                output_fd.write('""'+separator)
                if list_of_units:
                    for unit in list_of_units[:-1]:
                        output_fd.write('"'+unit+'"'+separator)
                    unit = list_of_units[-1]
                    output_fd.write('"'+unit+'"\n')
                else:
                    output_fd.write('"[NO DATA]"\n')

            try:
                data_is_2d = True
                if len(numpy.shape(data)) == 1:
                    data_is_2d = False

                if data_is_2d:
                    ns = numpy.shape(data)[0]
                    for subs_cnt in range(ns):
                        output_fd.write(str(subs_cnt+1)+separator+
                                        separator.join(str(val)
                                                       for val in
                                                       data[subs_cnt, :])+
                                        "\n")
                else:
                    # 1D data is returned if character values may be present
                    # in the data (in case autoget_cval or expand_flags
                    # are active)
                    # it may also happen if the message uses delayed
                    # replication and has variable lengths for the
                    # different subsets
                    subs_cnt = msg_or_subset_data.current_subset
                    output_fd.write(str(subs_cnt)+separator+
                                    separator.join(str(val)
                                                   for val in
                                                   data[:])+
                                    "\n")

            except TypeError:
                # in case of delayed replication or when character strings are
                # present (i.e. expand_flags = True) data will be returned as
                # a 1D list in stead of a 2D numpy array.
                # This generates a TypeError in the data[subs, :] indexing above
                output_fd.write(str(subs+1)+separator+
                                separator.join(str(val) for val in data[:])+
                                "\n")

        if list(list_of_unexp_descr) != list(list_of_unexp_descr_first_msg):
            print('\n\n')
            print('ERROR: it seems different types of BUFR messages')
            print('are mixed in this BUFR file, meaning that the list of')
            print('descriptor names and units printed on the first 2 output')
            print('lines will not match with all lines of data.')
            print('To prevent confusion, therefore decoding is halted')
            print('It is recommended to first sort BUFR messages by type')
            print('before converting them to ascii or csv.')
            print('The example script sort_bufr_msgs.py can be used')
            print('to sort a BUFR file.')
            print('\n\n')
            print('Detailed info:')
            print('list_of_unexp_descr != list_of_unexp_descr_first_msg !')
            print('list_of_unexp_descr           = ',
                  list_of_unexp_descr)
            print('list_of_unexp_descr_first_msg = ',
                  list_of_unexp_descr_first_msg)
            sys.exit(1)

        if numpy.shape(data)[0] == 0:
            print('NO DATA FOUND! this seems an empty BUFR message !')
            continue

        print('converted BUFR msg nr. ', msg_nr+1)
        if (max_msg_nr > 0) and (msg_nr >= max_msg_nr):
            print('skipping remainder of this BUFR file')
            break

    # close the file
    bufr.close()
    if msg_nr == -1:
        print('no BUFR messages found, are you sure this is a BUFR file?')
    #  #]

def print_bufr_content3(input_bufr_file, output_fd, separator,
                        max_msg_nr, expand_flags):
    #  #[ implementation 3
    """
    example implementation using the BUFRInterfaceECMWF class
    """
    if expand_flags:
        print('Sorry, expand_flags is not yet implemented '+
              'for example implementation 3')

    # get an instance of the RawBUFRFile class
    rbf = RawBUFRFile()

    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    rbf.open(input_bufr_file, 'rb')

    # extract the number of BUFR messages from the file
    num_msgs = rbf.get_num_bufr_msgs()

    # print('num_msgs = ',num_msgs)

    for msg_nr in range(1, num_msgs+1):
        encoded_message, section_sizes, section_start_locations = \
                         rbf.get_raw_bufr_msg(msg_nr)
        bufr_obj = BUFRInterfaceECMWF(encoded_message, section_sizes,
                                      section_start_locations)
        #                              verbose=True)
        bufr_obj.decode_sections_012()
        bufr_obj.setup_tables()
        # print('num_subsets: ', bufr_obj.get_num_subsets())
        # print('num_elements: ',bufr_obj.get_num_elements())
        # bufr_obj.decode_sections_0123()
        # bufr_obj.print_sections_0123_metadata()

        # d = '/home/jos/werk/pybufr_ecmwf_interface/'+\
        #     'BUFR_test_files/radar/bufrtables/'
        # bufr_obj.setup_tables(table_b_to_use = d+'B0000000000085011012.TXT',
         #                      table_d_to_use = d+'D0000000000085011012.TXT')
        # bufr_obj.print_sections_012()
        # bufr_obj.fill_descriptor_list()

        # do the actual decoding
        bufr_obj.decode_data()

        # needed to have the units ready, so autoget_cval will work
        bufr_obj.decode_sections_0123()

        # Create header lines from variable names and units
        if msg_nr == 1:
            list_of_names = []
            list_of_units = []
            for (cname, cunit) in zip(bufr_obj.cnames, bufr_obj.cunits):
                # glue the ndarray of characters together to form strings
                if python3:
                    cname_str = ''.join(c.decode() for c in cname).strip()
                    cunit_str = ''.join(c.decode() for c in cunit).strip()
                else:
                    cname_str = ''.join(cname).strip()
                    cunit_str = ''.join(cunit).strip()

                # cnames is a bit over dimensioned, so check for empty values
                if cname_str.strip() == '':
                    break

                # append the strings to the head list and quote them
                list_of_names.append('"'+cname_str+'"')
                list_of_units.append('"'+cunit_str+'"')

            output_fd.write('"subset nr"'+separator)
            output_fd.write(separator.join(list_of_names) + '\n')

            output_fd.write('""'+separator)
            output_fd.write(separator.join(list_of_units) + '\n')

        nsubsets = bufr_obj.get_num_subsets()
        for subs in range(1, nsubsets+1):

            # needed to have the units ready, so autoget_cval will work
            bufr_obj.fill_descriptor_list_subset(subs)

            nelements = bufr_obj.get_num_elements()
            data_list = []
            for descr_nr in range(nelements):
                data = bufr_obj.get_value(descr_nr, subs, autoget_cval=True)
                data_list.append(data)
            output_fd.write(str(subs)+separator+
                            separator.join(str(val) for val in data_list)+
                            "\n")
        print('converted BUFR msg nr. ', msg_nr)
        if (max_msg_nr > 0) and (msg_nr >= max_msg_nr):
            print('skipping remainder of this BUFR file')
            break

    # close the BUFR file
    rbf.close()
    if num_msgs == 0:
        print('no BUFR messages found, are you sure this is a BUFR file?')

    #  #]

def print_bufr_content4(input_bufr_file, output_fd, separator,
                        max_msg_nr, expand_flags, expand_strings,
                        descr_multiplier):
    #  #[ implementation 4
    """
    example implementation using the BUFRReader class
    to decode a bufr file using delayed replication.
    Since these files may have different descriptor lists
    for each subset, a different call pattern is needed.
    """

    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bufr = BUFRReader(input_bufr_file, warn_about_bufr_size=False,
                      #verbose=True, expand_flags=expand_flags,
                      verbose=False, expand_flags=expand_flags,
                      expand_strings=expand_strings,
                      descr_multiplyer=descr_multiplier)

    msg_nr = -1
    for msg_nr, msg in enumerate(bufr):
        # since this example assumes a bufr file using delayed replication
        # always request and add the header for each subset
        nsubsets = msg.get_num_subsets()
        # print('nsubsets = ', nsubsets)

        for msg_or_subs_nr, msg_or_subset_data in enumerate(msg):
            # add header strings
            list_of_names = msg_or_subset_data.names
            list_of_units = msg_or_subset_data.units
            data = msg_or_subset_data.data
            if numpy.shape(data)[0] == 0:
                print('NO DATA FOUND! this seems an empty BUFR message !')
                continue
            output_fd.write('"subset nr"'+separator+
                            separator.join(list_of_names) + "\n")
            output_fd.write('""'+separator+
                            separator.join(list_of_units) + "\n")

            # print(data.shape)
            if len(data.shape) == 1:
                # we are walking over subsets
                subs = msg_or_subs_nr
                output_fd.write(str(subs+1)+separator+
                                separator.join(to_str(val)
                                               for val in data[:])+
                                "\n")
            else:
                # we are getting a 2D array as result
                for subs in range(data.shape[0]):
                    output_fd.write(str(subs+1)+separator+
                                    separator.join(to_str(val)
                                                   for val in data[subs, :])+
                                    "\n")
                    
                
        print('converted BUFR msg nr. ', msg_nr+1)
        if (max_msg_nr >= 0) and (msg_nr >= max_msg_nr):
            print('skipping remainder of this BUFR file')
            break

    # close the file
    bufr.close()
    if msg_nr == -1:
        print('no BUFR messages found, are you sure this is a BUFR file?')
    #  #]

def print_bufr_content5(input_bufr_file, output_fd, separator,
                        max_msg_nr, expand_flags):
    #  #[ implementation 5
    """
    example implementation using the BUFRReader class
    to decode a bufr file using delayed replication.
    Since these files may have different descriptor lists
    for each subset, a different call pattern is needed.
    """

    # testcases:
    # ./example_programs/bufr_to_ascii.py -5 -c -o tmp.csv \
    #     -i ./pybufr_ecmwf/ecmwf_bufr_lib/bufrdc_000403/data/syno_1.bufr
    #
    # ./example_programs/bufr_to_ascii.py -5 -c -o tmp.csv \
    #     -i ../BUFR_test_files/synop_knmi_via_ko_janssen/MSSAEOL_00002950.b
    #

    names_to_be_selected = ['temperature', 'wind']
    names_to_be_excluded = ['minimum', 'maximum']

    write_names_and_units_just_once = True

    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bob = BUFRReader(input_bufr_file, warn_about_bufr_size=False,
                     verbose=False, expand_flags=expand_flags)

    msg_nr = 0
    not_yet_printed = True
    while True:
        try:
            bob.get_next_msg()
            msg_nr += 1
        except EOFError:
            break

        # since this example assumes a bufr file using delayed replication
        # always request and add the header for each subset
        nsubsets = bob.get_num_subsets()
        for subs in range(1, nsubsets+1):

            print('==> subset ', subs)

            # add header strings
            (list_of_names, list_of_units) = bob.get_names_and_units(subs)
            data = bob.get_subset_values(subs) #,autoget_cval=True)

            selected_names = []
            selected_units = []
            selected_values = []
            for i, name in enumerate(list_of_names):
                selected = False
                for name in names_to_be_selected:
                    if name in name.lower():
                        selected = True
                for name in names_to_be_excluded:
                    if name in name.lower():
                        selected = False

                if selected:
                    # print(' '*10,name,'=',data[i],list_of_units[i])
                    selected_names.append(list_of_names[i])
                    selected_units.append(list_of_units[i])
                    selected_values.append(data[i])

            if len(selected_values) == 0:
                print('NO DATA SELECTED for BUFR message %d and subset %d!' %
                      (msg_nr, subs))
                continue

            if write_names_and_units_just_once and not_yet_printed:
                output_fd.write('"subset nr"'+separator+
                                separator.join(selected_names) + "\n")
                output_fd.write('""'+separator+
                                separator.join(selected_units) + "\n")
                not_yet_printed = False

            output_fd.write(str(subs)+separator+
                            separator.join(str(val) for val in selected_values)+
                            "\n")

        print('='*25)
        print('converted BUFR msg nr. ', msg_nr)
        print('='*25)
        if (max_msg_nr > 0) and (msg_nr >= max_msg_nr):
            print('skipping remainder of this BUFR file')
            break

    # close the file
    bob.close()
    if msg_nr == 0:
        print('no BUFR messages found, are you sure this is a BUFR file?')
    #  #]

def usage():
    #  #[
    """ a small routine to print the options that may be used
    with this example progra,
    """
    print('Usage: ')
    print(sys.argv[0] + ' [OPTIONS]')
    print('')
    print('With [OPTIONS] being one or more of these possibilities:')
    print('-a or --ascii    selects ascii output')
    print('-c or --csv      selects csv output')
    print('-i or --infile   defines the input BUFR file to be used [required]')
    print('-o or --outfile  defines the output file to be used')
    print('                 if this option is omitted, stdout will be used')
    print('-1, -2, -3, -4 or -5 test implementation 1 upto 5 [default is 1]')
    print('-m or --maxmsgnr defines max number of BUFR messages to convert')
    print('-f or --expand_flags converts flags to text using table C')
    print('-s or --expand_strings converts CCITT IA5 entries to text')
    print('-u <n> or --descr_multiplier=<n> sets the descriptor multiplier')
    print('     value, which may help decode large messages')
    print('-h               display this help text')
    #  #]

def main():
    #  #[ define the main program
    """ define the main code for this test program as a subroutine
    to prevent the ugly pylint convention of using capital letters
    for all variables at root level.
    """
    try:
        # command line handling; the ':' and '=' note that the
        # options must have a value following it
        short_options = 'aci:o:m:h12345fsu:'
        long_options = ['ascii', 'csv', 'infile=', 'outfile=',
                        'maxmsgnr=', 'help', 'expand_flags',
                        'expand_strings', 'descr_multiplier=']
        (options, other_args) = getopt.getopt(sys.argv[1:],
                                              short_options, long_options)
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err)) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    # test prints
    #print('options = ', options)
    #print('other_args = ', other_args)

    # defaults
    output_to_ascii = True
    input_bufr_file = None
    output_file = None
    implementation_nr = 1
    max_msg_nr = -1
    expand_flags = False
    expand_strings = False
    descr_multiplier = 10
    for (opt, value) in options:
        if   (opt == '-h') or (opt == '--help'):
            usage()
        elif (opt == '-a') or (opt == '--ascii'):
            output_to_ascii = True
        elif (opt == '-c') or (opt == '--csv'):
            output_to_ascii = False # implies csv
        elif (opt == '-i') or (opt == '--infile'):
            input_bufr_file = value
        elif (opt == '-o') or (opt == '--outfile'):
            output_file = value
        elif opt == '-1':
            implementation_nr = 1
        elif opt == '-2':
            implementation_nr = 2
        elif opt == '-3':
            implementation_nr = 3
        elif opt == '-4':
            implementation_nr = 4
        elif opt == '-5':
            implementation_nr = 5
        elif (opt == '-m') or (opt == '--maxmsgnr'):
            max_msg_nr = int(value)
        elif (opt == '-f') or (opt == '--expand_flags'):
            expand_flags = True
        elif (opt == '-s') or (opt == '--expand_strings'):
            expand_strings = True
        elif (opt == '-u') or (opt == '--descr_multiplier'):
            descr_multiplier = int(value)
        else:
            print("Unhandled option: "+opt)
            usage()
            sys.exit(2)

    # ensure input_bufr_file is defined
    if input_bufr_file is None:
        print("Missing input file!")
        usage()
        sys.exit(2)

    # warn about unused arguments
    if len(other_args) > 0:
        print('WARNING: there seem to be unused arguments:')
        print(other_args)

    # Open the output file
    if output_file:
        output_fd = open(output_file, "w")
    else:
        output_fd = sys.stdout

    if output_to_ascii:
        separator = ' ' # ascii case
    else:
        separator = ',' # csv case

    if implementation_nr == 1:
        print_bufr_content1(input_bufr_file, output_fd,
                            separator, max_msg_nr, expand_flags)
    elif implementation_nr == 2:
        print_bufr_content1(input_bufr_file, output_fd,
                            separator, max_msg_nr, expand_flags)
    elif implementation_nr == 3:
        print_bufr_content3(input_bufr_file, output_fd,
                            separator, max_msg_nr, expand_flags)
    elif implementation_nr == 4:
        print_bufr_content4(input_bufr_file, output_fd,
                            separator, max_msg_nr, expand_flags,
                            expand_strings, descr_multiplier)
    elif implementation_nr == 5:
        print_bufr_content5(input_bufr_file, output_fd,
                            separator, max_msg_nr, expand_flags)
    else:
        print('implementation nr. %d is not available...' %
              implementation_nr)

    if output_file:
        # close the output file
        output_fd.close()

        if output_to_ascii:
            print("ascii output written to file " + output_file)
        else:
            print("csv output written to file " + output_file)

#  #]

# run the tool
if __name__ == '__main__':
    main()
