#!/usr/bin/env python

"""
This file defines the BufrTemplate class, to allow easier
construction of BUFR templates
"""

#  #[ documentation
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
# Written by: J. de Kloe, KNMI (www.knmi.nl), Initial version 12-Nov-2009    
#
# License: GPL v2.
#
#  #]
#  #[ imported modules
from __future__ import (absolute_import, division,
                        print_function) #, unicode_literals)

#import os          # operating system functions
#import sys         # system functions
from . import bufr_table
#  #]

class BufrTemplate:
    #  #[
    """
    a class of to help create a BUFR template in a more structured way
    """
    
    #  #[ class constants
    
    Delayed_Descr_Repl_Factor = int('031001', 10)
    Extended_Delayed_Descr_Repl_Factor = int('031002', 10)
    
    #  #]
    def __init__(self):
        #  #[
        self.unexpanded_descriptor_list = []
        self.nr_of_delayed_repl_factors = 0
        self.del_repl_max_nr_of_repeats_list = []
        #  #]
    def add_descriptor(self, descriptor):
        #  #[
        """
        add a descriptor to the template
        """
        print('adding descriptor: ',descriptor)
        self.unexpanded_descriptor_list.append(descriptor)
        #  #]
    def add_descriptors(self, *descriptors):
        #  #[
        """
        add a list of descriptors to the template
        """
        nr_of_descriptors = len(descriptors)
        print('adding ', nr_of_descriptors, ' descriptors')
        self.unexpanded_descriptor_list.extend(descriptors)
        #  #]
    def add_delayed_replic_descriptors(self, max_nr_of_repeats,
                                       *descriptors, **kwargs):
        #  #[
        """
        use delayed replication to add a list of descriptors to the template
        """
        nr_of_descriptors = len(descriptors)
        if 'extended' in kwargs:
            repl_factor = self.Extended_Delayed_Descr_Repl_Factor
            print('adding extended delayed replication for ', nr_of_descriptors,
                  ' descriptors')
        else:
            repl_factor = self.Delayed_Descr_Repl_Factor
            print('adding delayed replication for ', nr_of_descriptors,
                  ' descriptors')
        print('replicating them at most ', max_nr_of_repeats, ' times')
        repl_code = self.get_replication_code(nr_of_descriptors, 0)
        self.unexpanded_descriptor_list.append(repl_code)
        self.unexpanded_descriptor_list.append(repl_factor)
        self.unexpanded_descriptor_list.extend(descriptors)
        self.nr_of_delayed_repl_factors = self.nr_of_delayed_repl_factors + 1
        self.del_repl_max_nr_of_repeats_list.append(max_nr_of_repeats)
        #  #]
    def add_replicated_descriptors(self, nr_of_repeats, *descriptors):
        #  #[
        """
        use normal replication to add a list of descriptors to the template
        """
        nr_of_descriptors = len(descriptors)
        print('adding replication for ', nr_of_descriptors, ' descriptors')
        print('replicating them ', nr_of_repeats, ' times')
        repl_code = self.get_replication_code(nr_of_descriptors,
                                              nr_of_repeats)
        self.unexpanded_descriptor_list.append(repl_code)
        self.unexpanded_descriptor_list.extend(descriptors)
        #  #]
    def get_replication_code(self, num_descriptors, num_repeats):
        #  #[
        """
        helper function to generate the replication code
        """
        repl_factor = 100000 + num_descriptors*1000 + num_repeats
        # for example replicating 2 descriptors 25 times will
        # be encoded as: 102025
        # for delayed replication, set num_repeats to 0
        # then add the Delayed_Descr_Repl_Factor after this code
        return bufr_table.SpecialCommand(repl_factor)
        #  #]
    def get_unexpanded_descriptor_list(self):
        #  #[
        ''' return a simple list (without nesting) if needed '''
        unexpanded_descriptor_list = []
        for descr in self.unexpanded_descriptor_list:
            if type(descr) == list:
                unexpanded_descriptor_list.extend(descr)
            else:
                unexpanded_descriptor_list.append(descr)
        return unexpanded_descriptor_list
        #  #]
    def get_max_size(self, descriptor_list, bufrtables):
        #  #[
        count = 0
        # ensure all descriptors are instances of bufr_table.Descriptor
        normalised_descriptor_list = \
                   bufrtables.normalise_descriptor_list(descriptor_list)
        #print('debug: normalised_descriptor_list = ',
        #      list(str(d) for d in normalised_descriptor_list))
        while normalised_descriptor_list:
            descr = normalised_descriptor_list.pop(0)
            # print('handling descr: ',descr)
            if isinstance(descr, (bufr_table.SpecialCommand,
                                  bufr_table.Replicator,
                                  bufr_table.DelayedReplicator)):
                descr_count = int((descr.reference-100000)/1000)
                if int(descr.reference % 1000) == 0:
                    # print('delayed replicator found !!')
                    # pop the obligatory 31001 code as well
                    normalised_descriptor_list.pop(0)
                    # count the obligatory 31001 code as well
                    count += 1
                    repeat_count = self.del_repl_count_list.pop(0)
                elif int(descr.reference/100000) == 1:
                    # print('replicator found !!')
                    repeat_count = int(descr.reference % 1000)
                    
                # print('repeat_count = ', repeat_count)

                repl_descr_list = \
                                normalised_descriptor_list[:descr_count]
                normalised_descriptor_list = \
                                normalised_descriptor_list[descr_count:]
                # print('repl_descr_list = ',
                #       ';'.join(str(d.reference) for d in repl_descr_list))
                # print('it has a size of: ',self.get_max_size(repl_descr_list,
                #                                              bufrtables))
                count += repeat_count*self.get_max_size(repl_descr_list,
                                                        bufrtables)
            elif isinstance(descr, bufr_table.CompositeDescriptor):
                # a composite D-table descriptor
                # print('D: ',descr)
                count += self.get_max_size(descr.descriptor_list,
                                           bufrtables)
            else:
                # a normal B-table descriptor
                count += descr.get_count()
            
        return count
        #  #]
    def get_max_nr_expanded_descriptors(self, bufrtables):
        #  #[
        # init list that is modified in the recursive get_max_size function
        self.del_repl_count_list = self.del_repl_max_nr_of_repeats_list[:]
        # get the max size
        s = self.get_max_size(self.unexpanded_descriptor_list,bufrtables)
        # print('s=',s)
        return s
        #  #]
    #  #]
