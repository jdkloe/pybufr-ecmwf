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
# License: GPL v2.
#  #]
#  #[ imported modules
import os
import sys
import glob
#  #]

class ProgrammingError(Exception):
    """ an exception to indicate that a progromming error seems
    present in the code (this should be reported to the author) """
    pass

class Singleton(object):
    #  #[ explanation
    """
    this Singleton class is a modified version of the one
    used by Guido van Rossum in his examples in his paper
    "Unifying types and classes in Python 2.2", see:
    http://www.python.org/download/releases/2.2.3/descrintro/
    Its purpose is to have only one instance for each different
    Descriptor reference number. If another instance is created with
    the same reference number, this will actually just be a pointer
    to the already existing instance, and not a totally new instance.
    This way a huge amount of memory can be saved for large
    BUFR templates/messages.
    """
    #  #]
    #  #[
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
            errtxt = "ERROR: at least one arg expected in init function !"
            raise AttributeError(errtxt)
        
        # the next line returns None if __instance_dict__ does not yet exist
        idct = cls.__dict__.get("__instance_dict__")
        if idct is None:
            # create a new dict to hold the instances of this class
            # to allow only one instance for each int val used in init.
            # NOTE THAT THIS WILL BE A CLASS VARIABLE
            # NOT AN INSTANCE VARIABLE
            # so all instances of this class will use the same dict
            cls.__instance_dict__ = idct = {}

        if idct.has_key(val):
            # ok, we already had an instance for this value, so return
            # a pointer to it, but first check if the init parameters
            # are identical
            instance = idct[val]
            instance.checkinit(*args, **kwds)
            return instance

        # no instance yet exists for this value, so create a new one
        cls.__instance_dict__[val] = instance = object.__new__(cls)
        #instance.init(*args, **kwds)
        return instance
    #  #]
    #def init(self, *args, **kwds):
        #  #[
        #print "class Singleton: calling init"
        #pass
        #  #]
    def checkinit(self, *args, **kwargs):
        #  #[
        """
        classes that inherit from this Singleton class should
        implement this function to verify that the additional
        args and kwargs are identical to the one used for an already
        existing instance of the class.
        """
        pass
        #  #]
    #  #]

class Descriptor(Singleton):
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
    def checkinit(self, reference, name, unit, unit_scale,
                  unit_reference, data_width):
        #  #[
        """
        a function to be called when an instance is created for a
        descriptor that had been instantiated before. It checks the instance
        properties to make sure we have no double descriptors with
        differing attributes (which would mean a serious design problem
        in the BUFR files and/or template)
        """
        try:
            assert(self.reference      == reference)
            assert(self.name           == name)
            assert(self.unit           == unit)
            assert(self.unit_scale     == unit_scale)
            assert(self.unit_reference == unit_reference)
            assert(self.data_width     == data_width)
        except AssertionError as aerr:
            print 'checkinit check failed !!!'
            print
            print "self.reference      = ", self.reference   , \
                  "reference           = ", reference
            print "self.name           = ", self.name        , \
                  "name                = ", name
            print "self.unit           = ", self.unit        , \
                  "unit                = ", unit
            print "self.unit_scale     = ", self.unit_scale  , \
                  "unit_scale          = ", unit_scale
            print "self.unit_reference = ", self.unit_reference, \
                  "unit_reference      = ", unit_reference
            print "self.data_width     = ", self.data_width  , \
                  "data_width          = ", data_width
            raise aerr
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
class ModificationCommand(Descriptor):
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
        print "ERROR: handling this modification is not fully implemented yet:"
        print self
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
        print "ERROR: handling this modification is not fully implemented yet:"
        print self
        raise NotImplementedError
        #  #]
    def check_matches(self, descr):
        #  #[
        """
        check whether a clear command matches a change command
        """
        
        #print "end modification: ", str(self)
        #print "seems to match modification: ", str(d)

        if self.xx_ == "01" or self.xx_ == "07":
            if ((self.yyy == "000" and descr.yyy != "000") or
                (descr.yyy == "000" and self.yyy != "000")   ):
                if self.xx_ == descr.xx_:
                    return True
                else:
                    return False
            else:
                print "ERROR: modification start-and-end do not match !"
                print "problem in check_matches."
                print "end modification: ", str(self)
                print "seems to match modification: ", str(descr)
                raise IOError
        else:
            print "ERROR: handling this modification is not "+\
                  "fully implemented yet:"
            print self
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
class SpecialCommand(Descriptor):
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
class Replicator(Descriptor):
    #  #[
    """
    a base class for replicators
    """
    def __init__(self):
        pass
    def checkinit(self):
        """
        a function to be called when an instance is created for a
        replication command that had been instantiated before.
        """
        pass
    #  ==>replication-count
    #  ==>list-of-descriptor-objects = []
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

