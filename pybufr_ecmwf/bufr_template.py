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

#  #]

class BufrTemplate:
    #  #[
    """
    a class of to help create a BUFR template in a more structured way
    """
    
    #  #[ class constants
    
    # define the delayed replication code
    Delayed_Descr_Repl_Factor = int('031001', 10)

    #  #]
    def __init__(self, max_nr_descriptors):
        #  #[
        self.max_nr_descriptors = max_nr_descriptors
        self.unexpanded_descriptor_list = []
        self.nr_of_delayed_repl_factors = 0
        self.del_repl_max_nr_of_repeats_list = []
        #  #]
    def add_descriptor(self, descriptor):
        #  #[
        """
        add a descriptor to the template
        """
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
                                       *descriptors):
        #  #[
        """
        use delayed replication to add a list of descriptors to the template
        """
        nr_of_descriptors = len(descriptors)
        print('adding delayed replication for ', nr_of_descriptors,
              ' descriptors')
        print('replicating them at most ', max_nr_of_repeats, ' times')
        repl_code = self.get_replication_code(nr_of_descriptors, 0)
        self.unexpanded_descriptor_list.append(repl_code)
        self.unexpanded_descriptor_list.append(self.Delayed_Descr_Repl_Factor)
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
        return repl_factor
        #  #]
    #  #]
