#!/usr/bin/env python

"""
a module to allow easier handling of BUFR files and messages
by providing several helper classes. This module defines the
following classes for general use:
* BUFRReader: for reading and decoding BUFR messages from a file
*
"""

#  #[ documentation
#
# This module implements a more pythonic interface layer
# around pybufr_ecmwf and is intended to make use of the BUFR
# file format easier and more intuitive for people used to python
# rather than fortran.
#
# Note about the use of the "#  #[" and "#  #]" comments:
#   these are folding marks for my favorite editor, emacs, combined with its
#   folding mode
#   (see http://www.emacswiki.org/emacs/FoldingMode for more details)
# Please do not remove them.
#
# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI (www.knmi.nl), Initial version 04-Feb-2010    
#
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

#  #]
#  #[ imported modules
from __future__ import (absolute_import, division,
                        print_function) #, unicode_literals)
import sys # os
import numpy   # array functionality
from .raw_bufr_file import RawBUFRFile
from .bufr_interface_ecmwf import BUFRInterfaceECMWF
from .helpers import python3
from .custom_exceptions import \
     (NoMsgLoadedError, CannotExpandFlagsError,
      IncorrectUsageError, NotYetImplementedError)
from pybufr_ecmwf.bufr_template import BufrTemplate
#  #]

def check_range(p, value):
    #  #[ ensure data can be packed
    in_range = True
    if value < p['min_allowed_value']:
        in_range = False
    if value > p['max_allowed_value']:
        in_range = False

    if not in_range:
        errtxt = ('current value {0} cannot be packed in this field. '.
                  format(value)+
                  'Allowed range is {0} upto {1}.'.
                  format(p['min_allowed_value'],
                         p['max_allowed_value']))
        raise ValueError(errtxt)
    #  #]

