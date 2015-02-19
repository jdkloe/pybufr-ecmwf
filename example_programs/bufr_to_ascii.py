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
# License: GPL v2.

#  #[ imported modules
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

def print_bufr_content1(input_bufr_file, output_fd, separator, max_msg_nr):
    #  #[ implementation 1
    """
    example implementation using the BUFRReader class
    combined with the get_values_as_2d_array method
    """

    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bob = BUFRReader(input_bufr_file, warn_about_bufr_size=False)

    msg_nr = 0
    while True:
        try:
            bob.get_next_msg()
            msg_nr += 1
        except EOFError:
            break

        # add header strings
        # print 'DEBUG: bob.msg_loaded ',bob.msg_loaded
        list_of_names = []
        list_of_units = []
        list_of_names.extend(bob.get_names())
        list_of_units.extend(bob.get_units())
        list_of_unexp_descr = bob.bufr_obj.py_unexp_descr_list

        #print('list_of_names = ',list_of_names)
        #print('list_of_units = ',list_of_units)

        if bob.msg_loaded == 1:
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

            list_of_unexp_descr_first_msg = bob.bufr_obj.py_unexp_descr_list
            #print('list_of_unexp_descr_first_msg = ',
            #      list_of_unexp_descr_first_msg)

        data = bob.get_values_as_2d_array()

        if list_of_unexp_descr != list_of_unexp_descr_first_msg:
            print '\n\n'
            print 'WARNING: it seems different types of BUFR messages'
            print 'are mixed in this BUFR file, meaning that the list of'
            print 'descriptor names and units printed on the first 2 output'
            print 'lines will not match with all lines of data.'
            print 'To prevent confusion, therefore decoding is halted'
            print 'It is recommended to first sort BUFR messages by type'
            print 'before converting them to ascii or csv.'
            print 'The example script soft_bufr_msgs.py can be used'
            print 'sort a BUFR file.'
            print '\n\n'
            print 'Detailed info:'
            print 'list_of_unexp_descr != list_of_unexp_descr_first_msg !'
            print 'list_of_unexp_descr           = ', \
                  list_of_unexp_descr
            print 'list_of_unexp_descr_first_msg = ', \
                  list_of_unexp_descr_first_msg
            sys.exit(0)

        if data.shape[0]*data.shape[1] == 0:
            print 'NO DATA FOUND! this seems an empty BUFR message !'
            continue

        for subs in range(len(data[:, 0])):
            output_fd.write(str(subs+1)+separator+
                            separator.join(str(val) for val in data[subs, :])+
                            "\n")
        print 'converted BUFR msg nr. ', msg_nr
        if (max_msg_nr > 0) and (msg_nr >= max_msg_nr):
            print 'skipping remainder of this BUFR file'
            break

    # close the file
    bob.close()
    if msg_nr == 0:
        print 'no BUFR messages found, are you sure this is a BUFR file?'
    #  #]

def print_bufr_content2(input_bufr_file, output_fd, separator, max_msg_nr):
    #  #[ implementation 2
    """
    example implementation using the BUFRReader class
    combined with the get_value method
    """

    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bob = BUFRReader(input_bufr_file, expand_flags=True)
    msg_nr = 0
    while True:
        try:
            bob.get_next_msg()
            msg_nr += 1
        except EOFError:
            break

        # add header strings
        if bob.msg_loaded == 1:
            list_of_names = bob.get_names()
            list_of_units = bob.get_units()

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

        nsubsets = bob.get_num_subsets()
        for subs in range(1, nsubsets+1):
            nelements = bob.get_num_elements()
            data_list = []
            for descr_nr in range(nelements):
                data = bob.get_value(descr_nr, subs)
                data_list.append(data)
            output_fd.write(str(subs)+separator+
                            separator.join(str(val) for val in data_list)+
                            "\n")

        print 'converted BUFR msg nr. ', msg_nr
        if (max_msg_nr > 0) and (msg_nr >= max_msg_nr):
            print 'skipping remainder of this BUFR file'
            break

    # close the file
    bob.close()
    if msg_nr == 0:
        print 'no BUFR messages found, are you sure this is a BUFR file?'
    #  #]

def print_bufr_content3(input_bufr_file, output_fd, separator, max_msg_nr):
    #  #[ implementation 3
    """
    example implementation using the BUFRInterfaceECMWF class
    """

    # get an instance of the RawBUFRFile class
    rbf = RawBUFRFile()

    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    rbf.open(input_bufr_file, 'rb')

    # extract the number of BUFR messages from the file
    num_msgs = rbf.get_num_bufr_msgs()

    # print 'num_msgs = ',num_msgs

    for msg_nr in range(1, num_msgs+1):
        encoded_message, section_sizes, section_start_locations = \
                         rbf.get_raw_bufr_msg(msg_nr)
        bufr_obj = BUFRInterfaceECMWF(encoded_message, section_sizes,
                                      section_start_locations)
        #                              verbose=True)
        bufr_obj.decode_sections_012()
        bufr_obj.setup_tables()
        # print 'num_subsets: ', bufr_obj.get_num_subsets()
        # print 'num_elements: ',bufr_obj.get_num_elements()
        # bufr_obj.decode_sections_0123()
        # bufr_obj.print_sections_0123_metadata()

        # d = '/home/jos/werk/pybufr_ecmwf_interface/'+\
        #     'BUFR_test_files/radar/bufrtables/'
        # bufr_obj.setup_tables(table_b_to_use = d+'B0000000000085011012.TXT',
         #                      table_d_to_use = d+'D0000000000085011012.TXT')
        # bufr_obj.print_sections_012()
        # bufr_obj.fill_descriptor_list()
        bufr_obj.decode_data()

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
            nelements = bufr_obj.get_num_elements()
            data_list = []
            for descr_nr in range(nelements):
                data = bufr_obj.get_value(descr_nr, subs)
                data_list.append(data)
            output_fd.write(str(subs)+separator+
                            separator.join(str(val) for val in data_list)+
                            "\n")
        print 'converted BUFR msg nr. ', msg_nr
        if (max_msg_nr > 0) and (msg_nr >= max_msg_nr):
            print 'skipping remainder of this BUFR file'
            break

    # close the BUFR file
    rbf.close()
    if num_msgs == 0:
        print 'no BUFR messages found, are you sure this is a BUFR file?'

    #  #]