class CompositeDescriptor(Descriptor): #[table D entry]
    #  #[
    """
    a base class for composite descriptors (table D entries)
    """
    def __init__(self, reference, descriptor_list, comment, parent):
        #  #[
        self.reference = reference
        self.descriptor_list = descriptor_list
        self.comment = comment
        self.parent = parent
        #  #]
    def __str__(self):
        #  #[
        txt = "reference: ["+str(self.reference)+"] "+\
              "refers to: "+\
              ";".join(str(d.reference) for d in self.descriptor_list)
        return txt
        #  #]
    # to remove:
    def expand(self):
        #  #[
        """ a function to expand a table D entry into a list of
        table B entries.
        """
        expanded_descriptor_list = []
        num_descr_to_skip = 0
        print '==> expanding: %6.6i' % self.reference
        for (i,descr) in enumerate(self.descriptor_list):

            # for replicated blocks, several descriptors may have been
            # added already (maybe several times) to the
            # expanded_descriptor_list, so this trick allows them to be
            # skipped when continuing the loop
            if num_descr_to_skip>0:
                num_descr_to_skip -= 1
                print 'skipping: %6.6i' % descr.reference
                continue
            
            f_val = int(descr.reference/100000.)
            if f_val==3:
                # this is another table D entry, so expand recursively
                print 'adding expanded version of: %6.6i' % \
                      descr.reference
                tmp_list = self.parent.table_d[descr.reference].expand()
                expanded_descriptor_list.extend(tmp_list)
            elif f_val==1:
                # this is a replication operator
                print 'handling replication operator: %6.6i' % descr.reference
                xx  = int((descr.reference-100000.)/1000)
                yyy = (descr.reference-100000-1000*xx)
                print 'xx = ',xx,' = num. descr. to replicate'
                print 'yyy = ',yyy,' = repl. count'

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
                print 'descr_list_to_be_replicated = ',\
                      ';'.join(str(s.reference) for s
                               in descr_list_to_be_replicated)
                # do the replication
                for j in range(yyy):
                    for repl_descr in descr_list_to_be_replicated:
                        repl_descr_f_val = int(repl_descr.reference/100000.)
                        if repl_descr_f_val==3:
                            print '%i: adding expanded version of: %6.6i' % \
                                  (j, repl_descr.reference)
                            expanded_descriptor_list.extend(repl_descr.expand())
                        else:
                            print '%i: adding copy of: %6.6i' % \
                                  (j, repl_descr.reference)
                            expanded_descriptor_list.\
                                     append(repl_descr.reference)
                
                # print 'TESTJOS: breakpoint'
                # sys.exit(1)
                
            else:
                print 'adding: %6.6i' % descr.reference
                expanded_descriptor_list.append(descr.reference)
                
        return expanded_descriptor_list
        #  #]    
    def checkinit(self, reference, descriptor_list, comment, parent):
        #  #[

        """
        a function to be called when an instance is created for a
        composite descriptor that had been instantiated before.
        It checks the instance
        properties to make sure we have no double descriptors with
        differing attributes (which would mean a serious design problem
        in the BUFR files and/or template)
        """
        assert(self.reference       == reference)
        assert(self.descriptor_list == descriptor_list)
        assert(self.comment         == comment)
        assert(self.parent          == parent)

        #  #]
    #  #]