class BUFRMessage_R:
    #  #[ bufr msg class for reading
    """
    a class that implements iteration over the data in
    a given bufr message for reading
    """
    def __init__(self, raw_msg,
                 section_sizes, section_start_locations,
                 expand_flags, msg_index, verbose,
                 table_b_to_use, table_c_to_use,
                 table_d_to_use, tables_dir):
        #  #[ initialise and decode
        ''' delegate the actual work to BUFRInterfaceECMWF '''
        self._bufr_obj = BUFRInterfaceECMWF(raw_msg,
                                            section_sizes,
                                            section_start_locations,
                                            expand_flags=expand_flags,
                                            verbose=verbose)
        self._bufr_obj.decode_sections_012()
        self._bufr_obj.setup_tables(table_b_to_use, table_c_to_use,
                                    table_d_to_use, tables_dir)
        self._bufr_obj.decode_data()
        self._bufr_obj.decode_sections_0123()
        self._bufr_obj.fill_descriptor_list_subset(subset=1)
        self.msg_index = msg_index
        self.expand_flags = expand_flags
        self.current_subset = None
        #  #]
    def get_num_subsets(self):
        #  #[
        """
        request the number of subsets in the current BUFR message
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError
        return self._bufr_obj.get_num_subsets()
        #  #]
    def get_num_elements(self):
        #  #[
        """
        request the number of elements (descriptors) in the current subset
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        return self._bufr_obj.get_num_elements()
        #  #]
    def get_value(self, descr_nr, subset_nr, autoget_cval=False):
        #  #[
        """
        request a value for a given subset and descriptor number
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        val = self._bufr_obj.get_value(descr_nr, subset_nr, autoget_cval)
        return val
        #  #]
    def get_values(self, descr_nr, autoget_cval=False):
        #  #[
        """
        request an array of values containing the values
        for a given descriptor number for all subsets
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        self._bufr_obj.delayed_repl_check_for_incorrect_use()

        vals = self._bufr_obj.get_values(descr_nr, autoget_cval)

        return vals
        #  #]
    def get_subset_values(self, subset_nr , autoget_cval=False):
         #  #[
        """
        request an array of values containing the values
        for a given subset for this bufr message
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        # needed to have the units ready, so autoget_cval will work
        self._bufr_obj.fill_descriptor_list_subset(subset_nr)

        vals = self._bufr_obj.get_subset_values(subset_nr, autoget_cval)

        return vals
        #  #]
    def get_values_as_2d_array(self,autoget_cval=False):
        #  #[
        """
        a convenience method to allow retrieving all data in
        a bufr message in the form of a 2D array. This first index
        runs over the subsets, the second over the descriptors.
        """
        if (self.msg_index == -1):
            txt = 'Sorry, no BUFR messages available'
            raise NoMsgLoadedError(txt)

        #if self.expand_flags:
        #    errtxt = ('ERROR: get_values_as_2d_array only returns numeric '+
        #              'results and cannot be used together with the '+
        #              'expand_flags option.'+
        #              'You will need to extract one element of one row of '+
        #              'elements at a time in this case.')
        #    raise CannotExpandFlagsError(errtxt)
            
        self._bufr_obj.delayed_repl_check_for_incorrect_use()

        num_subsets  = self._bufr_obj.get_num_subsets()
        num_elements = self._bufr_obj.get_num_elements()

        #print('DEBUG: num_subsets = ', num_subsets)
        #print('DEBUG: num_elements = ', num_elements)

        # The BUFR reader reads an array that is actually larger than the data.
        # Here we reshape the data to an array of this bigger size and then
        # slice it down to the actual size of the data. reshape data into 2D
        # array of size that was actually read
        factor = int(len(self._bufr_obj.values) / self._bufr_obj.actual_kelem)
        result = self._bufr_obj.values.reshape(
            (factor, self._bufr_obj.actual_kelem))[:num_subsets, :num_elements]

        # autoget_cval option not functional yet
        # for data retrieval in a 2D numpy array
        # this is delegated to self.get_subset_values()
        # in data_iterator below
        
        return result
        #  #]
    def get_names_and_units(self, subset=1):
        #  #[ request name and unit of each descriptor for the given subset
        '''
        wrapper around  self._bufr_obj.get_names_and_units
        '''
        if (self.msg_index == -1):
            raise NoMsgLoadedError
        
        (list_of_names, list_of_units) = \
                        self._bufr_obj.get_names_and_units(subset)

        return (list_of_names, list_of_units)
        #  #]
    def get_names(self, subset=1):
        #  #[ request name of each descriptor for the given subset
        '''
        wrapper around  self._bufr_obj.get_names_and_units
        '''
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        (list_of_names, list_of_units) = \
                        self._bufr_obj.get_names_and_units(subset)
        return list_of_names
        #  #]
    def get_units(self, subset=1):
        #  #[ request unit of each descriptor for the given subset
        '''
        wrapper around  self._bufr_obj.get_names_and_units
        '''
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        (list_of_names, list_of_units) = \
                        self._bufr_obj.get_names_and_units(subset)

        return list_of_units
        #  #]        
    def get_unexp_descr_list(self):
        #  #[ get unexpanded descfriptor list
        '''
        wrapper around  self._bufr_obj.py_unexp_descr_list
        '''
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        list_of_unexp_descr = self._bufr_obj.py_unexp_descr_list
        return list_of_unexp_descr
        #  #]
    def data_iterator(self):
        #  #[ define iteration for reading
        """
        Iterate over the data from a given BUFR message.
        If the message can be represented as a 2D array then
        the data will be returned as such. Otherwise 1D arrays
        will be returned.

        Yields
        ------
        data : numpy.ndarray
            Array of the data in the BUFR message. Can be a 2D array or a
            1D array.
        names: list
            List of variable names. If data is a 2D array these are the names
            of the variables along the second axis of the array. So if the
            data array has a shape of e.g. (361 ,44) there will be 44 elements
            in this list.
        units: list
            The units of each variable in the names list. Same length as the
            names list.
        """
        walk_over_subsets = False
        if self.expand_flags:
            walk_over_subsets = True

        if not walk_over_subsets:
            try:
                values = self.get_values_as_2d_array()
                names, units = self.get_names_and_units()
                # store the results as attributes of self and yield self
                self.data = values
                self.names = names
                self.units = units
                yield self
            except IncorrectUsageError:
                walk_over_subsets = True

        if walk_over_subsets:
            # no 2D representation possible. Return 1D arrays instead. If
            # there are multiple subsets yield them one after the other.
            nsubsets = self.get_num_subsets()
            for subs in range(1, nsubsets+1):
                self.current_subset = subs
                names, units = self.get_names_and_units(subs)
                values = self.get_subset_values(subs)
                self.data = values
                self.names = names
                self.units = units
                yield self
        #  #]
    def __iter__(self):
        #  #[ return the iterator
        '''returns the above defined iterator'''
        return self.data_iterator()
        #  #]
    #def __getattr__(self, key):
    #    #print('inside __getattr__: key = ', key)
    #    #sys.exit(1)
    #    if key == 'data':
    #        # try to get the data as 2D array
    #        ...
    
    #  #]

# todo: see how much of this class can be added/merged into
#       the above BUFRMessage class
class BUFRMessage_W:
    #  #[ bufr msg class for writing
    """
    a class that implements iteration over the data in
    a given bufr message for reading
    """    
    def __init__(self, parent, num_subsets=1, verbose=False,
                 do_range_check=False):
        #  #[ initialise a message for writing
        self.parent = parent
        self.num_subsets = num_subsets
        self.verbose = verbose
        self.do_range_check = do_range_check
        self.bufr_obj = BUFRInterfaceECMWF(verbose=verbose)
        # fill sections 0, 1, 2 and 3 with default values
        self.bufr_obj.fill_sections_0123(
            bufr_code_centre =   0, # use official WMO tables
            bufr_obstype     =   3, # sounding
            bufr_subtype     = 253, # L2B
            bufr_table_local_version  =  0, # dont use local tables
            bufr_table_master         =  0,
            bufr_table_master_version = 26, # use latest WMO version
            bufr_code_subcentre = 0, # L2B processing facility
            num_subsets = num_subsets,
            bufr_compression_flag = 64)
            # 64=compression/0=no compression

        #table_name = 'default'
        # self.bufr_obj.setup_tables(table_b_to_use='B'+table_name,
        #                            table_d_to_use='D'+table_name)

        # use information from sections 0123 to construct the BUFR table
        # names expected by the ECMWF BUFR library
        self.bufr_obj.setup_tables()
        #  #]
    def set_template(self, *args):
        #  #[ set the template
        self.template = BufrTemplate()

        # todo: see if it is possible to also allow
        # a bufr_template instance as input
        for descr in args:
            # inputs may be integer, string or a Descriptor instance
            # print('adding descriptor: ', descr, ' of type ', type(descr))
            self.template.add_descriptor(descr)
        
        self.bufr_obj.register_and_expand_descriptors(self.template)

        # retrieve the length of the expanded descriptor list
        exp_descr_list_length = self.bufr_obj.ktdexl
        if self.verbose:
            print("exp_descr_list_length = ", exp_descr_list_length)
        # ensure zeros at the end are removed, so explicitely
        # define the end of the slice
        exp_descr_list = self.bufr_obj.ktdexp[:exp_descr_list_length]
        if self.verbose:
            print("exp_descr_list = ",  self.bufr_obj.ktdexp)
        self.num_fields = exp_descr_list_length

        # ensure all descriptors are instances of bufr_table.Descriptor
        self.normalised_descriptor_list = \
            self.bufr_obj.bt.normalise_descriptor_list(exp_descr_list)

        # allocate the needed values and cvalues arrays

        self.num_values = self.num_subsets*self.num_fields
        self.values = numpy.zeros(self.num_values, dtype=numpy.float64)
        # note: float64 is the default but it doesnt hurt to be explicit
        if self.verbose:
            print("self.num_values = ", self.num_values)
        
        # note: these two must be identical for now, otherwise the
        # python to fortran interface breaks down. This also ofcourse is the
        # cause of the huge memory use of cvals in case num_values is large.
        self.num_cvalues = self.num_values
        self.cvals = numpy.zeros((self.num_cvalues, 80), dtype=numpy.character)
        self.cvals_index = 0

        # dont use this, it is not compatible to python 2.6:
        # from collections import OrderedDict

        # since I cannot use an orderddict due to missing compatibility
        # to python 2.6, I'll use an additional (ordered) list of keys
        
        # fill an ordered dict with field properties for convenience
        self.field_properties = {}
        self.field_properties_keys = []
        for idx, descr in enumerate(self.normalised_descriptor_list):
            (min_allowed_value,
             max_allowed_value, step) = descr.get_min_max_step()
            p = {'index':idx,
                 'name':descr.name,
                 'min_allowed_value':min_allowed_value,
                 'max_allowed_value':max_allowed_value,
                 'step':step}
            self.field_properties[descr.reference] = p
            self.field_properties_keys.append(descr.reference)
        #  #]
    def copy_template_from_bufr_msg(self, msg):
        pass
    def get_field_names(self):
        #  #[ request field names
        names = []
        for key in self.field_properties_keys:
            p = self.field_properties[key]
            names.append(p['name'])
        return names
        #  #]
    def add_subset_data(self, data):
        pass
    def write_msg_to_file(self):
        #  #[ write out the current message
        # do the encoding to binary format
        self.bufr_obj.encode_data(self.values,
                                  self.cvals)

        # check if file was properly opened
        if not self.parent.is_open:
            errtxt = 'please open the bufr file before writing data to it!'
            raise IncorrectUsageError(errtxt)
        
        # write the encoded BUFR message
        self.parent.raw_bf.write_raw_bufr_msg(self.bufr_obj.encoded_message)
        #  #]
    def str_get_index_to_use(self, this_key):
        #  #[ convert string input for key to index in exp. descr. list
        # see if an index is provided
        index = -1
        if '[' in this_key:
            parts = this_key.split('[')
            this_key = parts[0]
            index_str = parts[1][:-1]
            index = int(index_str)
            
        possible_matches = []
        names_of_possible_matches = []
        try:
            reference = int(this_key)
            fraction = float(this_key)-reference
            
            p = self.field_properties[reference]
            descr_name = p['name']
        except:
            # this appears to be not an integer number, so assume
            # (part of) the name is given
            descr_name = this_key

        for key in self.field_properties_keys:
            p = self.field_properties[key]
            if descr_name in p['name']:
                possible_matches.append(key)
                names_of_possible_matches.append(p['name'])

        # print('possible matches for key: ', possible_matches)
        if len(possible_matches) == 1:
            #  ok, proper location found
            key = possible_matches[0]
            p = self.field_properties[key]
            index_to_use = p['index']
            # print('filling row:', p)
        elif len(possible_matches) == 0:
            errtxt = ('ERROR: the current BUFRmessage does not contain any '+
                      'fields that have [{}] in their name.'.format(this_key))
            raise IncorrectUsageError(errtxt)
        elif index >= 0:
            #  ok, proper location found since an index was supplied
            try:
                key = possible_matches[index]
            except:
                # invalid index
                errtxt = ('ERROR: the index on the requested descriptor '+
                          'is out of the possible range. '+
                          'Only {0} '.format(len(possible_matches))+
                          'possible matches are present in this template. '+
                          'while the requested index was {} '.format(index)+
                          'for key {0}.'.format(this_key))
                raise IncorrectUsageError(errtxt)
            
            p = self.field_properties[key]
            index_to_use = p['index']
            # print('filling row:', p)
        else:
            errtxt = ('ERROR: the current BUFRmessage has multiple '+
                      'fields that have [{}] in their name.'.format(this_key)+
                      ' Please add an index to indicate which '+
                      'field should be used. Key [{}] matches with {}.'.
                      format(this_key, names_of_possible_matches))
            raise IncorrectUsageError(errtxt)

        return index_to_use, p
        #  #]
    def num_get_index_to_use(self, this_key):
        #  #[ get properties for direct index
        # print('self.field_properties_keys = ', self.field_properties_keys)
        # print('self.field_properties = ', self.field_properties)
        index_to_use = this_key
        reference = self.field_properties_keys[this_key]
        p = self.field_properties[reference]
        return index_to_use, p
        #  #]
    def __setitem__(self, this_key, this_value):
        #  #[ allow addition of date with dict like interface
        # print('searching for: ', this_key)

        if type(this_key) is int:
            # a direct index to the expanded list of descriptors
            # should be given in this case
            index_to_use, p = self.num_get_index_to_use(this_key)
        elif type(this_key) is str:
            index_to_use, p = self.str_get_index_to_use(this_key)
        else:
            errtxt = 'key has unknown type: {}'.format(type(this_key))
            raise IncorrectUsageError(errtxt)
        
        # check length of input (scalar or array?)
        try:
            n = len(this_value)
        except:
            n = 1

        if n != 1:
            if n != self.num_subsets:
                errtxt = ('Please provide an array of size num_subsets! '+
                          'Current array has size {0} '.format(n)+
                          'but num_subsets is {0}'.format(self.num_subsets))
                raise IncorrectUsageError(errtxt)

        # optional, since this may make the code slower
        if self.do_range_check:
            if n == 1:
                check_range(p, this_value)
            else:
                for val in this_value[:]:
                    check_range(p, val)
            
        # fill the requested row with data
        for subset in range(self.num_subsets):
            i = subset*self.num_fields
            j = i + index_to_use
            if n==1:
                self.values[j] = this_value
            else:
                self.values[j] = this_value[subset]
        #  #]
    #  #]

class BUFRReaderBUFRDC:
    #  #[ bufrdc reader class
    """
    a class that combines reading and decoding of a BUFR file
    to allow easier reading and usage of BUFR files
    It implements a file like interface for
    combined reading and decoding and allows iteration
    over the messages in this file.
    """
    def __init__(self, input_bufr_file, warn_about_bufr_size=True,
                 expand_flags=False, verbose=False):
        #  #[
        # get an instance of the RawBUFRFile class
        self._rbf = RawBUFRFile(warn_about_bufr_size=warn_about_bufr_size)

        self.verbose = verbose
        
        # open the file for reading, count nr of BUFR messages in it
        # and store its content in memory, together with
        # an array of pointers to the start and end of each BUFR message
        self._rbf.open(input_bufr_file, 'rb')
    
        # extract the number of BUFR messages from the file
        self.num_msgs = self._rbf.get_num_bufr_msgs()

        # keep track of which bufr message has been loaded and
        # decoded from this file
        self.msg_index = -1
        self._bufr_obj = None

        # allow manual choice of tables
        self.table_b_to_use = None
        self.table_c_to_use = None
        self.table_d_to_use = None
        self.tables_dir = None

        # expand flags to text
        self.expand_flags = expand_flags
        
        #  #]
    def setup_tables(self,table_b_to_use=None, table_c_to_use=None,
                     table_d_to_use=None, tables_dir=None):
        #  #[
        """
        allow manual choice of bufr tables
        """
        self.table_b_to_use = table_b_to_use
        self.table_c_to_use = table_c_to_use
        self.table_d_to_use = table_d_to_use
        self.tables_dir = tables_dir
        #  #]
    def get_next_msg(self):
        #  #[
        """
        step to the next BUFR message in the open file
        """
        (raw_msg, section_sizes, section_start_locations) = \
                 self._rbf.get_next_raw_bufr_msg()
        msg_index = self._rbf.last_used_msg
        self.msg = BUFRMessage_R(raw_msg,
                                 section_sizes, section_start_locations,
                                 self.expand_flags, msg_index, self.verbose,
                                 self.table_b_to_use, self.table_c_to_use,
                                 self.table_d_to_use, self.tables_dir)

        self.msg_index = msg_index
        #  #]

    def messages(self):
        #  #[ iterate over messages for reading
        """
        Iterate over BUFR messages. If the message can be represented as a
        2D array then the data will be returned as such. Otherwise 1D arrays
        will be returned.

        Yields
        ------
        msg:
            An instance of BUFRMessage that gives access
            to the actual data, names and units for the
            current bufr message (if it can be represented as 2D array)
            or for the current subset of the current bufr message
            in which case it will be a 1D array.
        """
        for i in numpy.arange(self.num_msgs) + 1:
            self.get_next_msg()
            yield self.msg
        #  #]
    def __iter__(self):
        #  #[ return the above iterator
        return self.messages()
        #  #]
    def __enter__(self):
        #  #[ enters the 'with' context
        return self
        #  #]
    def __exit__(self, exc, val, trace):
        #  #[ exits the 'with' context
        self.close()
        #  #]
    def close(self):
        #  #[ close the file
        """
        close the file object
        """
        self._rbf.close()
        #  #]
    #  #]

class BUFRWriterBUFRDC:
    #  #[ bufrdc writer class
    """
    a class that makes it easier do encode a BUFR message
    and to create BUFR files
    It implements a file like interface for user convenience.
    """
    def __init__(self, verbose=False):
        self.verbose = verbose
    def add_new_msg(self, num_subsets=1):
        #  #[ initialise a new bufr message
        self.msg = BUFRMessage_W(parent=self, num_subsets=num_subsets,
                                 verbose=self.verbose)
        return self.msg
        #  #]
    def open(self, filename):
        #  #[ open a new bufr file for writing
        # get an instance of the RawBUFRFile class
        self.raw_bf = RawBUFRFile()

        # open the file for writing
        self.raw_bf.open(filename, 'wb')
        self.is_open = True
        #  #]
    def close(self):
        #  #[ close the file
        self.raw_bf.close()
        self.is_open = False
        #  #]
    #  #]

# this class implements combined reading and decoding
# based on the new eccodes library (still in beta version!)
try:
    import eccodes, string
    eccodes_available = True
except:
    eccodes_available = False

# eccodes is not functional yet, so deactivate it for now
#eccodes_available=False

class BUFRReaderECCODES:
    #  #[
    """
    a class that combines reading and decoding of a BUFR file
    to allow easier reading and usage of BUFR files
    """
    def __init__(self, input_bufr_file, warn_about_bufr_size=True,
                 expand_flags=False, verbose=False):
        #  #[
        print('opening BUFR file: ', input_bufr_file)

        # open the BUFR file
        self.fd = open(input_bufr_file,'r')

        # extract the number of BUFR messages from the file
        self.num_msgs =  eccodes.codes_count_in_file(self.fd)

        print('self.num_msgs = ', self.num_msgs)

        # not yet used
        self.verbose = verbose
    
        # keep track of which bufr message has been loaded and
        # decoded from this file
        self.msg_index = -1
        self.bufr_id = -1

        # allow manual choice of tables
        #self.table_b_to_use = None
        #self.table_c_to_use = None
        #self.table_d_to_use = None
        self.tables_dir = None

        # expand flags to text
        self.expand_flags = expand_flags
        
        #  #]
    def setup_tables(self,table_b_to_use=None, table_c_to_use=None,
                     table_d_to_use=None, tables_dir=None):
        #  #[
        """
        allow manual choice of bufr tables
        """
        #self.table_b_to_use = table_b_to_use
        #self.table_c_to_use = table_c_to_use
        #self.table_d_to_use = table_d_to_use
        self.tables_dir = tables_dir
        #  #]
    def get_next_msg(self):
        #  #[
        """
        step to the next BUFR message in the open file
        """
        print('getting next message')
        
        if self.msg_index < self.num_msgs:
            self.msg_index += 1
            # get an instance of the eccodes bufr class
            self.bufr_id = eccodes.codes_bufr_new_from_file(self.fd)
            print('self.bufr_id = ', self.bufr_id)
            if self.bufr_id is None:
                raise StopIteration
        else:
            self.msg_index = -1
            self.bufr_id = -1
            raise StopIteration

        # unpack this bufr message
        eccodes.codes_set(self.bufr_id,'unpack',1)

        # possibly extract descriptor list here
        # self._bufr_obj.fill_descriptor_list_subset(subset=1)
        
        #  #]
    def get_num_subsets(self):
        #  #[
        """
        request the number of subsets in the current BUFR message
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        return eccodes.codes_get(self.bufr_id,"numberOfSubsets")
        #  #]
    def get_num_elements(self):
        #  #[
        """
        request the number of elements (descriptors) in the current subset
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        fieldnames = eccodes.codes_get_array(self.bufr_id, 'expandedNames')

        # other possibilities are:
        # 'expandedAbbreviations'
        # 'expandedNames'
        # 'expandedUnits'
        # 'expandedOriginalScales'
        # 'expandedOriginalReferences'
        # 'expandedOriginalWidths'
        
        return len(fieldnames)
        #  #]
    def get_value(self, descr_nr, subset_nr, autoget_cval=False):
        #  #[
        """
        request a value for a given subset and descriptor number
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        print('getting value for subset ', subset_nr)
        values = self.get_values(descr_nr, autoget_cval)
        val = values[subset_nr-1]
        return val
        #  #]
    def get_values(self, descr_nr, autoget_cval=False):
        #  #[
        """
        request an array of values containing the values
        for a given descriptor number for all subsets
        NOTE: this may not work for templates using delayed replication.
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        list_of_names = self._get_abbr_names()
        keyname = list_of_names[descr_nr]
        print('keyname: ', keyname)
        s = eccodes.codes_get_size(self.bufr_id,keyname)
        t = eccodes.codes_get_native_type(self.bufr_id, keyname)
        print('key:', keyname, 'size = ', s, 'type = ', t)

        if s==1: # or t==str:
            # values = eccodes.codes_get_string(bufr_id, keyname)
            values = [eccodes.codes_get(self.bufr_id, keyname),]
        else:
            values = eccodes.codes_get_array(self.bufr_id, keyname)

        return values
        #  #]
    def get_subset_values(self, subset_nr , autoget_cval=False):
         #  #[
        """
        request an array of values containing the values
        for a given subset for this bufr message
        """
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        data = []
        field_names = self._get_abbr_names(subset_nr)
        print('field_names = ', field_names)
        print('DEBUG: names = ',self.get_names(subset_nr))
        for field in field_names:
            if field[0] in string.digits:
                print('cannot get data for field: ',field)
                continue
            print('trying field name: ', field)
            s = eccodes.codes_get_size(self.bufr_id,field)
            if s==1:
                value = eccodes.codes_get(self.bufr_id,field)
                data.append(value)
            else:
                values = eccodes.codes_get_array(self.bufr_id,field)
                data.append(values[subset_nr])

        return data
        #  #]
    def get_values_as_2d_array(self,autoget_cval=False):
        #  #[
        """
        a convenience method to allow retrieving all data in
        a bufr message in the form of a 2D array. This first index
        runs over the subsets, the second over the descriptors.
        """
        if (self.msg_index == -1):
            txt = 'Sorry, no BUFR messages available'
            raise NoMsgLoadedError(txt)

        if self.expand_flags:
            errtxt = ('ERROR: get_values_as_2d_array only returns numeric '+
                      'results and cannot be used together with the '+
                      'expand_flags option.'+
                      'You will need to extract one element of one row of '+
                      'elements at a time in this case.')
            raise CannotExpandFlagsError(errtxt)
            
        #self._bufr_obj.delayed_repl_check_for_incorrect_use()

        num_subsets  = self.get_num_subsets()
        num_elements = self.get_num_elements()
        result = numpy.zeros([num_subsets, num_elements], dtype=float)

        print('DEBUG: num_subsets = ', num_subsets)
        print('DEBUG: num_elements = ', num_elements)

        for descr_nr in range(num_elements):
            
            result[:, descr_nr] = self.get_values(descr_nr)
            # autoget_cval option not functional yet

        return result
        #  #]
    def get_names_and_units(self, subset=1):
        #  #[ request name and unit of each descriptor for the given subset
        if (self.msg_index == -1):
            raise NoMsgLoadedError
        
        return (self.get_names(subset), self.get_units(subset))
        #  #]
    def get_names(self, subset=1):
        #  #[ request name of each descriptor for the given subset
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        return eccodes.codes_get_array(self.bufr_id, 'expandedNames')
        #  #]
    def _get_abbr_names(self, subset=1):
        #  #[ request abbr. name of each descriptor for the given subset
        '''
        internal method to get the key name needed to extract the data
        '''
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        # remove entries that are not expanded and numeric.
        # these typically are replication codes and not part
        # of the field list
        abbr_names = [n for n in
                      eccodes.codes_get_array(self.bufr_id,
                                              'expandedAbbreviations')
                      if not n[0] in string.digits]
        return abbr_names
        #  #]
    def get_units(self, subset=1):
        #  #[ request unit of each descriptor for the given subset
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        return eccodes.codes_get_array(self.bufr_id, 'expandedUnits')
        #  #]        
    def get_unexp_descr_list(self):
        #  #[ get unexpanded descfriptor list
        '''
        wrapper around  self._bufr_obj.py_unexp_descr_list
        '''
        if (self.msg_index == -1):
            raise NoMsgLoadedError

        n = eccodes.codes_get(self.bufr_id, 'numberOfUnexpandedDescriptors')
        if n==1:
            list_of_unexp_descr = [eccodes.codes_get(self.bufr_id,
                                                'unexpandedDescriptors'),]
        else:
            list_of_unexp_descr = eccodes.codes_get_array(self.bufr_id,
                                                'unexpandedDescriptors')
        
        return list_of_unexp_descr
        #  #]
    def messages(self):
        """
        Raises
        ------
        IncorrectUsageError
            if message can not be packed into a 2D array.

        Yields
        ------
        data : dict
            Dictionary of the data in the BUFR message.
            Keys are the names of the variables.
        units: dict
            The units of each data field in the data dictionary.
            Keys are the same as in the data dictionary.
        """
        for i in numpy.arange(self.num_msgs) + 1:
            self.get_next_msg()
            values = self.get_values_as_2d_array()
            cnames, cunits = self.get_names_and_units()

            data = {}
            units = {}
            for i, name in enumerate(cnames):
                data[name] = values[:, i]
                units[name] = cunits[i]

            yield data, units

    def __enter__(self):
        return self

    def __exit__(self, exc, val, trace):
        self.close()

    def close(self):
        #  #[
        """
        close the file object
        """
        if self.bufr_id != -1:
            eccodes.codes_release(self.bufr_id)

        self.fd.close()
        #  #]
    #  #]

BUFRReader = BUFRReaderBUFRDC
BUFRWriter = BUFRWriterBUFRDC

if eccodes_available:
    print('Using ecCodes')
    BUFRReader = BUFRReaderECCODES
    #not yet implemented:
    #BUFRWriter = BUFRWriterECCODES
    #sys.exit(1)


if __name__ == "__main__":
    #  #[ test program
    print("Starting test program:")
    
    # this is how I think the BUFR module interfacing should look like
    
    # get a msg instance
    BMSG = BUFRMessage_R()
    # all sections should be filled with sensible defaults but ofcourse
    # the user should be able to change all of them
    # also the user should be able to insert a bufr table name to be
    # used, in contrast with the ECMWF method of using the metadata
    # to construct the BUFR table name. In that case the symbolic link
    # to the constructed BUFR table name should be rerouted to the name
    # provided by the user, to trick the ECMWF library in using it.
    
    # built the template
    #bm.add_descriptor()
    #bm.add_descriptor()
    #bm.add_descriptor()
    
    # expand any D-table entries
    #bm.expand_descriptor_list()
    
    #ns = 361
    #bm.set_num_subsets(ns)
    #for ss in range(ns):
    #    bm.set_fill_index_to_start_subset(ss)
    #    bm.fill_one_element(val, descr_code, descr_text)
    #    bm.fill_one_element(val, descr_code, descr_text)
    #    bm.fill_one_element(val, descr_code, descr_text)
    
    #bf = BUFRFile()
    #bf.open(file = '', mode = 'w')
    #bf.write(bm) # this should automatically do the encoding
    #bf.close()
    
    # further ideas:
    # -allow generation of a custom minimal BUFR table
    #  holding only the entries needed to decode/encode the
    #  current BUFR message
    # -add methods to compose a BUFR table from scratch
    #  and/or modify it (add, delete, save, load)
    #
    #  #]
    