def print_bufr_content4(input_bufr_file, output_fd, separator, max_msg_nr):
    #  #[ implementation 4
    """
    example implementation using the BUFRReader class
    to decode a bufr file using delayed replication.
    Since these files may have different descriptor lists
    for each subset, a different call pattern is needed.
    """

    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bob = BUFRReader(input_bufr_file, warn_about_bufr_size=False,
                     verbose=False)

    msg_nr = 0
    while True:
        try:
            bob.get_next_msg()
            msg_nr += 1
        except EOFError:
            break

        # since this eample assumes a bufr file using delayed replication
        # always request and add the header for each subset
        nsubsets = bob.get_num_subsets()
        for subs in range(1, nsubsets+1):

            # add header strings
            (list_of_names, list_of_units) = bob.get_names_and_units(subs)

            # currently not used
            # list_of_unexp_descr = bob.bufr_obj.py_unexp_descr_list

            data = bob.get_subset_values(subs)

            # print('len(list_of_names) = ', len(list_of_names))
            # print('len(list_of_units) = ', len(list_of_units))
            # print('len(data) = ', len(data))

            if numpy.shape(data)[0] == 0:
                print 'NO DATA FOUND! this seems an empty BUFR message !'
                continue

            output_fd.write('"subset nr"'+separator+
                            separator.join(list_of_names) + "\n")
            output_fd.write('""'+separator+
                            separator.join(list_of_units) + "\n")
            output_fd.write(str(subs)+separator+
                            separator.join(str(val) for val in data[:])+
                            "\n")

        print 'converted BUFR msg nr. ', msg_nr
        if (max_msg_nr > 0) and (msg_nr >= max_msg_nr):
            print 'skipping remainder of this BUFR file'
            break

    # close the file
    bob.close()
    if msg_nr == 0:
        print 'no BUFR messages found, are you sure this is a BUFR file?'
    #  #]

def usage():
    #  #[
    """ a small routine to print the options that may be used
    with this example progra,
    """
    print 'Usage: '
    print sys.argv[0] + ' [OPTIONS]'
    print ''
    print 'With [OPTIONS] being one or more of these possibilities: '
    print '-a or --ascii    selects ascii output'
    print '-c or --csv      selects csv output'
    print '-i or --infile   defines the input BUFR file to be used [required]'
    print '-o or --outfile  defines the output file to be used'
    print '                 if this option is omitted, stdout will be used'
    print '-1, -2, -3 or -4 test implementation 1, 2, 3 or 4 [default is 1]'
    print '-m or --maxmsgnr defines max number of BUFR messages to convert'
    print '-h               display this help text'
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
        short_options = 'aci:o:m:h1234'
        long_options = ['ascii', 'csv', 'infile=', 'outfile=',
                        'maxmsgnr=', 'help']
        (options, other_args) = getopt.getopt(sys.argv[1:],
                                              short_options, long_options)
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    # test prints
    #print 'options = ', options
    #print 'other_args = ', other_args

    # defaults
    output_to_ascii = True
    input_bufr_file = None
    output_file = None
    implementation_nr = 1
    max_msg_nr = -1

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
        elif (opt == '-m') or (opt == '--maxmsgnr'):
            max_msg_nr = int(value)
        else:
            print "Unhandled option: "+opt
            usage()
            sys.exit(2)

    # ensure input_bufr_file is defined
    if input_bufr_file is None:
        print "Missing input file!"
        usage()
        sys.exit(2)

    # warn about unused arguments
    if len(other_args) > 0:
        print 'WARNING: there seem to be unused arguments:'
        print other_args

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
                            separator, max_msg_nr)
    elif implementation_nr == 2:
        print_bufr_content2(input_bufr_file, output_fd,
                            separator, max_msg_nr)
    elif implementation_nr == 3:
        print_bufr_content3(input_bufr_file, output_fd,
                            separator, max_msg_nr)
    elif implementation_nr == 4:
        print_bufr_content4(input_bufr_file, output_fd,
                            separator, max_msg_nr)

    if output_file:
        # close the output file
        output_fd.close()

        if output_to_ascii:
            print "ascii output written to file " + output_file
        else:
            print "csv output written to file " + output_file

#  #]

# run the tool
main()