class BufrTable:
    #  #[
    """
    a base class for BUFR B and D tables    
    """
    def __init__(self,
                 autolink_tablesdir = "tmp_BUFR_TABLES",
                 tables_dir = None,
                 verbose=True):
        #  #[
        self.table_b   = {} # dict of desciptor-objects (f=0)
        self.specials  = {} # dict of specials  (f=1)
        self.modifiers = {} # dict of modifiers (f=2)
        self.table_d   = {} # dict of composite-descriptor-objects (f=3)

        self.verbose = verbose
        
        self.autolink_tables = True
        if (tables_dir is not None):
            # dont use autolinking if the user provided a tables dir
            self.autolink_tables = False
            self.tables_dir = tables_dir
            
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
            self.set_bufr_tables_dir(tables_dir)

        # used for the decoding of table D
        self.list_of_d_entry_lineblocks = []
        self.num_d_blocks = 0

        #  #]
    def expand_descriptor_list(self, descr_list):
        #  #[
        """ a function to expand a descriptor list, holding table D entries
        and replicators etc. into a clean list of table B entries (with f=0)
        and modification operators (with f=2).
        Descr_list may be a list of descriptor instances, or a list of
        integer reference numbers, or a list of strings that can be
        converted to a list of reference numbers.
        """
        #  #[ normalise the list to hold only Desciptor instances
        normalised_descriptor_list = []
        for tmp_descr in descr_list:

            if isinstance(tmp_descr, Descriptor):
                descr = tmp_descr
            else:
                if (type(tmp_descr) == str):
                    int_descr = int(tmp_descr)
                elif (type(tmp_descr) == int):
                    int_descr = tmp_descr
                else:
                    print 'ERROR: type(tmp_descr): ',type(tmp_descr)
                    print 'tmp_descr = ',tmp_descr
                f_val = int(int_descr/100000.)
                if f_val==0:
                    # this one should already be in the table_b dictionary
                    # otherwise the wrong table_b is loaded
                    descr = self.table_b[int_descr]
                if f_val==1:
                    if not self.specials.has_key(int_descr):
                        new_descr = SpecialCommand(int_descr)
                        self.specials[int_descr] = new_descr
                    descr = self.specials[int_descr]
                if f_val==2:
                    if not self.modifiers.has_key(int_descr):
                        new_descr = ModificationCommand(int_descr)
                        self.modifiers[int_descr] = new_descr
                    descr = self.modifiers[int_descr]
                if f_val==3:
                    # this one should already be in the table_d dictionary
                    # otherwise the wrong table_d is loaded
                    descr = self.table_d[int_descr]

            normalised_descriptor_list.append(descr)
        #  #]
        #  #[ do the actual expansion
        expanded_descriptor_list = []
        num_descr_to_skip = 0
        for (i,descr) in enumerate(normalised_descriptor_list):

            # for replicated blocks, several descriptors may have been
            # added already (maybe several times) to the
            # expanded_descriptor_list, so this trick allows them to be
            # skipped when continuing the loop
            if num_descr_to_skip>0:
                num_descr_to_skip -= 1
                print 'skipping: %6.6i' % descr.reference
                continue
            
            f_val = int(descr.reference/100000.)
            if f_val==3:
                # this is another table D entry, so expand recursively
                print 'adding expanded version of: %6.6i' % \
                      descr.reference
                tmp_list = self.expand_descriptor_list(\
                                self.table_d[descr.reference].descriptor_list)
                expanded_descriptor_list.extend(tmp_list)
                print 'done expanding: %6.6i' % \
                      descr.reference
            elif f_val==1:
                # this is a replication operator
                print 'handling replication operator: %6.6i' % descr.reference
                xx  = int((descr.reference-100000.)/1000)
                yyy = (descr.reference-100000-1000*xx)
                print 'xx = ',xx,' = num. descr. to replicate'
                print 'yyy = ',yyy,' = repl. count'

                # note: for now only handle normal replication
                # since I have no testfile at hand with delayed replication.
                # In case of delayed replication, the replication operator
                # is followed by a maximum replication count, and I believe
                # the expansion of the descriptor list should assume the
                # maximum (but this is to be confirmed)
                replication_count = yyy
                num_descr_to_skip = xx

                # note that i points to the replication operator
                descr_list_to_be_replicated = \
                      normalised_descriptor_list[i+1:i+1+xx]
                print 'descr_list_to_be_replicated = ',\
                      ';'.join(str(s.reference) for s
                               in descr_list_to_be_replicated)
                # do the replication
                for j in range(yyy):
                    for repl_descr in descr_list_to_be_replicated:
                        repl_descr_f_val = int(repl_descr.reference/100000.)
                        if repl_descr_f_val==3:
                            print '%i: adding expanded version of: %6.6i' % \
                                  (j, repl_descr.reference)
                            expanded_descriptor_list.extend(repl_descr.expand())
                        else:
                            print '%i: adding copy of: %6.6i' % \
                                  (j, repl_descr.reference)
                            expanded_descriptor_list.\
                                     append(repl_descr.reference)
                print 'done handling replication operator: %6.6i' % \
                      descr.reference
            else:
                print 'adding: %6.6i' % descr.reference
                expanded_descriptor_list.append(descr.reference)
        #  #]
        return expanded_descriptor_list
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
        if self.table_b.has_key(reference):
            return self.table_b[reference]
        if self.table_d.has_key(reference):
            return self.table_d[reference]
        # get 1st digit
        f_val = int(reference/100000.)
        # note: the cases f == 0 should already be part of table_b
        # and the cases f == 3 should already be part of table_d
        if f_val == 1:
            # this is a special code
            if self.specials.has_key(reference):
                return self.specials[reference]
            else:
                # this is a new special
                if self.verbose:
                    print "adding special: ", reference
                special = SpecialCommand(reference)
                self.specials[reference] = special
                return special
        if f_val == 2:
            # this is a modifier
            if self.modifiers.has_key(reference):
                return self.modifiers[reference]
            else:
                # this is a new modifier
                if self.verbose:
                    print "adding modifier: ", reference
                modifier = ModificationCommand(reference)
                self.modifiers[reference] = modifier
                return modifier
            
        return None
        #  #]
    def load(self, t_file):
        #  #[
        """
        load a BUFR B or D table from file
        """
