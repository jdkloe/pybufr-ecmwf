#!/usr/bin/env python

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
# License: GPL v2.
#  #]
#  #[ imported modules
from pybufr_ecmwf import RawBUFRFile
#  #]

class Descriptor:
    pass
    #  ==>descriptor-code (table reference)
    #  ==>descriptive text (element name)
    #  ==>unit text (element unit)
    #  ==>offset (reference value)
    #  ==>num bits (data width)
    #  ==>etc.

class Replicator(Descriptor):
    pass
    #  ==>replication-count
    #  ==>list-of-descriptor-objects = []

class DelayedReplicator(Descriptor):
    pass
    #  ==>maximum-replication-count = 4
    #  ==>actual-replication-count-list ] [1,2,3,4]
    #  ==>list-of-descriptor-objects = []

class CompositeDescriptor(Descriptor): #[table D entry]
    pass
    #  ==>descriptor code
    #  ==>list-of-descriptor-objects = []

class BufrTable:
    pass
    #  ==>table-B = [list of desciptor-objects]
    #  ==>table-D = [list of composite-descriptor-objects]
    #  methods:
    #  ==>read-tables
    #  ==>write-tables

class DataValue:
    pass
    #  ==>value or string-value
    #  ==>already filled or not?
    #  ==>pointer to the associated descriptor object

class BUFRMessage: # [moved here from pybufr_ecmwf.py]
    pass
    #  ==>properties-list = [sec0,sec1,sec2,sec3 data]
    #  ==>list-of-descriptor-objects = []
    #  ==>finish (set num subsets, num delayed replications)
    #  ==>2D-data-array of data objects (num subsets x expanded num descriptors)
    #
    # possible methods:
    # -add_descriptor
    # -expand_descriptorList
    # -encode
    # -decode
    # -print_sections_012
    # -get_descriptor_properties
    # -fill_one_real_value
    # -fill_one_string_value
    # -get_one_real_value
    # -get_one_string_value
    # -...


class BUFRFile(RawBUFRFile):
    pass
    # bufr-file [can reuse much functionality from what I have now in the
    #            RawBUFRFile class in pybufr_ecmwf.py]
    #  ==>some meta data
    #  ==>list-of-bufr-msgs = []
     
