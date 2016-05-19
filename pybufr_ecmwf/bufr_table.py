#!/usr/bin/env python

"""
a module to allow easier handling of BUFR tables
by providing several helper classes.
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
#  #[ some notes
# see: WMO_BUFR_Guide_Layer3-English-only.pdf
#
# p.25 (L3-23)
# for F=0 (table B entries)
# classes x=48 to 63 are reserved for local use
# entries y=192-255 within all classes are reserved for local use
#
#  #]
#  #[ imported modules
from __future__ import (absolute_import, division,
                        print_function) #, unicode_literals)

import os, stat
import sys
import glob
import csv

from pybufr_ecmwf.helpers import python3
from pybufr_ecmwf.custom_exceptions import ProgrammingError
#  #]

class Descriptor: # [a simple table B entry]
    #  #[
    """
    a base class for storing descriptor information
    """
    def __init__(self, reference, name, unit, unit_scale,
                 unit_reference, data_width):
        #  #[
        self.reference      = reference      # descriptor code
        self.name           = name           # descriptive text
        self.unit           = unit           # unit text
        self.unit_scale     = unit_scale     # multiplicative factor of 10
        self.unit_reference = unit_reference # offset
        self.data_width     = data_width     # number of bits for storage
        #  #]
    def __str__(self):
        #  #[
        txt = "reference: ["+str(self.reference)+"] "+\
              "name: ["+self.name+"] "+\
              "unit: ["+self.unit+"] "+\
              "unit_scale: ["+str(self.unit_scale)+"] "+\
              "unit_reference: ["+str(self.unit_reference)+"] "+\
              "data_width: ["+str(self.data_width)+"] "
        return txt
        #  #]
    def checkinit(self, other):
        #  #[
        """
        a function to be called when an instance is created for a
        descriptor that had been instantiated before. It checks the instance
        properties to make sure we have no double descriptors with
        differing attributes (which would mean a serious design problem
        in the BUFR files and/or template)
        """
        try:
            assert(self.reference      == other.reference)
            assert(self.name           == other.name)
            assert(self.unit           == other.unit)
            assert(self.unit_scale     == other.unit_scale)
            assert(self.unit_reference == other.unit_reference)
            assert(self.data_width     == other.data_width)
        except AssertionError as aerr:
            print('checkinit check failed !!!')
            print()
            print('which means that the current B table contains multiple')
            print('conflicting definitions for the same descriptor!')
            print('This is a bug in the tables provided by ECMWF')
            print('and should be reported to them to be solved.')
            print('')
            print('')
            print()
            print(("self.reference       = [%12s]"
                   "other.reference      = [%12s]") %
                  (str(self.reference), str(other.reference)))
            print(("self.name            = [%12s]"
                   "other.name           = [%12s]") %
                  (str(self.name), str(other.name)))
            print(("self.unit            = [%12s]"
                   "other.unit           = [%12s]") %
                  (str(self.unit), str(other.unit)))
            print(("self.unit_scale      = [%12s]"
                   "other.unit_scale     = [%12s]") %
                  (str(self.unit_scale), str(other.unit_scale)))
            print(("self.unit_reference  = [%12s]"
                   "other.unit_reference = [%12s]") %
                  (str(self.unit_reference), str(other.unit_reference)))
            print(("self.data_width      = [%12s]"
                   "other.data_width     = [%12s]") %
                  (str(self.data_width), str(other.data_width)))
            #print('cls.__instance_dict__ = ', self.__class__.__instance_dict__)
            raise aerr
        #  #]
    def __long__(self):
        if python3:
            return int(self.reference)
        else:
            return long(self.reference)
    def get_count(self):
        return 1
    def get_num_bits(self):
        return self.data_width
    def get_min_max_step(self):
        #  #[ return some descriptor properties
        # encoded_val = value*10^scale-refvalue
        # decoded_val = (encoded_val+refvalue)*10^(-scale)
        # ==>range for encoded values for n bits: min_val = 0, max_val = 2^n-1
        # ==>this gives for the range of decoded values:
        #    min_val = (0+refvalue)*10^(-scale)
        #    max_val = (2^n-1+refvalue)*10^(-scale)

        step = 10.**(-1.*self.unit_scale)
        min_allowed_value = self.unit_reference * step
        max_allowed_value = ((2**self.data_width)-1+self.unit_reference)*step
        return (min_allowed_value, max_allowed_value, step)
        #  #]
    #  #]

# todo: look-up the possibilities in the documentation
class ModifiedDescriptor:
    #  #[
    """
    a base class for modified descriptors
    """
    # note: this cannot be subclassed from Descriptor, since the whole
    # point of modified descriptors is that you can have several with
    # the same descriptor code but with different properties.
    # Since Descriptor is itself a subclass of Singleton this would not
    # be possible, so just copy all items defined by the descriptor
    # to allow easy modification
    def __init__(self, descriptor):
        #  #[
        self.descriptor = descriptor
        self.list_of_modifications = []

        # these properties are copied from the input descriptor,
        # unless they are changed by a modification
        self.reference      = descriptor.reference  # descriptor code
        self.name           = descriptor.name       # descriptive text
        self.unit           = descriptor.unit       # unit text
        self.unit_scale     = descriptor.unit_scale # multipl. factor of 10
        self.unit_reference = descriptor.unit_reference # offset
        self.data_width     = descriptor.data_width # number of bits for storage
        #  #]        
    def add_modification(self, modification):
        #  #[
        """
        define a modification for this descriptor
        """
        assert(isinstance(modification, ModificationCommand))
        self.list_of_modifications.append(modification)
        # todo: depending on the type of midification
        #       change the instance variables
        #  #]
    #  #]
    
# todo: look-up the possibilities in the documentation
# see WMO_BUFR_Guide_Layer3-English-only.pdf p.70
class ModificationCommand(Descriptor): # F=2 [table C entry]
    #  #[
    """
    a base class for modification commands to descriptors
    """
    def __init__(self, reference):
        #  #[
        self.reference      = reference      # descriptor code
        # TODO: add more state variables depending on the type
        # of modification

        # extract xxyyy from the 2xxyyy format of the descriptor
        reference_text = "%6.6i" % reference
        self.xx_ = reference_text[1:3]
        self.yyy = reference_text[3:]
        #  #]
    def __str__(self):
        #  #[
        txt = "modification command reference: ["+str(self.reference)+"] "
        return txt
        #  #]
    def checkinit(self, reference):
        #  #[
        """
        a function to be called when an instance is created for a
        modification command that had been instantiated before.
        """
        assert(self.reference == reference)
        #  #]
    def is_modification_start(self):
        #  #[
        """
        detect whether current modification is a start code
        """
        if self.xx_ == "01" or self.xx_ == "07":
            if self.yyy != "000":
                return True
            else:
                return False
        print("ERROR: handling this modification is not fully implemented yet:")
        print(self)
        raise NotImplementedError
        #  #]
    def is_modification_end(self):
        #  #[
        """
        detect whether current modification is an end code
        """
        if self.xx_ == "01" or self.xx_ == "07":
            if self.yyy == "000":
                return True
            else:
                return False
        print("ERROR: handling this modification is not fully implemented yet:")
        print(self)
        raise NotImplementedError
        #  #]
    def check_matches(self, descr):
        #  #[
        """
        check whether a clear command matches a change command
        """
        
        #print("end modification: "+str(self))
        #print("seems to match modification: "+str(d))

        if self.xx_ == "01" or self.xx_ == "07":
            if ((self.yyy == "000" and descr.yyy != "000") or
                (descr.yyy == "000" and self.yyy != "000")   ):
                if self.xx_ == descr.xx_:
                    return True
                else:
                    return False
            else:
                print("ERROR: modification start-and-end do not match !")
                print("problem in check_matches.")
                print("end modification: "+str(self))
                print("seems to match modification: "+str(descr))
                raise IOError
        else:
            print("ERROR: handling this modification is not "+
                  "fully implemented yet:")
            print(self)
            raise NotImplementedError
        #  #]

    # Modification commands are:
    # (see:BUFR reference manual, by Milan Dragosavac, 2007, p.20)
    # 201yyy change data width
    # 202yyy change scale
    # 203yyy change reference value
    # 204yyy add associated field
    # 205yyy signify character
    # 206yyy signify data width
    # 207yyy increase scale, ref.val. and data width
    # 207000 cancel change
    # 208yyy change with of CCITTIA5 field
    # 209yyy IEEE floating point representation
    # 221yyy data not present

    # (see:BUFR reference manual, by Milan Dragosavac, 1984, p.67-71)
    # 222000 quality information
    # 223000 substituted values operator
    # 223255 substituted value marker operator
    # 224000 first order statistical values follow
    # 224255 first order statistical values marker operator
    # 225000 difference statistical values follow
    # 225255 difference statistical values marker operator
    # 232000 replaced/retained values follow
    # 232255 replaced/retained values marker operator
    # 235000 cancel backward data reference
    # 236000 define backward reference bit map
    # 237000 use defined bit map
    # 237255 cancel 237000
    
    # (see:BUFR reference manual, by Milan Dragosavac, 2007, p.21)
    # 241yyy define event
    # 241255 cancel 241yyy
    # 242yyy define conditioning event
    # 242255 cancel 242yyy
    # 243yyy categorical forecast values follow
    # 243255 cancel 243yyy
    #  #]

# todo: look-up the possibilities in the documentation
class SpecialCommand(Descriptor): # F=1
    #  #[
    """
    a base class for special descriptors (i.e. replicators)
    """
    def __init__(self, reference):
        #  #[
        self.reference = reference      # descriptor code
        # TODO: add more state variables depending on the type
        # of special
        #  #]
    def __str__(self):
        #  #[
        txt = "special command reference: ["+str(self.reference)+"] "
        return txt
        #  #]
    def checkinit(self, reference):
        #  #[
        """
        a function to be called when an instance is created for a
        special command that had been instantiated before.
        """
        assert(self.reference == reference)
        #  #]
    #  ==>descriptor
    #  ==>special command

    # the commands described by a reference like 1xxyyy
    # are replication commands, defined like this:
    #def get_replication_code(num_descriptors, num_repeats):
    #    repl_factor = 100000 + num_descriptors*1000 + num_repeats
    #    # for example replicating 2 descriptors 25 times will be
    #    # encoded as: 102025
    #    # for delayed replication, set num_repeats to 0
    #    # then add the Delayed_Descr_Repl_Factor after this code
    #    return repl_factor
    #  #]

# is this identical to SpecialCommand ?x
# see also the F=1 case in the expand method of CompositeDescriptor
class Replicator(Descriptor):
    #  #[
    """
    a base class for replicators
    """
    def __init__(self,repeats,descriptor_list):
        #  #[ init
        self.repeats = repeats
        self.descriptor_list = descriptor_list
        #  #]
    def checkinit(self):
        # checkinit is probably not needed for this type
        pass
    def __str__(self):
        #  #[
        txt = (str(self.repeats)+" repeats of ["+
               str(";".join(str(d.reference) for d
                            in self.descriptor_list))+"]")
        return txt
        #  #]
    def __getattr__(self, attr):
        #  #[ delegate to compose_reference
        if attr=='reference':
            return self.compose_reference()
        else:
            raise AttributeError
        #  #]
    def compose_reference(self):
        #  #[ 
        # f = type = 1 for replication
        # xx = num. descr. to replicate
        # yyy = repl. count
        f = '1'
        xx = '%02' % len(self.descriptor_list)
        yyy = '%03' % self.repeats
        return int(f+xx+yyy)
        #return f+xx+yyy+';'+str(";".join(str(d.reference) for d
        #                                 in self.descriptor_list))
        #  #]
    #  #]

class DelayedReplicator(Descriptor):
    #  #[
    """
    a base class for delayed replicators
    """
    def __init__(self):
        pass
    def checkinit(self):
        """
        a function to be called when an instance is created for a
        delayed replicator command that had been instantiated before.
        """
        pass
    #  ==>maximum-replication-count = 4
    #  ==>actual-replication-count-list ] [1, 2, 3, 4]
    #  ==>list-of-descriptor-objects = []
    #  #]

class CompositeDescriptor(Descriptor): # [table D entry]
    #  #[
    """
    a base class for composite descriptors (table D entries)
    """
    def __init__(self, reference, descriptor_list, comment, bufr_table_set):
        #  #[
        self.reference = reference

        self.descriptor_list = []
        for d in descriptor_list:
            if isinstance(d, DelayedReplicator):
                raise NotImplementedError('adding a DelayedReplicator')
            elif isinstance(d, Replicator):
                self.descriptor_list.append(d)
                self.descriptor_list.extend(d.descriptor_list)
            else:
                self.descriptor_list.append(d)
            
        self.comment = comment
        # set of BUFR tables to which this D descriptor belongs
        # (essential information to enable unpacking this D descriptor!)
        self.bufr_table_set = bufr_table_set
        #  #]
    def __str__(self):
        #  #[
        txt = "reference: ["+str(self.reference)+"] "+\
              "refers to: "+\
              ";".join(str(d.reference) for d in self.descriptor_list)
        return txt
        #  #]
    def expand(self):
        #  #[
        """ a function to expand a table D entry into a list of
        table B entries.
        """
        expanded_descriptor_list = []
        num_descr_to_skip = 0
        if self.bufr_table_set.verbose:
            print('==> expanding: %6.6i' % self.reference)
        for (i, descr) in enumerate(self.descriptor_list):

            # for replicated blocks, several descriptors may have been
            # added already (maybe several times) to the
            # expanded_descriptor_list, so this trick allows them to be
            # skipped when continuing the loop
            if num_descr_to_skip > 0:
                num_descr_to_skip -= 1
                if self.bufr_table_set.verbose:
                    print('skipping: %6.6i' % descr.reference)
                continue
            
            f_val = int(descr.reference/100000.)
            if f_val == 3:
                # this is another table D entry, so expand recursively
                if self.bufr_table_set.verbose:
                    print('adding expanded version of: %6.6i' %
                          descr.reference)
                tmp_list = self.bufr_table_set.table_d[descr.reference].expand()
                expanded_descriptor_list.extend(tmp_list)
            elif f_val == 1:
                # this is a replication operator
                if self.bufr_table_set.verbose:
                    print('handling replication operator: %6.6i' %
                          descr.reference)
                xx  = int((descr.reference-100000.)/1000)
                yyy = (descr.reference-100000-1000*xx)
                if self.bufr_table_set.verbose:
                    print('xx = ', xx, ' = num. descr. to replicate')
                    print('yyy = ', yyy, ' = repl. count')

                # note: for now only handle normal replication
                # since I have no testfile at hand with delayed replication.
                # In case of delayed replication, the replication operator
                # is followed by a maximum replication count, and I believe
                # the expansion of the descriptor list should assume the
                # maximum (but this is to be confirmed)
                replication_count = yyy
                num_descr_to_skip = xx

                # note that i points to the replication operator
                descr_list_to_be_replicated = self.descriptor_list[i+1:i+1+xx]
                if self.bufr_table_set.verbose:
                    print('descr_list_to_be_replicated = ',
                          ';'.join(str(s.reference) for s
                                   in descr_list_to_be_replicated))
                # do the replication
                for j in range(yyy):
                    for repl_descr in descr_list_to_be_replicated:
                        repl_descr_f_val = int(repl_descr.reference/100000.)
                        if repl_descr_f_val == 3:
                            if self.bufr_table_set.verbose:
                                print(('%i: adding expanded version '+
                                       'of: %6.6i') %
                                       (j, repl_descr.reference))
                            expanded_descriptor_list.extend(repl_descr.expand())
                        else:
                            if self.bufr_table_set.verbose:
                                print('%i: adding copy of: %6.6i' %
                                      (j, repl_descr.reference))
                            expanded_descriptor_list.\
                                     append(repl_descr.reference)
                
                # print('DEBUG: breakpoint')
                # sys.exit(1)
                
            else:
                if self.bufr_table_set.verbose:
                    print('adding: %6.6i' % descr.reference)
                expanded_descriptor_list.append(descr.reference)
                
        return expanded_descriptor_list
        #  #]    
    def checkinit(self, reference, descriptor_list, comment, bufr_table_set):
        #  #[

        """
        a function to be called when an instance is created for a
        composite descriptor that had been instantiated before.
        It checks the instance
        properties to make sure we have no double descriptors with
        differing attributes (which would mean a serious design problem
        in the BUFR files and/or template)
        """
        try:
            assert(self.reference       == reference)
            assert(self.descriptor_list == descriptor_list)
            assert(self.comment         == comment)
            assert(self.bufr_table_set  == bufr_table_set)
        except:
            print('assertion failed in CompositeDescriptor.checkinit')
            print('in module pybufr_ecmwf.bufr_table')
            print()
            print('details: ')
            print('self.reference = ', str(self.reference))
            print('reference      = ', str(reference))
            print('self.descriptor_list = ', str(self.descriptor_list))
            print('descriptor_list      = ', str(descriptor_list))
            print('self.comment = ', str(self.comment))
            print('comment      = ', str(comment))
            print('self.bufr_table_set = ', str(self.bufr_table_set))
            print('bufr_table_set      = ', str(bufr_table_set))
            print()
            print('==>A possibly cause for this problem could be that')
            print('==>you tried to load a BUFR D-table twice into the same')
            print('==>BufrTable instance, without first deleting')
            print('==>the previous copy?')
            sys.exit(1)
        #  #]
    def get_count(self):
        count = 0
        for d in self.descriptor_list:
            if isinstance(d, SpecialCommand):
                print('Sorry, not yet implemented')
                sys.exit(1)
            count += d.get_count()
        return count
    #  #]

class FlagDefinition:
    def __init__(self, reference):
        self.reference = reference
        self.flag_dict = {}
    def __str__(self):
        text = []
        for k in sorted(self.flag_dict):
            text.append('flag: '+str(k)+' value: '+str(self.flag_dict[k]))
        return '\n'.join('==> '+l for l in text)
    
class BufrTable:
    #  #[
    """
    a base class for BUFR B, C and D tables    
    """
    # Some variables to remember if we already loaded a BUFR table or not.
    # Note that these have to be stored as class variables.
    # If they would have been stored as BufrTable instance variables
    # the information could not be shared between 2 different
    # instances of this class (even though the actual descriptor instances
    # are shared thanks to the singleton trick used in this module).
    # This is important to speed up performance in case multiple
    # BUFR messages need to be decoded sequentially that use the
    # same set of BUFR tables (which will ususally be the case, although
    # this is not a requirement as far as I know; even 2 BUFR messages
    # from the same BUFR file could in theory use different tables ...).
    currently_loaded_B_table = None
    currently_loaded_C_table = None
    currently_loaded_D_table = None
    saved_B_table = None
    saved_C_table = None
    saved_D_table = None
    
    def __init__(self,
                 autolink_tablesdir="tmp_BUFR_TABLES",
                 tables_dir=None,
                 verbose=True,
                 report_warnings=True):
        #  #[
        self.table_b   = {} # dict of desciptor-objects (f=0)
        self.specials  = {} # dict of specials  (f=1)
        self.modifiers = {} # dict of modifiers (f=2)
        self.table_d   = {} # dict of composite-descriptor-objects (f=3)

        self.table_c   = {} # dict of flag definitions

        self.verbose = verbose
        self.report_warnings = report_warnings
        
        self.autolink_tables = True
        if (tables_dir is not None):
            # dont use autolinking if the user provided a tables dir
            # print('using user provided directory to look for BUFR tables:')
            # print('==> tables_dir = ',tables_dir)
            self.autolink_tables = False
            self.tables_dir = tables_dir

        # inspect the environment setting 'BUFR_TABLES' and use that
        # one as user provided BUFR table directory, if defined
        # WARNING: this won't work when called from expand_raw_descriptor_list
        # defined in bufr_interface_ecmwf (which in turn is called from
        # decode_data, because setup_tables is supposed to be used first,
        # and that one already alters the BUFR_TABLES env setting!
        if 'BUFR_TABLES' in os.environ:
            # print('using user provided directory to look for BUFR tables: ')
            # print("==> os.environ['BUFR_TABLES'] = "+
            #       os.environ['BUFR_TABLES'])
            self.autolink_tables = False
            self.tables_dir = os.environ['BUFR_TABLES']
            
        # if self.autolink_tables is True, 
        # try to automatically make symbolic links to
        # BUFR tables provided by the ECMWF library for any new
        # BUFR table name that is requested by the decoder/encoder
        # in this directory
        self.autolink_tablesdir = autolink_tablesdir

        # apply the choosen tables dir setting
        if (self.autolink_tables):
            self.set_bufr_tables_dir(self.autolink_tablesdir)
        else:
            self.set_bufr_tables_dir(self.tables_dir)

        # used for the decoding of table D
        self.list_of_d_entry_lineblocks = []
        self.num_d_blocks = 0

        #  #]
    def normalise_descriptor_list(self, descr_list):
        #  #[ normalise the list to hold only Desciptor instances
        normalised_descriptor_list = []
        for tmp_descr in descr_list:

            if isinstance(tmp_descr, Descriptor):
                normalised_descriptor_list.append(tmp_descr)
            elif isinstance(tmp_descr,list):
                # we have got a list ...
                norm_descr_list = self.normalise_descriptor_list(tmp_descr)
                normalised_descriptor_list.extend(norm_descr_list)
            else:
                try:
                    int_descr = int(tmp_descr)
                except:
                    print('ERROR: unknown type: type(tmp_descr): ',
                          type(tmp_descr))
                    print('for tmp_descr = ', tmp_descr)
                    sys.exit(1)
                f_val = int(int_descr/100000.)
                if f_val == 0:
                    # this one should already be in the table_b dictionary
                    # otherwise the wrong table_b is loaded
                    descr = self.table_b[int_descr]
                if f_val == 1:
                    if int_descr not in self.specials:
                        new_descr = SpecialCommand(int_descr)
                        self.specials[int_descr] = new_descr
                    descr = self.specials[int_descr]
                if f_val == 2:
                    if int_descr not in self.modifiers:
                        new_descr = ModificationCommand(int_descr)
                        self.modifiers[int_descr] = new_descr
                    descr = self.modifiers[int_descr]
                if f_val == 3:
                    # this one should already be in the table_d dictionary
                    # otherwise the wrong table_d is loaded
                    descr = self.table_d[int_descr]

                normalised_descriptor_list.append(descr)
                
        return normalised_descriptor_list
        #  #]
    def expand_descriptor_list(self, descr_list):
        #  #[
        """ a function to expand a descriptor list, holding table D entries
        and replicators etc. into a clean list of table B entries (with f=0)
        and modification operators (with f=2).
        Descr_list may be a list of descriptor instances, or a list of
        integer reference numbers, a list of strings that can be
        converted to a list of reference numbers, or even a combination of
        these different types.
        """
        normalised_descriptor_list = self.normalise_descriptor_list(descr_list)
        expanded_descriptor_list = []
        delayed_repl_present = False
        num_descr_to_skip = 0
        for (i, descr) in enumerate(normalised_descriptor_list):

            # for replicated blocks, several descriptors may have been
            # added already (maybe several times) to the
            # expanded_descriptor_list, so this trick allows them to be
            # skipped when continuing the loop
            if num_descr_to_skip > 0:
                num_descr_to_skip -= 1
                if self.verbose:
                    print('skipping: %6.6i' % descr.reference)
                continue
            
            f_val = int(descr.reference/100000.)
            if f_val == 3:
                # this is another table D entry, so expand recursively
                if self.verbose:
                    print('adding expanded version of: %6.6i' %
                          descr.reference)
                tmp_list, tmp_del_repl_present = \
                          self.expand_descriptor_list(\
                               self.table_d[descr.reference].descriptor_list)
                if tmp_del_repl_present:
                    delayed_repl_present = True
                if tmp_list:
                    expanded_descriptor_list.extend(tmp_list)
                else:
                    # this exception occurs in case of delayed replication
                    return None, True
                if self.verbose:
                    print('done expanding: %6.6i' % descr.reference)
            elif f_val == 1:
                # this is a replication operator
                if self.verbose:
                    print('handling replication operator: %6.6i' %
                          descr.reference)
                xx  = int((descr.reference-100000.)/1000)
                yyy = (descr.reference-100000-1000*xx)
                if self.verbose:
                    print('xx = ', xx, ' = num. descr. to replicate')
                    print('yyy = ', yyy, ' = repl. count')
                
                # note: we van only handle normal replication here
                # Delayed replication can only be expanded if the data
                # is available as well, and cannot be done based on
                # a descriptor list alone.
                replication_count = yyy
                num_descr_to_skip = xx

                # note that i points to the replication operator
                descr_list_to_be_replicated = \
                      normalised_descriptor_list[i+1:i+1+xx]
                if self.verbose:
                    print('descr_list_to_be_replicated = ',
                          ';'.join(str(s.reference) for s
                                   in descr_list_to_be_replicated))
                
                if yyy == 0:
                    # delayed replication is a problem since we don't
                    # know the actual replication count untill section 4
                    # is unpacked.
                    # This descriptor list expansion routine should also
                    # run if only sections 0-3 are unpacked,
                    # so we have no choice but to leave the delayed
                    # replication unhandled here
                    #if self.verbose:
                    #    print('Sorry, expanding delayed replications is not')
                    #    print('possible based on a descriptor list alone.')
                    #    print('expand_descriptor_list failed ...')
                    #return None, True
                    delayed_repl_operator = normalised_descriptor_list[i+1]
                    descr_list_to_be_replicated = \
                                normalised_descriptor_list[i+2:i+2+xx]
                    tmp_list, tmp_del_repl_present = \
                       self.expand_descriptor_list(descr_list_to_be_replicated)
                    expanded_descriptor_list.append(delayed_repl_operator.reference)
                    expanded_descriptor_list.append(tmp_list)
                    delayed_repl_present = True
                    num_descr_to_skip += 1
                else:
                    # do the replication
                    for j in range(yyy):
                        for repl_descr in descr_list_to_be_replicated:
                            repl_descr_f_val = int(repl_descr.reference/100000.)
                            if repl_descr_f_val == 3:
                                if self.verbose:
                                    print(('%i: adding expanded version '+
                                           'of: %6.6i') %
                                           (j, repl_descr.reference))
                                expanded_descriptor_list.\
                                         extend(repl_descr.expand())
                            else:
                                if self.verbose:
                                    print('%i: adding copy of: %6.6i' %
                                          (j, repl_descr.reference))
                                expanded_descriptor_list.\
                                         append(repl_descr.reference)
                if self.verbose:
                    print('done handling replication operator: %6.6i' %
                          descr.reference)
            else:
                if self.verbose:
                    print('adding: %6.6i' % descr.reference)
                expanded_descriptor_list.append(descr.reference)

        return expanded_descriptor_list, delayed_repl_present
        #  #]    
    def set_bufr_tables_dir(self, tables_dir):
        #  #[
        """
        a method to pass the directory name, in which BUFR tables
        should be available for the current BUFR messages/files
        """

        # force a slash at the end, otherwise the library fails
        # to find the tables
        self.tables_dir = os.path.abspath(tables_dir)+os.path.sep

        # make sure the BUFR tables can be found by setting the
        # needed environment variable
        env = os.environ
        env["BUFR_TABLES"] = self.tables_dir
        #  #]
    def get_descr_object(self, reference):
        #  #[
        """
        method that returns a different class instance,
        depending on the type of descriptor.
        """
        if reference in self.table_b:
            return self.table_b[reference]
        if reference in self.table_d:
            return self.table_d[reference]
        # get 1st digit
        f_val = int(reference/100000.)
        # note: the cases f == 0 should already be part of table_b
        # and the cases f == 3 should already be part of table_d
        if f_val == 1:
            # this is a special code
            if reference in self.specials:
                return self.specials[reference]
            else:
                # this is a new special
                if self.verbose:
                    print("adding special: "+str(reference))
                special = SpecialCommand(reference)
                self.specials[reference] = special
                return special
        if f_val == 2:
            # this is a modifier
            if reference in self.modifiers:
                return self.modifiers[reference]
            else:
                # this is a new modifier
                if self.verbose:
                    print("adding modifier: "+str(reference))
                modifier = ModificationCommand(reference)
                self.modifiers[reference] = modifier
                return modifier
            
        return None
        #  #]
    def load(self, t_file):
        #  #[
        """
        load a BUFR B, C or D table from file
        """

#        print("loading file: "+t_file)

#        e = os.environ
#        tables_dir = e["BUFR_TABLES"]
#        if not os.path.exists(os.path.join(tables_dir,bfile)):
#            print("ERROR: could not find B-table file")
#            print("Tried to load: "+bfile)
#            print("BUFR_TABLES dir = "+tables_dir)
#            raise IOError

        # first see if the user specified a valid full path/file combination
        # and use it if it exists
        if os.path.exists(t_file):
            tablefile = t_file
        else:
            # if it does not exist, try to find it in the tables_dir
            tablefile = os.path.join(self.tables_dir, t_file)
            if not os.path.exists(tablefile):
                # if still not found, see if autolinking is on
                if (self.autolink_tables):
                    # if so, try to automatically get a symlink 
                    print("autolinking table file: "+t_file)
                    self.autolinkbufrtablefile(t_file)

        #print("inspecting file: "+t_file)
        #maxlen = 0
        #for line in open(t_file, 'rt'):
        #    l = line.replace('\r', '').replace('\n', '')
        #    if len(l)>maxlen:
        #        maxlen = len(l)
        #print("longest line is: "+str(maxlen))

        (path, base) = os.path.split(tablefile)
        B_tablefile = os.path.join(path, 'B'+base[1:])
        C_tablefile = os.path.join(path, 'C'+base[1:])
        D_tablefile = os.path.join(path, 'D'+base[1:])

        reload_tables = False
        if base[0].upper() == 'B':
            #
            if (self.__class__.currently_loaded_B_table !=  B_tablefile):
                reload_tables = True
        elif base[0].upper() == 'C':
            if (self.__class__.currently_loaded_C_table != C_tablefile):
                reload_tables = True
        elif base[0].upper() == 'D':
            if (self.__class__.currently_loaded_D_table != D_tablefile):
                reload_tables = True
        else:
            print("ERROR: don't know what table this is")
            print("(path, base) = "+str((path, base)))
            raise IOError
        
        if reload_tables:
            # first unload the previous file
            # note that unload removes all 3 files (B,C,D)
            # see just reload all 3 as well
            # next calls to this load method will detect this,
            # set reload_tables to False and use the stored version

            #print('******* DEBUG: unloading tables')
            self.unload_tables()

            # then load the new files
            #print('******* DEBUG: reloading table B: ',  B_tablefile)
            self.load_b_table(B_tablefile)
            self.__class__.saved_B_table = self.table_b

            # allow this load to fail for now, since some BUFR tables
            # versions provided by ECMWF consist of a B and D table only...
            # (and the C table is not needed for basic encoding/decoding
            #  anyway, only for interpretation of flag tables)
            #print('******* DEBUG: reloading table C: ', C_tablefile)
            try:
                self.load_c_table(C_tablefile)
                self.__class__.saved_C_table = self.table_c
            except IOError:
                pass
            except UnicodeDecodeError:
                print('Text encding problem detected in file: ', C_tablefile)
                raise

            #print('******* DEBUG: reloading table D: ', D_tablefile)
            self.load_d_table(D_tablefile)
            self.__class__.saved_D_table = self.table_d

        else: # reuse the already loaded tables
            #print('******* DEBUG: Reusing stored tables')
            self.table_b = self.__class__.saved_B_table
            self.table_c = self.__class__.saved_C_table
            self.table_d = self.__class__.saved_D_table

        self.__class__.currently_loaded_B_table = B_tablefile
        self.__class__.currently_loaded_C_table = C_tablefile
        self.__class__.currently_loaded_D_table = D_tablefile
        #  #]
    def autolinkbufrtablefile(self, t_file):
        #  #[
        """
        a method that automatically creates a symbolic link to
        the given BUFR file, with a name that is expected by the
        ECMWF BUFR software. This should make it possible to use
        a user-defined filename for BUFR files with the ECMWF BUFR
        library.
        """

        if not self.autolink_tables:
            print("programming error in autolinkbufrtablefile!!!")
            raise ProgrammingError
        
        # define our own location for storing (symlinks to) the BUFR tables
        if (not os.path.exists(self.tables_dir)):
            os.mkdir(self.tables_dir)
    
        # make the needed symlinks
        if os.path.exists("ecmwf_bufrtables"):
            ecmwf_bufr_tables_dir = "ecmwf_bufrtables"
        else:
            ecmwf_bufr_tables_dir = "../ecmwf_bufrtables"
            
        ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)

        # algorithm: try the list B or D files one by one,
        # and remove a character from the name in every step.
        # Then try to find a match using glob. This should give
        # the filename that most closely matches the required one,
        pattern = t_file
        while (len(pattern)>1):
            pattern = pattern[:-1]
            print("trying pattern: "+
                  os.path.join(ecmwf_bufr_tables_dir, pattern)+'*')
            matches = glob.glob(os.path.join(ecmwf_bufr_tables_dir,
                                             pattern)+'*')
            print("matches = "+str(matches))
            print("len(matches) = "+str(len(matches)))
            if len(matches)>0:
                source      = matches[0]
                destination = os.path.join(self.tables_dir, t_file)
                if (not os.path.exists(destination)):
                    print("making symlink from "+source+
                          " to "+destination)
                    os.symlink(source, destination)
                break

        #  #]
    def load_b_table(self, bfile):
        #  #[ load the B table from file
        """
        load BUFR table B from file
        """
        if self.verbose:
            print("loading B table from file: "+bfile)

        nr_of_ignored_probl_entries = 0
        for (i, line) in enumerate(open(bfile, 'rt')):
            success = True
            line_copy = line.replace('\r', '').replace('\n', '')

            # example of the expected format (156 chars per line):
            # " 005001 LATITUDE (HIGH ACCURACY)                    "+\
            # "                     DEGREE                     5   "+\
            # "  -9000000  25 DEGREE                    5         7"

            
            if len(line_copy) >= 118:
                txt_reference       = line_copy[0:8] # 8 characters
                txt_name            = line_copy[8:73] # 64 characters
                txt_unit            = line_copy[73:98] # 24 characters
                txt_unit_scale      = line_copy[98:102] # 4 characters
                txt_unit_reference  = line_copy[102:115] # 14 characters
                txt_data_width      = line_copy[115:118] # 4 characters
                # sometimes additional info seems present, but
                # I don't know yet the definition used for that
                txt_additional_info = ''
                if len(line_copy)>118:
                    txt_additional_info = line_copy[118:]
            else:
                success = False
                nr_of_ignored_probl_entries += 1
                if self.report_warnings:
                    print("ERROR: unexpected format in table B file...")
                    print("linecount: "+str(i))
                    print("line: ["+line_copy+"]")
                    print("Line is too short, it should hold at "+
                          "least 118 characters")
                    print("but seems to have only: "+
                          str(len(line_copy))+" characters.")
                    # print("txt_reference       = ["+line_copy[0:8]+"]")
                    # print("txt_name            = ["+line_copy[8:73]+"]")
                    # print("txt_unit            = ["+line_copy[73:98]+"]")
                    # print("txt_unit_scale      = ["+line_copy[98:102]+"]")
                    # print("txt_unit_reference  = ["+line_copy[102:115]+"]")
                    # print("txt_data_width      = ["+line_copy[115:118]+"]")
                    print("You could report this to the creator of this table "+
                          "since this should never happen.")
                    print("Ignoring this entry .....")

            if (success):
                try:
                    reference = int(txt_reference, 10)
                    unit_scale = int(txt_unit_scale)
                    unit_reference = int(txt_unit_reference)
                    data_width = int(txt_data_width)
                    
                    # remove excess spaces from the string before storing
                    name = txt_name.strip()
                    unit = txt_unit.strip()
                    
                except ValueError:
                    success = False
                    nr_of_ignored_probl_entries += 1
                    if (txt_name.strip() == "RESERVED"):
                        # it seems part of the BUFR TABLE file format defined
                        # by ECMWF to allow RESERVED lines in the B tables
                        # (according to an email exchange about my bug report
                        #  on this subject)
                        # therefore do not warn for this condition anynore
                        # print("Ignoring a reserved entry: "+txt_reference)
                        pass
                    else:
                        if self.report_warnings:
                            print("ERROR: unexpected format in table B file...")
                            print("Could not convert one of the numeric "+
                                  "fields to integer.")
                            print("txt_reference       = ["+txt_reference+"]")
                            print("txt_unit_scale      = ["+txt_unit_scale+"]")
                            print("txt_unit_reference  = ["+
                                  txt_unit_reference+"]")
                            print("txt_data_width      = ["+txt_data_width+"]")
                            print("txt_additional_info = ["+
                                  txt_additional_info+"]")
                            print("Ignoring this entry .....")
                        
            if (success):
                # add descriptor object to the list
                b_descr = Descriptor(reference, name, unit,
                                     unit_scale, unit_reference, data_width)

                # NOTE:
                # the BUFR tables in the current ECMWF software, upto
                # version 000403 at least, contain bugs. Multiple conflicting
                # definitions occur for the same B descriptor in some tables.
                # After reporting this to ECMWF, they responded that the
                # problem will not be fixed because the software is to
                # be phased out and replaced by a complete rewrite.
                # They recommend to follow the way the fortran library
                # handles these tables, i.e. just allow the later definition
                # to overwrite the earlier definitions.
                # (see the comments on issue SUP-1082 in the ECMWF
                #  software bug tracking system, 24-nov.2014)
                # Therefore the following test has been disabled for now,
                # and is replaced by this simple assignment.
                self.table_b[reference] = b_descr
                
                #if reference not in self.table_b:
                #    #print("adding descr. key "+str(reference))
                #    self.table_b[reference] = b_descr
                #else:
                #    if self.report_warnings:
                #        print("ERROR: multiple table B descriptors with "+
                #              "identical reference")
                #        print("number found. This should never happen !!!")
                #        print("problematic descriptor is: "+str(b_descr))
                #        print("Ignoring this entry .....")
                #    try:
                #        self.table_b[reference].checkinit(b_descr)
                #    except AssertionError:
                #        print()
                #        print('The current B table file is '+bfile)
                #        print()
                #        raise # reraise
                #    nr_of_ignored_probl_entries += 1

        if self.verbose:
            print("-------------")
            if (nr_of_ignored_probl_entries>0):
                print("nr_of_ignored_probl_entries = "+
                      str(nr_of_ignored_probl_entries))
            print("Loaded: "+str(len(self.table_b))+" table B entries")
            print("-------------")
            # print("self.table_b[006001] = "+
            #       str(self.table_b[int('006001', 10)].reference))
            # print("-------------")
            print('Loaded {} B table entries'.
                  format(str(len(self.table_b.keys()))))
        #  #]
    def add_ref_to_descr_list(self, descriptor_list, reference,
                              ref_reference, line_nr,
                              postpone, report_unhandled):
        #  #[
        """
        add a descriptor instance for the given reference
        to the provided discriptor list
        """

        # get object for ref_reference
        #print("trying descriptor "+str(ref_reference))
        descr = self.get_descr_object(ref_reference)
        if (descr == None):
            postpone = True
            if report_unhandled:
                print("---")
                print("descriptor "+str(ref_reference)+
                      " is never defined but is used by")
                print("D-table entry "+str(reference)+
                      " (line "+str(line_nr)+")")
                #print("postponing processing of this one")
        else:
            # add this object to the list
            #print("adding descriptor with ref: "+str(ref_reference))
            descriptor_list.append(descr)

        return postpone
        #  #]
    def custom_c_split(self, line):
        #  #[ split a flag table line in parts
        part0 = line[:6]
        part1 = line[7:11]
        part2 = line[12:20]
        part3 = line[21:23]
        part4 = line[24:]
        return (part0, part1, part2, part3, part4)
        #  #]
    def custom_d_split(self, line):
        #  #[ replacement for split()
        # needed because sometimes D-descriptors do not have
        # spaces in between the items on the start line
        # (it fails if more than 100 elements are present in one D-entry
        #  which currently is the case for "340005100 001007")
        part1 = line[:7]
        part2 = line[7:11]
        part3 = line[11:18]
        parts = []
        if part1.strip() != '':
            parts.append(part1)
        if part2.strip() != '':
            parts.append(part2)
        if part3.strip() != '':
            parts.append(part3)
        return parts
        #  #]
    def decode_blocks(self, report_unhandled = False):
        #  #[ decode table D blocks of lines
        """
        helper method to decode a block of ascii lines taken from
        the D-table file, defining a single D-descriptor.
        """
        
        handled_blocks = 0
        list_of_handled_blocks = []
        for d_entry_block in self.list_of_d_entry_lineblocks:
            # print("d_entry_block = "+str(d_entry_block))

            # ensure i and line are defined,
            # even if d_entry_block is an empty list
            i = 0
            line = ''
            
            # notes:
            # i is the line number where this d_entry_block is defined
            # j is the counter along all d_entry_blocks
            for (j, (i, line)) in enumerate(d_entry_block):
                #print(j, "considering line ["+line+"]")
                # this fails if more than 100 elements in one D-entry
                # parts = line[:18].split()
                parts = self.custom_d_split(line)
                if j == 0: # startline
                    #print("is a start line")
                    reference     = int(parts[0], 10)
                    count         = int(parts[1])
                    ref_reference = int(parts[2], 10)
                    comment        = ''
                    postpone = False
                    descriptor_list = []
                    if len(line)>18:
                        comment = line[18:]
                else: # continuation_line:
                    #print("is a continuation line")
                    ref_reference = int(parts[0], 10)
                    extra_comment  = ''
                    if len(line)>18:
                        # todo: check if the ref_reference is maybe a table-D
                        # entry without comment, and add the comment there
                        # in stead
                        extra_comment = line[18:]
                        if not (extra_comment.strip() == ""):
                            if self.report_warnings:
                                print("WARNING: ignoring extra comment on "+
                                      "continuation line: ")
                                print("line: ["+line+"]")
                        
                #print(descriptor_list, reference,
                #      ref_reference, postpone, report_unhandled)
                postpone = self.add_ref_to_descr_list(descriptor_list,
                                                      reference,
                                                      ref_reference, i,
                                                      postpone,
                                                      report_unhandled)
            if (not postpone):
                # all continuation lines have been processed so store
                # the result.
                # first a safety check
                if len(descriptor_list)<count:
                    print("ERROR: unexpected format in table D file...")
                    print("problematic descriptor is: "+str(reference))
                    print("linecount: "+str(i))
                    print("line: ["+line+"]")
                    print("This D-table entry defines less descriptors than")
                    print("specified in the start line.")
                    print("This error is unrecoverable.")
                    print("Please report this problem, together with")
                    print("a copy of the bufr table you tried to read.")
                    print("len(descriptor_list) = "+
                          str(len(descriptor_list)))
                    print("count = "+str(count))
                    raise IOError

                if len(descriptor_list)>count:
                    if self.report_warnings:
                        print("WARNING: unexpected format in table D file...")
                        print("problematic descriptor is: "+str(reference))
                        print("linecount: "+str(i))
                        print("line: ["+line+"]")
                        print("This D-table entry defines more "+
                              "descriptors than")
                        print("specified in the start line.")
                        print("Please report this problem, together with")
                        print("a copy of the bufr table you tried to read.")
                        print("len(descriptor_list) = "+
                              str(len(descriptor_list)))
                        print("count = "+str(count))
                        print("This is a formatting problem in the BUFR")
                        print("Table but will not affect decoding.")
                        print("ignoring excess descriptors for now...")
                    
                
                #print("************************storing result")
                d_descr = CompositeDescriptor(reference, descriptor_list,
                                              comment, self)
                if reference not in self.table_d:
                    #print("adding descr. key "+str(reference))
                    self.table_d[reference] = d_descr
                else:
                    if self.report_warnings:
                        print("WARNING: multiple table D descriptors "+
                              "with identical reference")
                        print("number found. This should never happen !!!")
                        print("problematic descriptor is: "+str(d_descr))
                        print("Please report this problem, together with")
                        print("a copy of the bufr table you tried to read.")
                        print("This is a formatting problem in the BUFR")
                        print("Table but will not affect decoding.")
                        print("Ignoring this entry for now.....")
                        self.table_d[reference].checkinit(d_descr)
                    
                # mark this block as done
                list_of_handled_blocks.append(d_entry_block)
                # count successfully handled blocks
                handled_blocks += 1

        # remove the processed blocks
        for d_entry_block in list_of_handled_blocks:
            self.list_of_d_entry_lineblocks.remove(d_entry_block)

        remaining_blocks = len(self.list_of_d_entry_lineblocks)

        # print('DEBUG: handled_blocks   = ', handled_blocks)
        # print('DEBUG: remaining_blocks = ', remaining_blocks)
        return (handled_blocks, remaining_blocks)
        #  #]
    def add_c_table_entry(self,lineblock):
        #  #[ parse lines defining a C table entry

        #if self.verbose:
        #    print(60*'=')
        #    for l in lineblock:
        #        print('line: ['+l+']')

        startline = lineblock[0]
        parts = self.custom_c_split(startline)
        reference = int(parts[0])
        num_flags = int(parts[1])

        fldef = FlagDefinition(reference)

        copied_lineblock = lineblock[:]
        flag_value = None
        # repeat as long as we have lines
        while copied_lineblock:
            current_line = copied_lineblock.pop(0)
            #if self.verbose:
            #    print('parsing: ', current_line)
            parts = self.custom_c_split(current_line)
            if parts[2].strip() == '':
                # this is a continuation line
                text += current_line[22:]
                num_text_lines_added += 1
            else:
                # this is a main flag definition line
                # store previous flag
                if flag_value is not None:
                    # print('storing prev. flag')
                    fldef.flag_dict[flag_value] = text
                    # verify consistency of C table definition
                    if num_text_lines_added != num_text_lines:
                        print('WARNING: C-table seems wrong!')
                        print('expected num_text_lines = ', num_text_lines)
                        print('found    num_text_lines = ',
                              num_text_lines_added)
                        print('parts: ',parts)
                        sys.exit(1)
                        
                # parse new flag
                flag_value = int(parts[2])
                num_text_lines = int(parts[3])
                text = parts[4]
                num_text_lines_added = 1

        # print('Handling final flag def')
        
        # handle last flag def
        if flag_value is not None:
            fldef.flag_dict[flag_value] = text
            # verify consistency of C table definition
            if num_text_lines_added != num_text_lines:
                print('WARNING: C-table seems wrong!')
                print('expected num_text_lines = ', num_text_lines)
                print('found    num_text_lines = ', num_text_lines_added)
                sys.exit(1)
            
        # verify consistency of C table definition
        if num_flags != len(fldef.flag_dict):
            if self.report_warnings:
                print('WARNING: C-table seems wrong for reference '+
                      str(reference)+'!')
                print('expected number of flag values = '+str(num_flags))
                print('found number of unique flag values = '+
                      str(len(fldef.flag_dict)))
                # if num_flags==0:
                print('==>ignoring this problem for now\n')
        else:
            #print('fldef '+str(reference)+' \n'+str(fldef))
            # store the result
            self.table_c[reference] = fldef
        #  #]
    def load_c_table(self, cfile):
        #  #[ load the C table from file
        """
        load BUFR table C from file
        """
        if self.verbose:
            print("loading C table from file: "+cfile)

        # load blocks of lines that define each flag
        this_lineblock = []
        if python3:
            # note: bufr uses CCITT-5 encoding (also known as us-ascii)
            # for all text fields. However there is no such 
            # definition for the descriptions in the c-table file.
            # From experience with the ECMWF files it seems they
            # use the latin-1 alphabet in stead.
            cfd = open(cfile, 'rt', encoding='latin_1')
        else:
            cfd = open(cfile, 'rt')
        for (i, line) in enumerate(cfd):
            line_copy = line.replace('\r', '').replace('\n', '')
            # skip empty lines
            if line_copy == '': continue

            if line_copy[:6].strip() != '':
                # found a new flag definition

                # in case this is not the first block
                if this_lineblock:
                    # handle the previous one
                    self.add_c_table_entry(this_lineblock)
                    # and start all over again
                    this_lineblock = []

            # add the line to the block
            this_lineblock.append(line_copy)

        # handle final definition in the file
        self.add_c_table_entry(this_lineblock)
        
        #  #]
    def load_d_table(self, dfile):
        #  #[ load the D table from file
        """
        load BUFR table D from file
        """
        if self.verbose:
            print("loading D table from file: "+dfile)
            
        if self.verbose:
            print("********************")
            print("**** first pass ****")
            print("********************")
            
        #  #[ create a list of blocks of lines
        self.list_of_d_entry_lineblocks = []
        this_lineblock = None
        for (i, line) in enumerate(open(dfile, 'rt')):
            line_copy = line.replace('\r', '').replace('\n', '')
            # print("considering line "+str(i)+": ["+line_copy+"]")

            # this fails if more than 100 elements in one D-entry
            # parts = line_copy[:18].split()
            parts = self.custom_d_split(line_copy)
            # print('parts: ',parts)
            
            start_line = False
            continuation_line = False
            if (len(parts) == 3):
                start_line = True
            elif (len(parts) == 1):
                continuation_line = True
            else:
                print("ERROR: unexpected format in table D file...")
                print("linecount: "+str(i))
                print("line: ["+line_copy+"]")
                print("first 17 characters should hold either 1 or 3 integer")
                print("numbers, but in stead it holds: "+
                      str(len(parts))+" parts")
                print("You could report this to the creator of this table "+
                      "since this should never happen.")
                raise IOError
            
            if start_line:
                # print("is a start line")
                if (this_lineblock != None):
                    # save the just read block in the list
                    self.list_of_d_entry_lineblocks.append(this_lineblock)
                # and start with a new lineblock
                this_lineblock = []
                this_lineblock.append((i, line_copy))
                
            if continuation_line:
                # print("is a continuation line")
                this_lineblock.append((i, line_copy))

        # save the last block as well
        if (this_lineblock != None):
            # save the final block in the list
            self.list_of_d_entry_lineblocks.append(this_lineblock)

        self.num_d_blocks = len(self.list_of_d_entry_lineblocks)
        #  #]

        if self.verbose:
            print("*********************")
            print("**** second pass ****")
            print("*********************")
            
        handled_blocks_prev_try = 1
        handled_blocks_this_try = 1
        loop_count = 0
        while ( (handled_blocks_prev_try>0) or
                (handled_blocks_this_try>0)    ):
            handled_blocks_prev_try = handled_blocks_this_try
            loop_count += 1
            if self.verbose:
                print("==============>loop count: "+str(loop_count))
            (handled_blocks_this_try, remaining_blocks) = self.decode_blocks()
            
        if self.verbose:
            print("remaining blocks: "+str(remaining_blocks))
            print("decoded blocks (prev try):   "+str(handled_blocks_prev_try))
            print("decoded blocks (this try):   "+str(handled_blocks_this_try))
        if self.report_warnings:
            if remaining_blocks > 0:
                print("---------------------------------------------------")
                print("Reporting problematic blocks:")
                print("---------------------------------------------------")
                # nothing more to decode here, but run it once more with
                # the report_unhandled flag set, to generate a listing
                # of not properly used/defined entries
                (handled_blocks, remaining_blocks) = \
                                 self.decode_blocks(report_unhandled = True)
                print("---------------------------------------------------")
                
        if self.verbose:
            print('-------------')
            print('Loaded: '+str(self.num_d_blocks)+' table D entries')
            print('-------------')
            
        if self.verbose:
            print("remaining_blocks = "+str(remaining_blocks))
            
        if (self.num_d_blocks == remaining_blocks):
            print("ERROR: it seems you forgot to load "+
                  "the B-table before trying")
            print("to load the D-table. It is required to load "+
                  "the corresponding B-table")
            print("first, because it is needed to apply consistency "+
                  "checking on the")
            print("D-table during the read process.")
            print("")
            print("Alternatively, this could point to D table entries")
            print("that have no definition in the provided B table.")
            raise ProgrammingError

        if self.verbose:
            print('Loaded {} D table entries'.format(len(self.table_d.keys())))
        #  #]
    def read_WMO_csv_table_b(self, b_filename):
        #  #[ load table B from WMO csv file
        table_b   = {} # dict of desciptor-objects (f=0)
        with open(b_filename) as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            nr_of_ignored_probl_entries = 0
            for row in csvreader:
                success = True
                FXY            = row['FXY']
                ElementName_en = row['ElementName_en']
                Note_en        = row['Note_en']
                ElementName_en = ElementName_en + Note_en
                BUFR_Unit      = row['BUFR_Unit']
                BUFR_Scale     = row['BUFR_Scale']
                BUFR_ReferenceValue  = row['BUFR_ReferenceValue']
                BUFR_DataWidth_Bits  = row['BUFR_DataWidth_Bits']
                
                # manual fix a long unit
                if BUFR_Unit=="Code table defined by originating/generating centre":
                    BUFR_Unit = "Code table"
                # manually truncate name field
                if len(ElementName_en) > 64:
                    ElementName_en = ElementName_en[:64]
                    
                # check field widths
                if len(FXY) > 8:
                    print("ERROR: string too long for field: FXY "+str(FXY))
                if len(ElementName_en) > 64:
                    print("ERROR: string too long for field: "+
                          "ElementName_en "+str(len(ElementName_en))+
                          " "+str(ElementName_en))
                if len(BUFR_Unit) > 24:
                    print("ERROR: string too long for field: BUFR_Unit "+
                          str(len(BUFR_Unit))+" "+str(BUFR_Unit))
                if len(BUFR_Scale) > 4:
                    print("ERROR: string too long for field: BUFR_Scale "+
                          str(len(BUFR_Scale))+" "+str(BUFR_Scale))
                if len(BUFR_ReferenceValue) > 14:
                    print("ERROR: string too long for field: "+
                          "BUFR_ReferenceValue "+
                          str(len(BUFR_ReferenceValue))+" "+
                          str(BUFR_ReferenceValue))
                if len(BUFR_DataWidth_Bits) > 4:
                    print("ERROR: string too long for field: "+
                          "BUFR_DataWidth_Bits "+
                          str(len(BUFR_DataWidth_Bits))+" "+
                          str(BUFR_DataWidth_Bits))
        
                #print(''.join('['+str(s)+']' for s in
                #              [FXY,ElementName_en,BUFR_Unit,BUFR_Scale,
                #               BUFR_ReferenceValue,BUFR_DataWidth_Bits]))
                
                try:
                    reference = int(FXY, 10)
                    unit_scale = int(BUFR_Scale)
                    unit_reference = int(BUFR_ReferenceValue)
                    data_width = int(BUFR_DataWidth_Bits)
                    txt_additional_info = ''
                    
                    # remove excess spaces from the string before storing
                    name = ElementName_en.strip()
                    unit = BUFR_Unit.strip()
                except ValueError:
                    success = False
                    nr_of_ignored_probl_entries += 1
                    print("ERROR: unexpected format in WMO table B file...")
                    print("Could not convert one of the numeric "+
                          "fields to integer.")
                    print("txt_reference       = ["+FXY+"]")
                    print("txt_unit_scale      = ["+BUFR_Scale+"]")
                    print("txt_unit_reference  = ["+BUFR_ReferenceValue+"]")
                    print("txt_data_width      = ["+BUFR_DataWidth_Bits+"]")
                    print("txt_additional_info = ["+txt_additional_info+"]")
                    print("Ignoring this entry .....")
                
                if (success):
                    # add descriptor object to the list
                    b_descr = Descriptor(reference, name, unit, unit_scale,
                                         unit_reference, data_width)
                    if reference not in table_b:
                        #print("adding descr. key "+str(reference))
                        table_b[reference] = b_descr
                    else:
                        print("ERROR: multiple table B descriptors with "+
                              "identical reference")
                        print("number found. This should never happen !!!")
                        print("problematic descriptor is: "+str(b_descr))
                        self.table_b[reference].checkinit(b_descr)
                        print("Ignoring this entry .....")
                        nr_of_ignored_probl_entries += 1
                        
                    
        print("-------------")
        if (nr_of_ignored_probl_entries>0):
            print("nr_of_ignored_probl_entries = "+
                  str(nr_of_ignored_probl_entries))
        print("Loaded: "+st(len(table_b))+" table B entries")
        print("-------------")
        self.table_b = table_b
        #  #]
    def read_WMO_csv_table_d(self, d_filename):
        #  #[ load table D from WMO csv file
        table_d   = {} # dict of desciptor-objects (f=0)
        with open(d_filename) as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            nr_of_ignored_probl_entries = 0
            for row in csvreader:
                FXY1 = row['FXY1']
                FXY2 = row['FXY2']
                # comment = row['ElementName_en'] + \
                #          row['ElementDescription_en'] + \
                #          row['Note_en']
                int_FXY1 = int(FXY1, 10)
                int_FXY2 = int(FXY2, 10)
                if int_FXY1 not in table_d:
                    table_d[int_FXY1] = []
                # table_d[int_FXY1].append((int_FXY2, comment))
                table_d[int_FXY1].append(int_FXY2)

        # now convert the imported lists into proper
        # CompositeDescriptor instances
        while table_d:
            for reference in table_d:
                descriptor_list = []
                
                postpone = False
                for d in table_d[reference]:
                    descr = self.get_descr_object(d)
                    if (descr == None):
                        postpone = True
                        break
                    descriptor_list.append(descr)
                    
                if postpone:
                    # print 'postponing'
                    continue
            
                comment = ''
                d_descr = CompositeDescriptor(reference, descriptor_list,
                                              comment, self)
                if reference not in self.table_d:
                    # print("adding descr. key "+str(reference))
                    self.table_d[reference] = d_descr
                else:
                    print("WARNING: multiple table D descriptors "+
                          "with identical reference")
                    print("number found. This should never happen !!!")
                    print("problematic descriptor is: "+str(d_descr))
                    print("Please report this problem, together with")
                    print("a copy of the bufr table you tried to read.")
                    print("This is a formatting problem in the BUFR")
                    print("Table but will not affect decoding.")
                    self.table_d[reference].checkinit(d_descr)
                    print("Ignoring this entry for now.....")
                
                del(table_d[reference])
        #  #]
    def apply_special_commands(self):
        #  #[
        """
        apply a special command (t.b.d.)
        """
        # application of special commands (i.e. replications) is
        # done by calling the buxdes subroutine in the ECMWF library
        # so for now I won't implement this in python
        pass
        #  #]
    def apply_modification_commands(self, descr_list):
        #  #[
        """
        register each modification with all the descriptors that
        it applies to. This is needed to allow calculation of the
        allowed range of the value of the descriptor, which is something
        I would like to be able to check from within python
        (because the errors thrown by the ECMWF BUFR library can be rather
        difficult to decipher, and usually won't point you to the mistake
        that you probably made in your own program).

        input: an expanded descriptor list

        output: a new descriptor list, with descriptors that need to be
        modified replaced by their corresponding ModifiedDescriptor
        instance, which should hold pointers to the original descriptor
        and to all modifications applied to it
        """


        mod_descr_list = []
        current_modifications = []
        for descr in descr_list:
            if isinstance(descr, ModificationCommand):
                if descr.is_modification_start():
                    current_modifications.append(descr)
                elif descr.is_modification_end():
                    removed_descr = current_modifications.pop()
                    descr.check_matches(removed_descr)
                else:
                    print("Problem in apply_modification_commands.")
                    print("Modifier not recognised as start or end command.")
                    print("This should never happen !")
                    raise ProgrammingError
            elif isinstance(descr, SpecialCommand):
                print("Problem in apply_modification_commands.")
                print("The current descriptor list still seems to contain")
                print("replication commands, so it is not yet expanded!!!")
                print("The input to apply_modification_commands() should be")
                print("an expanded descriptor list...")
                raise ProgrammingError
            else:
                if len(current_modifications)>0:
                    mod_descr = ModifiedDescriptor(descr)
                    print("current_modifications:")
                    print(";".join(str(cur_mod) for cur_mod
                                   in current_modifications))
                    for cur_mod in current_modifications:
                        mod_descr.add_modification(cur_mod)
                    mod_descr_list.append(mod_descr)
                else:
                    mod_descr_list.append(descr)
        return mod_descr_list
        #  #]
    def unload_tables(self):
        #  #[
        """
        unload the descriptors for the current BUFR table by removing them
        from the class namespace to allow loading a new table
        """
        del(self.list_of_d_entry_lineblocks)
        self.list_of_d_entry_lineblocks = []

        # reset instance  attributes
        self.table_b   = {}
        self.specials  = {}
        self.modifiers = {}
        self.table_c   = {}
        self.table_d   = {}
        self.list_of_d_entry_lineblocks = []
        self.num_d_blocks = 0

        # reset class attributes
        self.__class__.currently_loaded_B_table = None
        self.__class__.currently_loaded_C_table = None
        self.__class__.currently_loaded_D_table = None
        self.__class__.saved_B_table = None
        self.__class__.saved_C_table = None
        self.__class__.saved_D_table = None
        #  #]
    def add_to_B_table(self, descriptor):
        #  #[
        assert(isinstance(descriptor, Descriptor) == True)
        self.table_b[descriptor.reference] = descriptor
        #  #]
    def add_to_C_table(self, flag_def):
        ref = flag_def.reference
        self.table_c.flag_dict[ref] = flag_def
    def add_to_D_table(self, descriptor):
        #  #[
        assert(isinstance(descriptor, CompositeDescriptor) == True)
        self.table_d[descriptor.reference] = descriptor
        #  #]
    def print_B_table(self):
        #  #[
        for ref in sorted(self.table_b):
            print(str(self.table_b[ref]))
        #  #]
    def print_C_table(self):
        #  #[
        for ref in sorted(self.table_c):
            print('flag table for reference: '+str(ref)+'\n'+
                  str(self.table_c[ref]))
        #  #]
    def print_D_table(self):
        #  #[
        for ref in sorted(self.table_d):
            print(str(self.table_d[ref]))
        #  #]
    def write_B_table(self, fd):
        #  #[
        for ref in sorted(self.table_b):
            # the B BUFR table reading in the ECMWF BUFR library code
            # uses the following format:
            # '(1X,I6,1x,64x,1x,24x,1x,I3,1x,I12,1x,I3)'
            # see: ecmwf_bufr_lib/bufr_000387/bufrdc/btable.F
            # around line 142

            # Note also that some ECMWF B-tables (especially for the
            # CCITTIA5/character string definitions), there seem to be
            # extra fields in the B-table; for example:
            # "CHARACTER                 0    "
            # for other descriptors these 2 fields seem to contain
            # a copy of the unit and unit scale
            # For some descriptors however, especially at the end of the
            # table, these fields are not filled at all.
            # It is not clear to me whether these extra fields
            # are actually used or not.

            # Note also that the BUFR standard actually dus not prescribe
            # anything on the BUFR table format, so ECMWF can choose to
            # do anything it likes to do here ...
            
            b_descr = self.table_b[ref]
            txt = ' %6.6d %-64s %-24s %3i %12i %3i\n' % \
                  (int(b_descr.reference),
                   b_descr.name,
                   b_descr.unit,
                   b_descr.unit_scale,
                   b_descr.unit_reference,
                   b_descr.data_width)
            fd.write(txt)
        #  #]
    def write_C_table(self, fd):
        #  #[
        max_text_length = 64
        for ref in sorted(self.table_c):
            flag_values = self.table_c[ref].flag_dict
            num_keys = len(self.table_c[ref].flag_dict)
            for i, flag_value in enumerate(sorted(self.table_c[ref].flag_dict)):
                text = self.table_c[ref].flag_dict[flag_value]
                this_line = text[:] # take a copy
                text_lines = []
                while this_line:
                    front     = this_line[:max_text_length]
                    remainder = this_line[max_text_length:]
                    text_lines.append(front)
                    this_line = remainder
                    
                num_text_lines = len(text_lines)

                # write first line of text
                if i==0:
                    # this is not python2.6 compatible
                    #fd.write('{:06d} {:04d} {:08d} {:02d} {}\n'.
                    # so use this in stead
                    fd.write('%06d %04d %08d %02d %s\n' %
                             (ref, num_keys, flag_value,
                              num_text_lines, text_lines[0]))
                else:
                    # this is not python2.6 compatible
                    #fd.write('{} {:08d} {:02d} {}\n'.
                    # so use this in stead
                    fd.write('%s %08d %02d %s\n' %
                             (' '*11, flag_value,
                              num_text_lines, text_lines[0]))
                    
                for l in text_lines[1:]:
                    # write remaining lines of text
                    # this is not python2.6 compatible
                    # fd.write('{} {}\n'.format(' '*22, l))
                    # so use this in stead
                    fd.write('%s %s\n' % (' '*22, l))
        #  #]
    def write_D_table(self, fd):
        #  #[
        for ref in sorted(self.table_d):
            # the BUFR table reading in the ECMWF BUFR library code
            # uses the following format: '(1X,I6,I3)'
            # for the first 2 items, and: '(11X,I6)'
            # for the 3rd item.
            # see: ecmwf_bufr_lib/bufr_000387/bufrdc/dtable.F
            # around line 145

            # Note also that there seem to be comment fields following
            # some ECMWF D-table entries, but not often.
            # It is not clear to me if these are used at all.
            
            d_descr = self.table_d[ref]
            n = len(d_descr.descriptor_list)
            for (i, ref_descr) in enumerate(d_descr.descriptor_list):
                if (i == 0):
                    txt = ' %6i %2i %6.6i\n' % \
                          (int(d_descr.reference), n, int(ref_descr.reference))
                else:
                    txt = ' %6s %2s %6.6i\n' % \
                          ('', '', int(ref_descr.reference))
                    
                # txt = str(self.table_d[ref])+'\n'
                fd.write(txt)
        #  #]
    def write_tables(self, table_name):
        #  #[
        b_table_name = 'B'+table_name
        c_table_name = 'C'+table_name
        d_table_name = 'D'+table_name

        fd = open(b_table_name,'w')
        self.write_B_table(fd)
        fd.close()

        fd = open(c_table_name,'w')
        self.write_C_table(fd)
        fd.close()

        fd = open(d_table_name,'w')
        self.write_D_table(fd)
        fd.close()
        #  #]
    def is_defined(self, descr):
        #  #[ check function
        '''
        check whether the given descriptor is available in the current
        set of BUFR tables or not
        '''
        # print('checked: '+str(descr))
        f_val = int(descr/100000.)
        if f_val == 0:
            # check table B
            if descr in self.table_b:
                return True
        if f_val == 1:
            # special class 1 descriptors are not defined in BUFR tables
            return True
        if f_val == 2:
            # special class 2 descriptors are not defined in BUFR tables
            return True
        if f_val == 3:
            # check table D
            if descr in self.table_d:
                return True

        return False
        #  #]
    #  #]

if __name__ == "__main__":
    #  #[ test program
    print("Starting test program:")

    BT = BufrTable(autolink_tablesdir = "tmp_BUFR_TABLES",
                   verbose=False)
    # load BUFR tables using the automatically linked
    # tables defined on the lines above

    par = ''
    if len(sys.argv)>1:
        par = sys.argv[1]
    if par == 'simpletest':
        # simple test on one file only
        bufr_b_table = 'ecmwf_bufrtables/B0000000000099017001.TXT'
        bufr_c_table = 'ecmwf_bufrtables/C0000000000099017001.TXT'
        bufr_d_table = 'ecmwf_bufrtables/D0000000000099017001.TXT'

        BT.load(bufr_b_table)
        print('loaded bufr B table: '+bufr_b_table)
        BT.load(bufr_c_table)
        print('loaded bufr C table: '+bufr_c_table)
        BT.load(bufr_d_table)
        print('loaded bufr D table: '+bufr_d_table)
    
        sys.exit()
    
    # test the available bufr tables
    #TABLE_CODES = ["0000000000098000000",
    #               "0000000000098002001", "0000000000098006000",
    #               "0000000000098006001", "0000000000098013001",
    #               "0000000000098014001"]
    #, "0000000000000014000",
    #, "0000000000254011001"
    # this last one seems only to have a B table but no D table!!!!
    
    handled_orig_names = []

    def check_tablefile(bufr_table):
        #  #[ check consistency of a BUFR table file
        bufr_name = os.path.split(bufr_table)[1]
        table_type = bufr_name[0]
        code = bufr_name[1:]
        
        if not os.path.exists(bufr_table):
            print('ERROR: '+str(table_type)+
                  ' table missing for code: '+str(code))
            return

        realname_bufr_table = os.path.split(os.path.realpath(bufr_table))[1]

        # prevent double checking
        if realname_bufr_table in handled_orig_names: return

        print('appending: ',realname_bufr_table)
        handled_orig_names.append(realname_bufr_table)

        print('='*50)
        print('loading: '+bufr_table)
        print('='*50)
        comments_file = 'comments_during_load_of_'+realname_bufr_table
        saved_sys_stdout = sys.stdout
        try:
            sys.stdout = open(comments_file,'wt')
            BT.load(bufr_table)
            sys.stdout.close()
            sys.stdout = saved_sys_stdout
        except:
            sys.stdout = saved_sys_stdout
            print('ERROR: load failed !!!')
        if os.path.exists(comments_file):
            # get the filesize and remove empty files
            statresult = os.stat(comments_file)
            filesize = statresult[stat.ST_SIZE]
            if filesize == 0:
                os.remove(comments_file)
        #  #]
            

    PATH = "ecmwf_bufrtables"
    bufr_b_tables = glob.glob(os.path.join(PATH, "B*.TXT"))
    # bufr_b_tables = glob.glob(os.path.join(PATH, "B*.distinct"))
    for bufr_b_table in bufr_b_tables:

        bufr_b_name = os.path.split(bufr_b_table)[1]
        code = bufr_b_name[1:]
        bufr_c_name = 'C'+code
        bufr_d_name = 'D'+code
        
        bufr_c_table = os.path.join(PATH, bufr_c_name)
        bufr_d_table = os.path.join(PATH, bufr_d_name)

        check_tablefile(bufr_b_table)
        check_tablefile(bufr_c_table)
        check_tablefile(bufr_d_table)
        
        BT.unload_tables()
    
    # test application of modification commands:
    # this is D-descriptor 331004
    
    # load the ADM-Aeolus L2B-product BUFR table
    PATH = "alt_bufr_tables"
    TABLE_CODE = "0000000000098015001"

    bufr_b_table = os.path.join(PATH, "B"+TABLE_CODE+".TXT")
    bufr_d_table = os.path.join(PATH, "D"+TABLE_CODE+".TXT")
    
    print('='*50)
    print('loading: '+bufr_b_table)
    print('='*50)
    BT.load(bufr_b_table)
    
    print('='*50)
    print('loading: '+bufr_d_table)
    print('='*50)
    BT.load(bufr_d_table)

    print('='*50)
    print('doing some custom modification tests')
    print('='*50)
    CODES = ["207001", # = modifier
             "005001", # = LATITUDE (HIGH ACCURACY)  [DEGREE]
             "006001", # = LONGITUDE (HIGH ACCURACY) [DEGREE]
             "207000"] # = end of modifier   
    DESCR_LIST = []
    for c in CODES:
        DESCR_LIST.append(BT.get_descr_object(int(c, 10)))
    print("DESCR_LIST = "+str(DESCR_LIST))
    
    MOD_DESCR_LIST = BT.apply_modification_commands(DESCR_LIST)
    
    #  #]
    