#        e = os.environ
#        tables_dir = e["BUFR_TABLES"]
#        if not os.path.exists(os.path.join(tables_dir,bfile)):
#            print "ERROR: could not find B-table file"
#            print "Tried to load: ", bfile
#            print "BUFR_TABLES dir = ", tables_dir
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
                    print "autolinking table file: ", t_file
                    self.autolinkbufrtablefile(t_file)

        #print "inspecting file: ", t_file
        #maxlen = 0
        #for line in open(t_file, 'rt'):
        #    l = line.replace('\r', '').replace('\n', '')
        #    if len(l)>maxlen:
        #        maxlen = len(l)
        #print "longest line is: ", maxlen

        (path, base) = os.path.split(tablefile)
        if base[0].upper() == 'B':
            self.load_b_table(tablefile)
        elif base[0].upper() == 'D':
            self.load_d_table(tablefile)
        else:
            print "ERROR: don;t know what table this is"
            print "(path, base) = ", (path, base)
            raise IOError
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
            print "programming error in autolinkbufrtablefile!!!"
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
            print "trying pattern: ", \
                  os.path.join(ecmwf_bufr_tables_dir, pattern)+'*'
            matches = glob.glob(os.path.join(ecmwf_bufr_tables_dir,
                                             pattern)+'*')
            print "matches = ", matches
            print "len(matches) = ", len(matches)
            if len(matches)>0:
                source      = matches[0]
                destination = os.path.join(self.tables_dir, t_file)
                if (not os.path.exists(destination)):
                    print "making symlink from ", source, \
                          " to ", destination
                    os.symlink(source, destination)
                break

        #  #]
    def load_b_table(self, bfile):
        #  #[
        """
        load BUFR table B from file
        """
        print "loading B table from file: ", bfile
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
                print "ERROR: unexpected format in table B file..."
                print "linecount: ", i
                print "line: ["+line_copy+"]"
                print "Line is too short, it should hold at "+\
                      "least 118 characters"
                print "but seems to have only: ", len(line_copy), " characters."
                #print "txt_reference       = ["+line_copy[0:8]+"]"
                #print "txt_name            = ["+line_copy[8:73]+"]"
                #print "txt_unit            = ["+line_copy[73:98]+"]"
                #print "txt_unit_scale      = ["+line_copy[98:102]+"]"
                #print "txt_unit_reference  = ["+line_copy[102:115]+"]"
                #print "txt_data_width      = ["+line_copy[115:118]+"]"
                print "You could report this to the creator of this table "+\
                      "since this should never happen."
                print "Ignoring this entry ....."

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
                        print "Ignoring a reserved entry: "+txt_reference
                    else:
                        print "ERROR: unexpected format in table B file..."
                        print "Could not convert one of the numeric "+\
                              "fields to integer."
                        print "txt_reference       = ["+txt_reference+"]"
                        print "txt_unit_scale      = ["+txt_unit_scale+"]"
                        print "txt_unit_reference  = ["+txt_unit_reference+"]"
                        print "txt_data_width      = ["+txt_data_width+"]"
                        print "txt_additional_info = ["+txt_additional_info+"]"
                        print "Ignoring this entry ....."

            if (success):
                # add descriptor object to the list
                b_descr = Descriptor(reference, name, unit,
                                     unit_scale, unit_reference, data_width)
                if not self.table_b.has_key(reference):
                    #print "adding descr. key ", reference
                    self.table_b[reference] = b_descr
                else:
                    print "ERROR: multiple table B descriptors with "+\
                          "identical reference"
                    print "number found. This should never happen !!!"
                    print "problematic descriptor is: ", b_descr
                    print "Ignoring this entry ....."
                    nr_of_ignored_probl_entries += 1

        print "-------------"
        if self.verbose:
            if (nr_of_ignored_probl_entries>0):
                print "nr_of_ignored_probl_entries = ", \
                      nr_of_ignored_probl_entries
        print "Loaded: ", len(self.table_b), " table B entries"
        print "-------------"
        #print "self.table_b[006001] = ", self.table_b[int('006001', 10)]
        #print "-------------"

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
        #print "trying descriptor ", ref_reference
        descr = self.get_descr_object(ref_reference)
        if (descr == None):
            postpone = True
            if report_unhandled:
                print "---"
                print "descriptor ", ref_reference, \
                      " is never defined but is used by"
                print "D-table entry ", reference, " (line ", line_nr, ")"
                #print "postponing processing of this one"
        else:
            # add this object to the list
            #print "adding descriptor with ref: ", ref_reference
            descriptor_list.append(descr)

        return postpone
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
            #print "d_entry_block=", d_entry_block

            # ensure i and line are defined,
            # even if d_entry_block is an empty list
            i = 0
            line = ''
            
            for (j, (i, line)) in enumerate(d_entry_block):
                #print j, "considering line ["+line+"]"
                parts = line[:18].split()
                if j == 0: # startline
                    #print "is a start line"
                    reference     = int(parts[0], 10)
                    count         = int(parts[1])
                    ref_reference = int(parts[2], 10)
                    comment        = ''
                    postpone = False
                    descriptor_list = []
                    if len(line)>18:
                        comment = line[18:]
                else: # continuation_line:
                    #print "is a continuation line"
                    ref_reference = int(parts[0], 10)
                    extra_comment  = ''
                    if len(line)>18:
                        # todo: check if the ref_reference is maybe a table-D
                        # entry without comment, and add the comment there
                        # in stead
                        extra_comment = line[18:]
                        if not (extra_comment.strip() == ""):
                            if self.verbose:
                                print "WARNING: ignoring extra comment on "+\
                                      "continuation line: "
                                print "line: ["+line+"]"
                        
                #print descriptor_list, reference, \
                #      ref_reference, postpone, report_unhandled
                postpone = self.add_ref_to_descr_list(descriptor_list,
                                                      reference,
                                                      ref_reference, i,
                                                      postpone,
                                                      report_unhandled)
            if (not postpone):
                # all continuation lines have been processed so store
                # the result.
                # first a safety check
                if len(descriptor_list) == count:
                    #print "************************storing result"
                    d_descr = CompositeDescriptor(reference, descriptor_list,
                                                  comment, self)
                    if not self.table_d.has_key(reference):
                        #print "adding descr. key ", reference
                        self.table_d[reference] = d_descr
                    else:
                        print "ERROR: multiple table D descriptors "+\
                              "with identical reference"
                        print "number found. This should never happen !!!"
                        print "problematic descriptor is: ", d_descr
                        print "Please report this problem, together with"
                        print "a copy of the bufr table you tried to read."
                        print "Ignoring this entry for now....."
                else:
                    print "ERROR: unexpected format in table D file..."
                    print "problematic descriptor is: ", reference
                    print "linecount: ", i
                    print "line: ["+line+"]"
                    print "This D-table entry defines more descriptors than"
                    print "specified in the start line."
                    print "Please report this problem, together with"
                    print "a copy of the bufr table you tried to read."
                    print "len(descriptor_list) = ", len(descriptor_list)
                    print "count = ", count
                    if len(descriptor_list)<count:
                        raise IOError
                    else:
                        if self.verbose:
                            print "ignoring excess descriptors for now..."
                        #print "************************storing result"
                        d_descr = CompositeDescriptor(reference,
                                                      descriptor_list,
                                                      comment, self)
                        if not self.table_d.has_key(reference):
                            #print "adding descr. key ", reference
                            self.table_d[reference] = d_descr
                        else:
                            print "ERROR: multiple table D descriptors with "+\
                                  "identical reference"
                            print "number found. This should never happen !!!"
                            print "problematic descriptor is: ", d_descr
                            print "Please report this problem, together with"
                            print "a copy of the bufr table you tried to read."
                            print "Ignoring this entry for now....."
                        
                # mark this block as done
                list_of_handled_blocks.append(d_entry_block)
                # count successfully handled blocks
                handled_blocks += 1

        # remove the processed blocks
        for d_entry_block in list_of_handled_blocks:
            self.list_of_d_entry_lineblocks.remove(d_entry_block)

        remaining_blocks = len(self.list_of_d_entry_lineblocks)
                
        return (handled_blocks, remaining_blocks)
        #  #]
    def load_d_table(self, dfile):
        #  #[
        """
        load BUFR table D from file
        """
        print "loading D table from file: ", dfile

        # known problem:
        # the code stops with an error if a D-table entry is used before
        # it is defined, even if it is defined lateron in the same D-table
        # in the current example file, this happens for entry 301028
        # which is used on line 67, but only defined on line 69

        if self.verbose:
            print "********************"
            print "**** first pass ****"
            print "********************"

        #  #[ create a list of blocks of lines
        self.list_of_d_entry_lineblocks = []
        this_lineblock = None
        for (i, line) in enumerate(open(dfile, 'rt')):
            line_copy = line.replace('\r', '').replace('\n', '')
            #print "considering line ["+l+"]"
            parts = line_copy[:18].split()
            start_line = False
            continuation_line = False
            if (len(parts) == 3):
                start_line = True
            elif (len(parts) == 1):
                continuation_line = True
            else:
                print "ERROR: unexpected format in table D file..."
                print "linecount: ", i
                print "line: ["+line_copy+"]"
                print "first 17 characters should hold either 1 or 3 integer"
                print "numbers, but in stead it holds: ", len(parts), " parts"
                print "You could report this to the creator of this table "+\
                      "since this should never happen."
                raise IOError
            
            if start_line:
                #print "is a start line"
                if (this_lineblock != None):
                    # save the just read block in the list
                    self.list_of_d_entry_lineblocks.append(this_lineblock)
                # and start with a new lineblock
                this_lineblock = []
                this_lineblock.append((i, line_copy))
                
            if continuation_line:
                #print "is a continuation line"
                this_lineblock.append((i, line_copy))

        # save the last block as well
        if (this_lineblock != None):
            # save the final block in the list
            self.list_of_d_entry_lineblocks.append(this_lineblock)

        self.num_d_blocks = len(self.list_of_d_entry_lineblocks)
        #  #]

        if self.verbose:
            print "*********************"
            print "**** second pass ****"
            print "*********************"

        handled_blocks = 1
        loop_count = 0
        while (handled_blocks>0):
            loop_count += 1
            if self.verbose:
                print "==============>loop count: ", loop_count
            (handled_blocks, remaining_blocks) = self.decode_blocks()

        if self.verbose:
            print "remaining blocks: ", remaining_blocks
            print "decoded blocks:   ", handled_blocks
            if remaining_blocks > 0:
                print "---------------------------------------------------"
                print "Reporting problematic blocks:"
                print "---------------------------------------------------"
                # nothing more to decode here, but run it once more with
                # the report_unhandled flag set, to generate a listing
                # of not properly used/defined entries
                (handled_blocks, remaining_blocks) = \
                                 self.decode_blocks(report_unhandled = True)
                print "---------------------------------------------------"

        print '-------------'
        print 'Loaded: ', self.num_d_blocks,' table D entries'
        print '-------------'
        
        if self.verbose:
            print "remaining_blocks = ", remaining_blocks

        if (self.num_d_blocks == remaining_blocks):
            print "ERROR: it seems you forgot to load the B-table before trying"
            print "to load the D-table. It is required to load "+\
                  "the corresponding B-table"
            print "first, because it is needed to apply consistency "+\
                  "checking on the"
            print "D-table during the read process."
            raise ProgrammingError

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
                    print "Problem in apply_modification_commands."
                    print "Modifier not recognised as start or end command."
                    print "This should never happen !"
                    raise ProgrammingError
            elif isinstance(descr, SpecialCommand):
                print "Problem in apply_modification_commands."
                print "The current descriptor list still seems to contain"
                print "replication commands, so it is not yet expanded!!!"
                print "The input to apply_modification_commands() should be"
                print "an expanded descriptor list..."
                raise ProgrammingError
            else:
                if len(current_modifications)>0:
                    mod_descr = ModifiedDescriptor(descr)
                    print "current_modifications:"
                    print ";".join(str(cur_mod) for cur_mod
                                   in current_modifications)
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
        unload the descriptors for the current BUFR table to
        allow loading a new table
        """
        # ok, this works but is not very pretty,
        # todo: see if this can be added as a function to the Singleton
        # or Descriptor class

        # dicts
        for b_reference in self.table_b.keys():
            del(self.table_b[b_reference].__class__.\
                __dict__.get("__instance_dict__")[b_reference])
            del(self.table_b[b_reference])
        for d_reference in self.table_d.keys():
            del(self.table_d[d_reference].__class__.\
                __dict__.get("__instance_dict__")[d_reference])
            del(self.table_d[d_reference])
        for s_reference in self.specials.keys():
            del(self.specials[s_reference].__class__.\
                __dict__.get("__instance_dict__")[s_reference])
            del(self.specials[s_reference])
        for m_reference in self.modifiers.keys():
            del(self.modifiers[m_reference].__class__.\
                __dict__.get("__instance_dict__")[m_reference])
            del(self.modifiers[m_reference])
        del(self.list_of_d_entry_lineblocks)
        self.list_of_d_entry_lineblocks = []

        print 'self.table_b = ', self.table_b
        print 'self.table_d = ', self.table_d
        print 'self.specials = ', self.specials
        print 'self.modifiers = ', self.modifiers
        print 'self.list_of_d_entry_lineblocks = ', \
              self.list_of_d_entry_lineblocks

        #sys.exit(1)
        #  #]
    #  possible additional methods:
    #  ==>write-tables
    #  #]
    
if __name__ == "__main__":
    #  #[ test program
    print "Starting test program:"
    BT = BufrTable(autolink_tablesdir = "tmp_BUFR_TABLES")
    # load BUFR tables using the automatically linked
    # tables defined on the lines above
    
    # test the available bufr tables
    TABLE_CODES = ["0000000000098000000",
                   "0000000000098002001", "0000000000098006000",
                   "0000000000098006001", "0000000000098013001",
                   "0000000000098014001"]
    #, "0000000000000014000",
    #, "0000000000254011001"
    # this last one seems only to have a B table but no D table!!!!
    
    PATH = "ecmwf_bufrtables"
    for table_code in TABLE_CODES:
        BT.load(os.path.join(PATH, "B"+table_code+".TXT"))
        BT.load(os.path.join(PATH, "D"+table_code+".TXT"))

        BT.unload_tables()
    
    # test application of modification commands:
    # this is D-descriptor 331004
    
    # load the ADM-Aeolus L2B-product BUFR table
    PATH = "alt_bufr_tables"
    TABLE_CODE = "0000000000098015001"
    BT.load(os.path.join(PATH, "B"+TABLE_CODE+".TXT"))
    BT.load(os.path.join(PATH, "D"+TABLE_CODE+".TXT"))
    
    CODES = ["207001", # = modifier
             "005001", # = LATITUDE (HIGH ACCURACY)  [DEGREE]
             "006001", # = LONGITUDE (HIGH ACCURACY) [DEGREE]
             "207000"] # = end of modifier   
    DESCR_LIST = []
    for c in CODES:
        DESCR_LIST.append(BT.get_descr_object(int(c, 10)))
    print "DESCR_LIST = ", DESCR_LIST
    
    MOD_DESCR_LIST = BT.apply_modification_commands(DESCR_LIST)
    
    #  #]
    
