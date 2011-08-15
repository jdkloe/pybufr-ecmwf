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

# import the python file defining the RawBUFRFile class
from pybufr_ecmwf.bufr import BUFRReader
from pybufr_ecmwf.raw_bufr_file import RawBUFRFile
from pybufr_ecmwf.bufr_interface_ecmwf import BUFRInterfaceECMWF

#  #]

def print_bufr_content1(input_bufr_file, output_fd, separator):
    #  #[ implementation 1
    """
    example implementation using the BUFRReader class
    combined with the get_values_as_2d_array method
    """
    
    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bob = BUFRReader(input_bufr_file)
    
    while True:
        try:
            bob.get_next_msg()
        except EOFError:
            break

        # add header strings
        if bob.msg_loaded == 1:
            list_of_names = ['']
            list_of_units = ['']
            list_of_names.extend(bob.get_names())
            list_of_units.extend(bob.get_units())
            output_fd.write(separator.join(list_of_names) + "\n")
            output_fd.write(separator.join(list_of_units) + "\n")
        
        data = bob.get_values_as_2d_array()
        for subs in range(len(data[:, 0])):
            output_fd.write(str(subs)+separator+
                            separator.join(str(val) for val in data[subs, :])+
                            "\n")
        
    # close the file
    bob.close()
    #  #]

def print_bufr_content2(input_bufr_file, output_fd, separator):
    #  #[ implementation 2
    """
    example implementation using the BUFRReader class
    combined with the get_value method
    """
    
    # get an instance of the BUFR class
    # which automatically opens the file for reading and decodes it
    bob = BUFRReader(input_bufr_file)
    
    while True:
        try:
            bob.get_next_msg()
        except EOFError:
            break
        
        # add header strings
        if bob.msg_loaded == 1:
            list_of_names = ['']
            list_of_units = ['']
            list_of_names.extend(bob.get_names())
            list_of_units.extend(bob.get_units())
            output_fd.write(separator.join(list_of_names) + "\n")
            output_fd.write(separator.join(list_of_units) + "\n")

        nsubsets = bob.get_num_subsets()
        for subs in range(nsubsets):
            nelements = bob.get_num_elements()
            data_list = []
            for descr_nr in range(nelements):
                data = bob.get_value(descr_nr, subs)
                data_list.append(data)
            output_fd.write(str(subs)+separator+
                            separator.join(str(val) for val in data_list)+
                            "\n")

    # close the file
    bob.close()
    #  #]

def print_bufr_content3(input_bufr_file, output_fd, separator):
    #  #[ implementation 3
    """
    example implementation using the BUFRInterfaceECMWF class
    """

    # get an instance of the RawBUFRFile class
    rbf = RawBUFRFile()
    
    # open the file for reading, count nr of BUFR messages in it
    # and store its content in memory, together with
    # an array of pointers to the start and end of each BUFR message
    rbf.open(input_bufr_file, 'r')
    
    # extract the number of BUFR messages from the file
    num_msgs = rbf.get_num_bufr_msgs()

    for msg_nr in range(1, num_msgs+1):
        encoded_message, section_sizes, section_start_locations = \
                         rbf.get_raw_bufr_msg(msg_nr)
        bufr_obj = BUFRInterfaceECMWF(encoded_message, section_sizes,
                                      section_start_locations)
        bufr_obj.decode_sections_012()
        bufr_obj.setup_tables()
        bufr_obj.decode_data()

        # Create header lines from variable names and units
        if msg_nr == 1:
            list_of_names = ['']
            list_of_units = ['']
            for (cname, cunit) in zip(bufr_obj.cnames, bufr_obj.cunits):
                # glue the ndarray of characters together to form strings
                cname_str = "".join(cname).strip()
                cunit_str = "".join(cunit).strip()
                # append the strings to the head list and quote them
                list_of_names.append('"'+cname_str+'"')
                list_of_units.append('"'+cunit_str+'"')

            output_fd.write(separator.join(list_of_names) + "\n")
            output_fd.write(separator.join(list_of_units) + "\n")

        nsubsets = bufr_obj.get_num_subsets()
        for subs in range(nsubsets):
            nelements = bufr_obj.get_num_elements()
            data_list = []
            for descr_nr in range(nelements):
                data = bufr_obj.get_value(descr_nr, subs)
                data_list.append(data)
            output_fd.write(str(subs)+separator+
                            separator.join(str(val) for val in data_list)+
                            "\n")
    
    # close the BUFR file
    rbf.close()

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
    print '-a or --ascii   selects ascii output'
    print '-c or --csv     selects csv output'
    print '-i or --infile  defines the input BUFR file to be used [required]'
    print '-o or --outfile defines the output file to be used'
    print '                if this option is omitted, stdout will be used'
    print '-1 or -2 or -3  test implementation 1, 2 or 3 [default is 1]'
    print '-h              display this help text'
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
        short_options = 'aci:o:h123'
        long_options  = ['ascii', 'csv', 'infile=', 'outfile=', 'help']
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
    output_to_ascii   = True
    input_bufr_file   = None
    output_file       = None
    implementation_nr = 1
    
    for (opt, value) in options:
        if   ( (opt == '-h') or (opt == '--help') ):
            usage()
        elif ( (opt == '-a') or (opt == '--ascii') ):
            output_to_ascii = True
        elif ( (opt == '-c') or (opt == '--csv') ):
            output_to_ascii = False # implies csv
        elif ( (opt == '-i') or (opt == '--infile') ):
            input_bufr_file = value
        elif ( (opt == '-o') or (opt == '--outfile') ):
            output_file = value
        elif (opt == '-1'):
            implementation_nr = 1
        elif (opt == '-2'):
            implementation_nr = 2
        elif (opt == '-3'):
            implementation_nr = 3
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

    if   (implementation_nr == 1):
        print_bufr_content1(input_bufr_file, output_fd, separator)
    elif (implementation_nr == 2):
        print_bufr_content2(input_bufr_file, output_fd, separator)
    elif (implementation_nr == 3):        
        print_bufr_content3(input_bufr_file, output_fd, separator)

    if output_file:
        # close the output file
        output_fd.close()

        if output_to_ascii:
            print("ascii output written to file " + output_file)
        else:
            print("csv output written to file " + output_file)

#  #]

# run the tool
main()
