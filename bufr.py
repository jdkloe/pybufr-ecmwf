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
import os
from pybufr_ecmwf import RawBUFRFile
#  #]

class Singleton(object):
    # this Singleton class is a modified version of the one
    # used by Guido van Rossum in his examples in his paper
    # "Unifying types and classes in Python 2.2", see:
    # http://www.python.org/download/releases/2.2.3/descrintro/
    # Its purpose is to have only one instance for each different
    # Descriptor reference number. If another instance is created with
    # the same reference number, this will actually just be a pointer
    # to the already existing instance, and not a totally new instance.
    # This way a huge amount of memory can be saved for large
    # BUFR templates/messages.
    def __new__(cls, *args, **kwds):
        #  #[
        #print "class Singleton: calling __new__"    
        if len(args)>0:
            # use the first arg, in case of Descriptors this is the
            # reference number, as key in the instance dict
            val = args[0]
        else:
            # note: since this __new__ is called with the same arguments
            # as the cls.__init__ method, use the name init in this message
            # to make more clear to the user where the problem is.
            print "ERROR: at least one arg expected in init function !"
            raise AttributeError
        
        # the next line returns None if __instance_dict__ does not yet exist
        id = cls.__dict__.get("__instance_dict__")
        if id is None:
            # create a new dict to hold the instances of this class
            # to allow only one instance for each int val used in init.
            # NOTE THAT THIS WILL BE A CLASS VARIABLE
            # NOT AN INSTANCE VARIABLE
            # so all instances of this class will use the same dict
            cls.__instance_dict__ = id = {}

        if id.has_key(val):
            # ok, we already had an instance for this value, so return
            # a pointer to it
            return id[val]

        # no instance yet exists for this value, so create a new one
        cls.__instance_dict__[val] = instance = object.__new__(cls)
        instance.init(*args, **kwds)
        return instance
    #  #]
    def init(self, *args, **kwds):
    #  #[
        #print "class Singleton: calling init"
        pass
    #  #]

class Descriptor(Singleton):
    def __init__(self,reference,name,unit,unit_scale,
                 unit_reference,data_width):
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
    def __init__(self):
        #  #[
        self.table_B = {} # dict of desciptor-objects
        self.table_D = {} # dict of composite-descriptor-objects
        #  #]
    def load(self,file):
        #  #[

        #print "inspecting file: ",file
        #maxlen=0
        #for line in open(file,'rt'):
        #    l=line.replace('\r','').replace('\n','')
        #    if len(l)>maxlen:
        #        maxlen = len(l)
        #print "longest line is: ",maxlen

        (path,base) = os.path.split(file)
        if base[0].upper()== 'B':
            self.load_B_table(file)
        elif base[0].upper()== 'D':
            self.load_D_table(file)
        else:
            print "ERROR: don;t know what table this is"
            print "(path,base) = ",(path,base)
            raise IOError
        #  #]
    def load_B_table(self,file):
        #  #[
        print "loading B table from file: ",file
        nr_of_ignored_problematic_entries = 0
        for (i,line) in enumerate(open(file,'rt')):
            success = True
            l=line.replace('\r','').replace('\n','')
            # example of the expected format (156 chars per line):
            # " 005001 LATITUDE (HIGH ACCURACY)                                         DEGREE                     5     -9000000  25 DEGREE                    5         7"
            if len(l)>=118:
                txt_reference       = l[0:8] # 8 characters
                txt_name            = l[8:73] # 64 characters
                txt_unit            = l[73:98] # 24 characters
                txt_unit_scale      = l[98:102] # 4 characters
                txt_unit_reference  = l[102:115] # 14 characters
                txt_data_width      = l[115:118] # 4 characters
                # sometimes additional info seems present, but
                # I don't know yet the definition used for that
                txt_additional_info = ''
                if len(l)>118:
                    txt_additional_info = l[118:]
            else:
                success = False
                nr_of_ignored_problematic_entries += 1
                print "ERROR: unexpected format in table B file..."
                print "linecount: ",i
                print "line: ["+l+"]"
                print "Line is too short, it should hold at least 118 characters"
                print "but seems to have only: ",len(l)," characters."
                #print "txt_reference       = ["+l[0:8]+"]"
                #print "txt_name            = ["+l[8:73]+"]"
                #print "txt_unit            = ["+l[73:98]+"]"
                #print "txt_unit_scale      = ["+l[98:102]+"]"
                #print "txt_unit_reference  = ["+l[102:115]+"]"
                #print "txt_data_width      = ["+l[115:118]+"]"
                print "You could report this to the creator of this table "+\
                      "since this should never happen."
                print "Ignoring this entry ....."

            if (success):
                try:
                    reference = int(txt_reference,10)
                    unit_scale = int(txt_unit_scale)
                    unit_reference = int(txt_unit_reference)
                    data_width = int(txt_data_width)
                    
                    # remove excess spaces from the string before storing
                    name = txt_name.strip()
                    unit = txt_unit.strip()
                    
                except:
                    success = False
                    nr_of_ignored_problematic_entries += 1
                    print "ERROR: unexpected format in table B file..."
                    print "Could not convert one of the numeric fields to integer."
                    print "txt_reference       = ["+txt_reference+"]"
                    print "txt_unit_scale      = ["+txt_unit_scale+"]"
                    print "txt_unit_reference  = ["+txt_unit_reference+"]"
                    print "txt_data_width      = ["+txt_data_width+"]"
                    print "Ignoring this entry ....."

            if (success):
                # add descriptor object to the list
                b_descr = Descriptor(reference,name,unit,
                                     unit_scale,unit_reference,data_width)
                if not self.table_B.has_key(reference):
                    #print "adding descr. key ",reference
                    self.table_B[reference] = b_descr
                else:
                    print "ERROR: multiple descriptors with identical reference"
                    print "number found. This should never happen !!!"
                    print "problematic descriptor is: ",b_descr
                    print "Ignoring this entry ....."
                    nr_of_ignored_problematic_entries += 1

        print "-------------"
        if (nr_of_ignored_problematic_entries>0):
            print "nr_of_ignored_problematic_entries = ",\
                  nr_of_ignored_problematic_entries
        print "Loaded: ",len(self.table_B)," table B entries"
        print "-------------"
        print "self.table_B[006001] = ",self.table_B[int('006001',10)]
        print "-------------"

        #  #]
    def load_D_table(self,file):
        #  #[
        print "loading D table from file: ",file
        print "not yet implemented"
        #nr_of_ignored_problematic_entries = 0
        #for (i,line) in enumerate(open(file,'rt')):
        #    l=line.replace('\r','').replace('\n','')
        #  #]

    #  possible additional methods:
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
     
if __name__ == "__main__":
        #  #[ test program
        print "Starting test program:"
        BT = BufrTable()
        BT.load("tmp_BUFR_TABLES/B0000000000098015001.TXT")
        BT.load("tmp_BUFR_TABLES/D0000000000098015001.TXT")
        #  #]
