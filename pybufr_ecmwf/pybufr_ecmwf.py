#!/usr/bin/env python

#  #[ documentation
#
# This module implements a python interface around the BUFR library provided by
# ECMWF to allow reading and writing the WMO BUFR file standard.
#
# For more on information ECMWF see: http://www.ecmwf.int/
# For more information on the BUFR library software provided
# by ECMWF see: http://www.ecmwf.int/products/data/software/download/bufr.html
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
import os          # operating system functions
import sys         # system functions
import time        # handling of date and time
import numpy as np # import numerical capabilities
import struct      # allow converting c datatypes and structs
# import some home made helper routines
from helpers import call_cmd_and_verify_output
from helpers import EcmwfBufrLibError
from helpers import EcmwfBufrTableError

# import the raw wrapper interface to the ECMWF BUFR library
import ecmwfbufr

#  #]

class BufrTemplate:
    #  #[
    """
    a class of to help create a BUFR template in a more structured way
    """
    
    #  #[ class constants
    
    # define the delayed replication code
    Delayed_Descr_Repl_Factor = int('031001',10)

    #  #]
    def __init__(self,max_nr_descriptors):
        #  #[
        self.max_nr_descriptors = max_nr_descriptors
        self.unexpanded_descriptor_list = []
        self.nr_of_delayed_repl_factors = 0
        self.del_repl_max_nr_of_repeats_list = []
        #  #]
    def add_descriptor(self,descriptor):
        #  #[
        self.unexpanded_descriptor_list.append(descriptor)
        #  #]
    def add_descriptors(self,*descriptors):
        #  #[
        nr_of_descriptors = len(descriptors)
        print 'adding ',nr_of_descriptors,' descriptors'
        self.unexpanded_descriptor_list.extend(descriptors)
        #  #]
    def add_delayed_replicated_descriptors(self,max_nr_of_repeats,*descriptors):
        #  #[
        nr_of_descriptors = len(descriptors)
        print 'adding delayed replication for ',nr_of_descriptors,' descriptors'
        print 'replicating them at most ',max_nr_of_repeats,' times'
        repl_code = self.get_replication_code(nr_of_descriptors,0)
        self.unexpanded_descriptor_list.append(repl_code)
        self.unexpanded_descriptor_list.append(self.Delayed_Descr_Repl_Factor)
        self.unexpanded_descriptor_list.extend(descriptors)
        self.nr_of_delayed_repl_factors = self.nr_of_delayed_repl_factors + 1
        self.del_repl_max_nr_of_repeats_list.append(max_nr_of_repeats)
        #  #]
    def add_replicated_descriptors(self,nr_of_repeats,*descriptors):
        #  #[
        nr_of_descriptors = len(descriptors)
        print 'adding replication for ',nr_of_descriptors,' descriptors'
        print 'replicating them ',nr_of_repeats,' times'
        repl_code = self.get_replication_code(nr_of_descriptors,
                                              nr_of_repeats)
        self.unexpanded_descriptor_list.append(repl_code)
        self.unexpanded_descriptor_list.extend(descriptors)
        #  #]
    def get_replication_code(self,num_descriptors,num_repeats):
        #  #[
	repl_factor = 100000 + num_descriptors*1000 + num_repeats
	# for example replicating 2 descriptors 25 times will
        # be encoded as: 102025
	# for delayed replication, set num_repeats to 0
	# then add the Delayed_Descr_Repl_Factor after this code
	return repl_factor
        #  #]
    #  #]

class BUFRInterfaceECMWF:
    #  #[
    """
    a class of wrapper and helper functions to allow easier use of the
    raw ECMWF BUFR interface wrapper
    """
    #  #[ local constant parameters
    size_ksup  =    9
    size_ksec0 =    3
    size_ksec1 =   40
    size_ksec2 = 4096
    size_key   =   52
    size_ksec3 =    4
    size_ksec4 =    2
    #  #]
    def __init__(self,encoded_message=None,
                 max_nr_descriptors=20,
                 max_nr_expanded_descriptors=140):
        #  #[
        # binary encoded BUFR message data
        # (usually stored as a 4-byte integer array)
        self.encoded_message = encoded_message

        # switches
        self.sections012_decoded      = False
        self.sections0123_decoded     = False
        self.data_decoded             = False
        self.descriptors_list_filled  = False
        self.bufr_template_registered = False # for encoding only
        self.data_encoded             = False # for encoding only
        
        # todo: pass these values as optional parameters to the decoder
        #       and check whether they pass the library maximum or not.
        #       (and choose sensible defaults if not provided)

        # define the needed sizes
        # (especially the last 2 define the size of the values and cvals
        #  array and can cause serious memory usage, so maybe later I'll
        #  add an option to choose the values at runtime)
        self.max_nr_descriptors          = max_nr_descriptors
        self.max_nr_expanded_descriptors = max_nr_expanded_descriptors
        #
        # note: these maximum constants are only used by the decoder,
        # and will be redefined during encoding
        #
        # note: maximum possible value for max_nr_expanded_descriptors
        # is JELEM=320.000 (as defined in ecmwfbufr_parameters.py), but
        # using that maximum value is not a very nice idea since it will
        # cause 24MB per subset of memory to be allocated for the cvals
        # array, so for a typical ERS2 BUFR message with 361 subsets
        # this would be 320000.*80*361/1024/1024/1024 = 8.6 GB ....)
        # Even if this is just virtual memory, it may not allways be
        # nice to your system to do this...
        self.nr_subsets = 361 # 25
        # self.max_nr_delayed_replication_factors = ///

        # copy to names that are more common in the ECMWF software
        self.ktdlen = self.max_nr_descriptors
        # self.krdlen = self.max_nr_delayed_replication_factors
        self.kelem  = self.max_nr_expanded_descriptors

        # filling this one is delayed in case of decoding
        # since the nr of subsets is only known after decoding
        # sections 0 upto 3. 
        #self.kvals  = self.max_nr_expanded_descriptors*self.max_nr_subsets
        # self.jbufl  = self.max_bufr_msg_size
        # self.jsup   = size_ksup
    
        # arrays to hold the meta data
        self.ksup   = np.zeros(self.size_ksup,  dtype = np.int)
        self.ksec0  = np.zeros(self.size_ksec0, dtype = np.int)
        self.ksec1  = np.zeros(self.size_ksec1, dtype = np.int)
        self.ksec2  = np.zeros(self.size_ksec2, dtype = np.int)
        self.key    = np.zeros(self.size_key,   dtype = np.int)
        self.ksec3  = np.zeros(self.size_ksec3, dtype = np.int)
        self.ksec4  = np.zeros(self.size_ksec4, dtype = np.int)

        # arrays to hold the descriptors
        self.ktdlen = 0 # will hold nr of descriptors
        self.ktdlst = np.zeros(self.max_nr_descriptors, dtype = np.int)
        self.ktdexl = 0 # will hold nr of expanded descriptors
        self.ktdexp = np.zeros(self.max_nr_expanded_descriptors, dtype = np.int)

        # the list of max nr of delayed replications is filled
        # inside the register_and_expand_descriptors method
        self.kdata = None
        
        # arrays to hold the actual numerical and string values
        self.cnames = np.zeros((self.kelem, 64), dtype = np.character)
        self.cunits = np.zeros((self.kelem, 24), dtype = np.character)

        # note: these next 2 arrays might become very large, especially
        # the cvals array, so in order to keep them as small as possible
        # I'll only define and allocate them after the number of subsets
        # has been retrieved (so just before entering the bufrex routine)
        self.values = None
        self.cvals  = None

        # define our own location for storing (symlinks to) the BUFR tables
        self.private_bufr_tables_dir = os.path.abspath("./tmp_BUFR_TABLES")
        if (not os.path.exists(self.private_bufr_tables_dir)):
            os.mkdir(self.private_bufr_tables_dir)

        # make sure the BUFR tables can be found
        # also, force a slash at the end, otherwise the library fails
        # to find the tables (at least this has been the case for many
        # library versions I worked with)
        env = os.environ
        env["BUFR_TABLES"] = self.private_bufr_tables_dir+os.path.sep
        # the above works just fine for me, no need for this one:
        #os.putenv("BUFR_TABLES",self.private_bufr_tables_dir+os.path.sep)

        #  #]        
    def get_expected_ecmwf_bufr_table_names(self,
                                            ecmwf_bufr_tables_dir,
                                            center, subcenter,
                                            LocalVersion, MasterTableVersion,
                                            EditionNumber, MasterTableNumber):
        #  #[
        # some local parameters used for detection of the
        # BUFR tables naming convention (short, medium or long)
        testfile_short  = "B0000980000.TXT"
        # this format was introduced with bufr_000260
        testfile_medium = "B000000000980000.TXT"
        # this format was introduced with bufr_000270
        testfile_long   = "B0000000000098000000.TXT"

        # somne codes to define the conventions
        conv_undefined = -1
        conv_short     =  1
        conv_medium    =  2
        conv_long      =  3

        #-------------------------------------------------------------
        # see which BUFR tables naming convention is used (short/long)
        #-------------------------------------------------------------
        bufrtable_naming_convention = conv_undefined

        testfile = os.path.join(ecmwf_bufr_tables_dir, testfile_short)
        if (os.path.exists(testfile)):
            #print "Using short BUFRtables naming convention ..."
            bufrtable_naming_convention = conv_short

        testfile = os.path.join(ecmwf_bufr_tables_dir, testfile_medium)
        if (os.path.exists(testfile)):
            #print "Using medium length BUFRtables naming convention ..."
            bufrtable_naming_convention = conv_medium

        testfile = os.path.join(ecmwf_bufr_tables_dir, testfile_long)
        if (os.path.exists(testfile)):
            #print "Using long BUFRtables naming convention ..."
            bufrtable_naming_convention = conv_long

        if (bufrtable_naming_convention == conv_undefined):
            print "Sorry, unable to detect which BufrTable naming convention"
            print "should be used. Assuming the short convention ....."
            bufrtable_naming_convention = conv_short

        copy_center            = center
        copy_subcenter         = subcenter
        copy_mastertablenumber = MasterTableNumber
    
        # exception: if version of local table is set to zero then
        # it is assumed in BUGBTS that a standard ECMWF table is used !
        if (LocalVersion == 0):
            copy_center    = 98 # ECMWF
            copy_subcenter = 0

        # initialise
        name_table_b = ''
        name_table_d = ''

        if   (bufrtable_naming_convention == conv_short):
            if (EditionNumber <= 2):
                table_format = "%2.2i%3.3i%2.2i%2.2i"
                copy_subcenter = 0
            else:
                # starting from edition 3 the originating center
                # has one digit more
                table_format = "%3.3i%3.3i%2.2i%2.2i"
            numeric_part = table_format % (copy_subcenter, copy_center,
                                           MasterTableVersion, LocalVersion)
            
        elif (bufrtable_naming_convention == conv_medium):
            table_format = "%3.3i%4.4i%4.4i%2.2i%2.2i"
            if (EditionNumber <= 2):
                copy_subcenter         = 0
                copy_mastertablenumber = 0
            numeric_part = table_format % (copy_mastertablenumber,
                                           copy_subcenter, copy_center,
                                           MasterTableVersion, LocalVersion)

        elif (bufrtable_naming_convention == conv_long):
            table_format = "%3.3i%5.5i%5.5i%3.3i%3.3i"
            if (EditionNumber <= 2):
                copy_subcenter         = 0
                copy_mastertablenumber = 0
            numeric_part = table_format % (copy_mastertablenumber,
                                           copy_subcenter, copy_center,
                                           MasterTableVersion, LocalVersion)

        name_table_b = 'B'+numeric_part+'.TXT'
        name_table_d = 'D'+numeric_part+'.TXT'

        # xx=KSEC1(3)  = kcenter
        # yy=KSEC1(15) = kMasterTableVersion
        # zz=KSEC1(08) = kLocalVersion
        # for bufr editions 1 and 2
        # ww=0
        # ss=0
        # for bufr editions 3 and 4
        # ww=KSEC1(16) = ksubcenter
        # ss=KSEC1(14) = kMasterTableNumber
        #
        # naming convention for BUFR tables:
        # [B/C/D]xxxxxyyzz
        # with   xxxxx = originating centre          (tbd%kcenter)
        #        yy    = version of mastertable used (tbd%kMasterTableVersion)
        #        zz    = version of local table used (tbd%kLocalVersion)
        #
        # for more details see also file: buetab.f
        # (which actually reads the BUFR tables)
        #
        # see also: bufrdc.f in SUBROUTINE BUGBTS()
        #
        #             BUFR EDITION 2 NAMING CONVENTION
        #
        #             BXXXXXYYZZ , CXXXXXYYZZ , DXXXXXYYZZ
        #
        #             B/C/D  - BUFR TABLE B/C/D
        #             XXXXX  - ORIGINATING CENTRE
        #             YY     - VERSION NUMBER OF MASTER TABLE
        #                      USED( CURRENTLY 2 )
        #             ZZ     - VERSION NUMBER OF LOCAL TABLE USED
        #
        #             BUFR EDITION 3 NAMING CONVENTION
        #
        #             BWWWXXXYYZZ , CWWWXXXYYZZ , DWWWXXXYYZZ
        #
        #             B/C/D  - BUFR TABLE B/C/D
        #             WWW    - ORIGINATING SUB-CENTRE
        #             XXX    - ORIGINATING CENTRE
        #             YY     - VERSION NUMBER OF MASTER TABLE
        #                      USED( CURRENTLY 2 )
        #             ZZ     - VERSION NUMBER OF LOCAL TABLE USED
        #
        #
        #             BUFR EDITION 4 NAMING CONVENTION
        #
        #             BSSSWWWWXXXXYYZZ , CSSSWWWWXXXXYYZZ , DSSSWWWWXXXXYYZZ
        #
        #             B      - BUFR TABLE 'B'
        #             C      - BUFR TABLE 'C'
        #             D      - BUFR TABLE 'D'
        #             SSS    - MASTER TABLE
        #             WWWW(W)   - ORIGINATING SUB-CENTRE
        #             XXXX(X)   - ORIGINATING CENTRE
        #             YY(Y)     - VERSION NUMBER OF MASTER
        #                         TABLE USED( CURRENTLY 12 )
        #             ZZ(Y)     - VERSION NUMBER OF LOCAL TABLE USED
        
        return (name_table_b, name_table_d)
        #  #]
    def decode_sections_012(self):
        #  #[ wrapper for bus012

        # running of this routine yields enough meta-data to enable
        # figuring out how to name the expected BUFR tables
        
        kerr = 0

        print "calling: ecmwfbufr.bus012():"
        ecmwfbufr.bus012(self.encoded_message, # input
                         self.ksup,  # output
                         self.ksec0, # output
                         self.ksec1, # output
                         self.ksec2, # output
                         kerr)       # output
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr,'bus012'))

        self.sections012_decoded = True
        #  #]
    def decode_sections_0123(self):
        #  #[ wrapper for bus0123

        # running of this routine yields the same as
        # decode_sections_012, and in addition it fills
        # ksec3, which contains:
        #
        # KSEC3( 1)-- LENGTH OF SECTION 3 (BYTES)
        # KSEC3( 2)-- RESERVED
        # KSEC3( 3)-- NUMBER OF SUBSETS
        # KSEC3( 4)-- FLAG (DATA TYPE,DATA COMPRESSION)
        #
        # At the moment it is not really clear to me why
        # it is usefull to have a routine to do this.

        kerr = 0
       
        print "calling: ecmwfbufr.bus012():"
        ecmwfbufr.bus0123(self.encoded_message, # input
                          self.ksup,  # output
                          self.ksec0, # output
                          self.ksec1, # output
                          self.ksec2, # output
                          self.ksec3, # output
                          kerr)       # output
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr,'bus0123'))

        self.sections012_decoded  = True
        self.sections0123_decoded = True
        #  #]
    def setup_tables(self,table_B_to_use=None,table_D_to_use=None):
        #  #[ routine for easier handling of tables
        if (not self.sections012_decoded):
            errtxt = "Sorry, setting up BUFR tables is only possible after "+\
                     "sections 0,1,2 of a BUFR message have been decoded "+\
                     "with a call to decode_sections_012"
            raise EcmwfBufrLibError(errtxt)

        # dont use this! This would need an import of helpers
        # which in turn imports pybufr_ecmwf so would give a circular
        # dependency ...
        #ecmwf_bufr_tables_dir = helpers.get_tables_dir()

        this_path,this_file = os.path.split(__file__)
        ecmwf_bufr_tables_dir = os.path.join(this_path,"ecmwf_bufrtables")
        if not os.path.exists(ecmwf_bufr_tables_dir):
            print "Error: could not find BUFR tables directory"
            raise IOError

        # make sure the path is absolute, otherwise the ECMWF library
        # might fail when it attempts to use it ...
        ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)

        # print 'ecmwf_bufr_tables_dir = ',ecmwf_bufr_tables_dir

        EditionNumber      = self.ksec0[3-1]

        center             = self.ksec1[3-1]
        LocalVersion       = self.ksec1[8-1]
        MasterTableNumber  = self.ksec1[14-1]
        MasterTableVersion = self.ksec1[15-1]
        subcenter          = self.ksec1[16-1]

        (expected_name_table_b, expected_name_table_d) = \
              self.get_expected_ecmwf_bufr_table_names(
                       ecmwf_bufr_tables_dir,
                       center, subcenter,
                       LocalVersion, MasterTableVersion,
                       EditionNumber, MasterTableNumber)
        
        # print '(expected_name_table_b, expected_name_table_d) = ',\
        #       (expected_name_table_b, expected_name_table_d)

        fullpath_table_b = os.path.join(ecmwf_bufr_tables_dir,
                                        expected_name_table_b)
        fullpath_table_d = os.path.join(ecmwf_bufr_tables_dir,
                                        expected_name_table_d)
        fullpath_default_table_b = os.path.join(ecmwf_bufr_tables_dir,
                                                'B_default.TXT')
        fullpath_default_table_d = os.path.join(ecmwf_bufr_tables_dir,
                                                'D_default.TXT')
        # print 'Test:'
        # print fullpath_table_b
        # print fullpath_table_d
        # print fullpath_default_table_b
        # print fullpath_default_table_d

        # OK, the trick now is to create a symbolic link in a tmp_BUFR_TABLES
        # directory from the name expected by the ecmwf bufr library to:
        #   1) the provided table names (if given) OR
        #   2) the expected table names (if present in the ECMWF sources) OR
        #   3) the default tables (and hope they will contain the needed
        #      descriptors to allow proper decoding or encoding)

        # note that self.private_bufr_tables_dir  is defined in __init__
        # now, since this one needs to be set before the bus012 call
        # (while this setup_tables method will be called after the bus012
        #  call because it needs some numbers from the sections 0,1,2)
        
        destination_b = os.path.join(self.private_bufr_tables_dir,
                                     expected_name_table_b)
        destination_d = os.path.join(self.private_bufr_tables_dir,
                                     expected_name_table_d)

        if ( (table_B_to_use is not None) and
             (table_D_to_use is not None)    ):
            # case 1)
            # create symbolic links from the provided tables to the
            # expected names in the private_bufr_tables_dir
            source_b = table_B_to_use
            source_d = table_D_to_use
        else:
            if (os.path.exists(fullpath_table_b) and
                os.path.exists(fullpath_table_d)    ):
                # case 2)
                # print 'table b and d found'
                # print fullpath_table_b
                # print fullpath_table_d
                source_b = fullpath_table_b
                source_d = fullpath_table_d
            elif (os.path.exists(fullpath_default_table_b) and
                  os.path.exists(fullpath_default_table_d)    ):
                # case 3)
                # print 'using default tables'
                # print fullpath_default_table_b
                # print fullpath_default_table_d
                source_b = fullpath_default_table_b
                source_d = fullpath_default_table_d
            else:
                errtxt = 'ERROR: no BUFR tables seem available.'+\
                         'please point explicitely to the tables '+\
                         'you wish to use'
                raise EcmwfBufrTableError(errtxt)
            
        # full names, containing full path, are not nice to print
        # in the unit tests since they will differ on different
        # machines, so print the bare filename only
        print 'Table names expected by the library:'
        print os.path.split(destination_b)[1]
        print os.path.split(destination_d)[1]
        
        print 'Tables to be used:'
        print os.path.split(source_b)[1]
        print os.path.split(source_d)[1]
        
        # make sure any old symbolic link is removed
        # (since it may point to an unwanted location)
        if ( os.path.islink(destination_b) or
             os.path.exists(destination_b)   ):
            os.remove(destination_b)
        if ( os.path.islink(destination_d) or
             os.path.exists(destination_d)   ):
            os.remove(destination_d)
        os.symlink(os.path.abspath(source_b), destination_b)
        os.symlink(os.path.abspath(source_d), destination_d)
            
        # make sure the BUFR tables can be found
        # also, force a slash at the end, otherwise the library fails
        # to find the tables (at least this has been the case for many
        # library versions I worked with)
        env = os.environ
        env["BUFR_TABLES"] = self.private_bufr_tables_dir+os.path.sep
    
        #  #]
    def print_sections_012(self):
        #  #[ wrapper for buprs0, buprs1, buprs2
        if (not self.sections012_decoded):
            errtxt = "Sorry, printing sections 0,1,2 of a BUFR message "+\
                     "is only possible after "+\
                     "sections 0,1,2 of a BUFR message have been decoded "+\
                     "with a call to decode_sections_012"
            raise EcmwfBufrLibError(errtxt)

        print '------------------------------'
        print "printing content of section 0:"
        ecmwfbufr.buprs0(self.ksec0)
        print '------------------------------'
        print "printing content of section 1:"
        ecmwfbufr.buprs1(self.ksec1)
        print '------------------------------'
        sec2_len = self.ksec2[0]        
        if (sec2_len > 0):
            # buukey expands local ECMWF information
            # from section 2 to the key array
            print '------------------------------'
            print "calling buukey"
            ecmwfbufr.buukey(self.ksec1,
                             self.ksec2,
                             self.key,
                             self.ksup,
                             kerr)
            print "printing content of section 2:"
            ecmwfbufr.buprs2(self.ksup,
                             self.key)
        else:
            print 'skipping section 2 [since it seems unused]'
        #  #]
    def decode_data(self):
        #  #[
        kerr   = 0

        if (not self.sections012_decoded):
            errtxt = "Sorry, in order to allow automatic allocation of the "+\
                     "values and cvals arrays the number of subsets is "+\
                     "needed. Therefore the decode_sections012 or "+\
                     "decode_sections_0123 subroutine needs to be called "+\
                     "before entering the decode_data subroutine."
            raise EcmwfBufrLibError(errtxt)

        # calculate the needed size of the values and cvals arrays
        actual_nr_of_subsets = self.get_num_subsets()
        self.kvals  = self.max_nr_expanded_descriptors*actual_nr_of_subsets

        # allocate space for decoding
        # note: float64 is the default, but it doesn't hurt to make it explicit
        self.values = np.zeros(      self.kvals, dtype = np.float64)
        self.cvals  = np.zeros((self.kvals, 80), dtype = np.character)

        ecmwfbufr.bufrex(self.encoded_message, # input
                         self.ksup,   # output
                         self.ksec0,  # output
                         self.ksec1,  # output
                         self.ksec2,  # output
                         self.ksec3,  # output
                         self.ksec4,  # output
                         self.cnames, # output
                         self.cunits, # output
                         self.values, # output
                         self.cvals,  # output
                         kerr)        # output
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr,'bufrex'))

        # note: something seems to fail in case self.kvals (also known
        # as kelem) is too small. bufrex should return with error 25,
        # but in my tests it seems to return with 0.
        # Note that this condition may occur if the user gives a wrong
        # value for max_nr_expanded_descriptors in __init__.
        # Therefore check to see if sec4 was decoded allright:
        if self.ksec4[0]==0:
            errtxt = "Sorry, call to bufrex failed, Maybe you have choosen "+\
                     "a too small value for max_nr_expanded_descriptors?"
            raise EcmwfBufrLibError(errtxt)
        
        self.data_decoded = True
        #  #]
    def print_sections_012_metadata(self):
        #  #[
        
        if (not self.sections012_decoded):
            errtxt = "Sorry, printing sections 0,1,2 of a BUFR message "+\
                     "is only possible after a BUFR message has been "+\
                     "partially decoded with a call to decode_sections_012"
            raise EcmwfBufrLibError(errtxt)
        
        print "ksup : ", self.ksup
        print "sec0 : ", self.ksec0
        print "sec1 : ", self.ksec1
        print "sec2 : ", self.ksec2
        #  #]
    def print_sections_0123_metadata(self):
        #  #[
        
        if (not self.sections0123_decoded):
            errtxt = "Sorry, printing sections 0,1,2,3 of a BUFR message "+\
                     "is only possible after a BUFR message has been "+\
                     "partially decoded with a call to decode_sections_0123"
            raise EcmwfBufrLibError(errtxt)
        
        print "ksup : ", self.ksup
        print "sec0 : ", self.ksec0
        print "sec1 : ", self.ksec1
        print "sec2 : ", self.ksec2
        print "sec3 : ", self.ksec3
        #  #]
    def print_sections_01234_metadata(self):
        #  #[
        if (not self.data_decoded):
            errtxt = "Sorry, printing sections 0,1,2,3,4 of a BUFR message "+\
                     "is only possible after a BUFR message has been decoded "+\
                     "with a call to decode_data"
            raise EcmwfBufrLibError(errtxt)
        
        print "ksup : ", self.ksup
        print "sec0 : ", self.ksec0
        print "sec1 : ", self.ksec1
        print "sec2 : ", self.ksec2
        print "sec3 : ", self.ksec3
        print "sec4 : ", self.ksec4
        #  #]
    def print_names_and_units(self):
        #  #[
        if (not self.data_decoded):
            errtxt = "Sorry, names and units are only available after "+\
                     "a BUFR message has been decoded with a call to "+\
                     "decode_data"
            raise EcmwfBufrLibError(errtxt)

        print "[index] cname [cunit] : "
        for (i, cnm) in enumerate(self.cnames):
            cun = self.cunits[i]
            txtn = ''.join(c for c in cnm)
            txtu = ''.join(c for c in cun)
            if (txtn.strip() != ''):
                print '[%3.3i]:%s [%s]' % (i, txtn, txtu)
        #  #]
    def explain_error(kerr, subroutine_name):
        #  #[ explain error codes returned by the bufrlib routines
        # to be implemented, for now just print the raw code

        # See file: bufrdc/buerr.F for a long list of possible
        # error conditions that the ECMWF library may return
        # (just wish it would really return them, since there seem
        # to be some bugs in the software on this point ...)

        return 'libbufr subroutine '+subroutine_name+\
               ' reported error code: kerr = '+str(kerr)
        #  #]
    def get_num_subsets(self):
        #  #[ return number of subsets in this BUFR message
        if (not self.sections012_decoded):
            errtxt = "Sorry, the number of subsets is only available after "+\
                     "a BUFR message has been decoded with a call to "+\
                     "decode_sections_012"
            raise EcmwfBufrLibError(errtxt)
        return self.ksup[5]
        # don't use this one, since that is only available after
        # decoding section3 ...
        #return self.ksec3[2]
        #  #]
    def get_num_elements(self):
        #  #[ return expanded number of descriptors in one subset
        if (not self.sections012_decoded):
            errtxt = "Sorry, the number of elements is only available after "+\
                     "a BUFR message has been decoded with a call to "+\
                     "decode_sections_012"
            raise EcmwfBufrLibError(errtxt)
        return self.ksup[4]
        #  #]
    def get_values(self,i):
        #  #[ get the i th number from each subset as an array
        if (not self.data_decoded):
            errtxt = "Sorry, retrieving values is only possible after "+\
                     "a BUFR message has been decoded with a call to "+\
                     "decode_data"
            raise EcmwfBufrLibError(errtxt)

        nsubsets  = self.get_num_subsets()
        nelements = self.get_num_elements()
        if i>nelements-1:
            errtxt = "Sorry, this BUFR message has only "+str(nelements)+\
                     " elements per subset, so requesting index "+\
                     str(i)+" is not possible (remember the arrays are "+\
                     "counted starting with 0)"
            raise EcmwfBufrLibError(errtxt)
        
        selection = self.max_nr_expanded_descriptors*\
                    np.array(range(nsubsets))+i

        values = self.values[selection]
        return values
        #  #]
    def get_element_name_and_unit(self,i):
        #  #[
        if (not self.data_decoded):
            errtxt = "Sorry, names and units are only available after "+\
                     "a BUFR message has been decoded with a call to "+\
                     "decode_data"
            raise EcmwfBufrLibError(errtxt)

        nelements = self.get_num_elements()
        if i>nelements-1:
            errtxt = "Sorry, this BUFR message has only "+str(nelements)+\
                     " elements per subset, so requesting name and unit for "+\
                     "index "+str(i)+" is not possible "+\
                     "(remember the arrays are counted starting with 0)"
            raise EcmwfBufrLibError(errtxt)

        txtn = ''.join(c for c in self.cnames[i])
        txtu = ''.join(c for c in self.cunits[i])

        return (txtn.strip(),txtu.strip())
        #  #]
    def fill_descriptor_list(self):
        #  #[ fills both the normal and expanded discriptor lists

        if ( (not self.data_decoded) and
             (not self.sections012_decoded)):
            errtxt = "Sorry, filling descriptor lists of a BUFR message "+\
                     "is only possible after a BUFR message has been decoded "+\
                     "with a call to decode_data or decode_sections_012"
            raise EcmwfBufrLibError(errtxt)

        # busel: fill the descriptor list arrays (only needed for printing)   
    
        # warning: this routine has no inputs, and acts on data stored
        #          during previous library calls
        # Therefore it only produces correct results when either bus012
        # or bufrex have been called previously on the same bufr message.....
    
        kerr   = 0
    
        print "calling: ecmwfbufr.busel():"
        ecmwfbufr.busel(self.ktdlen, # actual number of data descriptors
                        self.ktdlst, # list of data descriptors
                        self.ktdexl, # actual nr of expanded data descriptors
                        self.ktdexp, # list of expanded data descriptors
                        kerr)   # error  message
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr,'bufrex'))

        # It is not clear to me why busel seems to correctly produce
        # the descriptor lists (both bare and expanded), but yet it does
        # not seem to fill the ktdlen and ktdexl values.
        # To fix this the next 4 lines have been added:
        
        selection1 = np.where(self.ktdlst > 0)
        self.ktdlen = len(selection1[0])
        selection2 = np.where(self.ktdexp > 0)
        self.ktdexl = len(selection2[0])

        self.descriptors_list_filled = True
        #  #]
    def get_descriptor_list(self):
        #  #[
        if (not self.descriptors_list_filled):
            errtxt = "Sorry, retrieving the list of descriptors of a "+\
                     "BUFR message is only possible after a BUFR message "+\
                     "has been decoded with a call to decode_data or "+\
                     "decode_sections_012, and subsequently the lists have "+\
                     "been filled with a call to fill_descriptor_list"
            raise EcmwfBufrLibError(errtxt)

        return self.ktdlst[:self.ktdlen]
        #  #]
    def get_expanded_descriptor_list(self):
        #  #[
        if (not self.descriptors_list_filled):
            errtxt = "Sorry, retrieving the list of descriptors of a "+\
                     "BUFR message is only possible after a BUFR message "+\
                     "has been decoded with a call to decode_data or "+\
                     "decode_sections_012, and subsequently the lists have "+\
                     "been filled with a call to fill_descriptor_list"
            raise EcmwfBufrLibError(errtxt)

        return self.ktdexp[:self.ktdexl]
        #  #]
    def print_descriptors(self):
        #  #[
        if (not self.descriptors_list_filled):
            errtxt = "Sorry, retrieving the list of descriptors of a "+\
                     "BUFR message is only possible after a BUFR message "+\
                     "has been decoded with a call to decode_data or "+\
                     "decode_sections_012, and subsequently the lists have "+\
                     "been filled with a call to fill_descriptor_list"
            raise EcmwfBufrLibError(errtxt)

        # Note: this next call will print self.max_nr_descriptors
        # descriptors and self.max_nr_expanded_descriptors
        # extended descriptors, one line for each, including
        # explanation.
        # They will also print zeros for all not used elements of
        # these ktdlst and ktdexp arrays
        ecmwfbufr.buprs3(self.ksec3,
                         self.ktdlst,
                         self.ktdexp,
                         self.cnames)
        #  #]        
    def fill_sections_0123(self,
                           bufr_code_centre,
                           bufr_obstype,
                           bufr_subtype,
                           bufr_table_local_version,
                           bufr_table_master,
                           bufr_table_master_version,
                           bufr_code_subcentre,
                           num_subsets,
                           bufr_compression_flag,
                           datetime=None,
                           bufr_edition=4):
        #  #[
        # fill section 0
        self.ksec0[1-1] = 0 # length of sec0 in bytes
        #                     [filled by the encoder]
        self.ksec0[2-1] = 0 # total length of BUFR message in bytes
        #                     [filled by the encoder]
        self.ksec0[3-1] = bufr_edition

        # fill section 1
        self.ksec1[ 1-1]=  22               # length sec1 bytes
        #                                     [filled by the encoder]
        # (note: this may depend on the bufr_edition nr.)
        
        # however,a minimum of 22 is obliged here
        self.ksec1[ 2-1]= bufr_edition      # bufr edition
        self.ksec1[ 3-1]= bufr_code_centre  # originating centre
        self.ksec1[ 4-1]=   1               # update sequence number
        # usually 1, only updated if the same data is re-issued after
        # reprocessing or so to fix some bug/problem
        self.ksec1[ 5-1]=   0               # (Flags presence of section 2)
        #                                     (0/128 = no/yes)
        self.ksec1[ 6-1]= bufr_obstype              # message type
        self.ksec1[ 7-1]= bufr_subtype              # subtype
        self.ksec1[ 8-1]= bufr_table_local_version  # version of local table
        # (this determines the name of the BUFR table to be used)

        # fill the datetime group. Note that it is not yet clear to me
        # whether this should refer to the encoding datetime or to the
        # actual measurement datetime. So allow the user to set the value,
        # but use the current localtime if not provided.
        if datetime is not None:
            (year,month,day,hour,minute,second,
             weekday,julianday,isdaylightsavingstime) = datetime
        else:
            (year,month,day,hour,minute,second,
             weekday,julianday,isdaylightsavingstime) = time.localtime()
            
        self.ksec1[ 9-1]= (year-2000) # Without offset year - 2000
        self.ksec1[10-1]= month       # month
        self.ksec1[11-1]= day         # day
        self.ksec1[12-1]= hour        # hour
        self.ksec1[13-1]= minute      # minute

        self.ksec1[14-1]= bufr_table_master         # master table
        # (this determines the name of the BUFR table to be used)
        self.ksec1[15-1]= bufr_table_master_version # version of master table
        # (this determines the name of the BUFR table to be used)

        # NOTE on filling items 16,17,18: this is the way to do it in edition 3
        # TODO: adapt this procedure to edition 4, which requires
        # filling 2 more datetime groups en the actual latitude
        # and longitude ranges
        # See bufrdc/buens1.F for some details.

        # ksec1 items 16 and above are to indicate local centre information
        self.ksec1[16-1]= bufr_code_subcentre       # originating subcentre
        # (this determines the name of the BUFR table to be used)
        self.ksec1[17-1]=   0
        self.ksec1[18-1]=   0

        # a test for filling ksec2 is not yet defined
    
        # fill section 3
        self.ksec3[1-1]= 0
        self.ksec3[2-1]= 0
        self.ksec3[3-1]= num_subsets                # no of data subsets
        self.ksec3[4-1]= bufr_compression_flag      # compression flag

        # note: filling the ksup array is not really needed for
        # encoding (it is no input to bufren) but since I use ksup[5]
        # to retrieve the nr of subsets in get_num_subsets(),
        # make sure at least that element is filled properly
        self.ksup[5] = num_subsets
     
        self.nr_subsets = num_subsets
        # decoding is ofcourse not needed when you fill all the ksec
        # metadata yourself, but flag them as decoded anyway to allow
        # other routines (like setup_tables) to work correctly.
        self.sections012_decoded = True
        self.sections0123_decoded = True
        #  #]
    def register_and_expand_descriptors(self,BT):
        #  #[

        kerr   = 0

        # input: BT must be an instance of the BufrTemplate class
        # so check this:
        assert(isinstance(BT,BufrTemplate))
        
        # length of unexpanded descriptor list
        self.ktdlen = len(BT.unexpanded_descriptor_list)
        # convert the unexpanded descriptor list to a numpy array
        self.ktdlst = np.array(BT.unexpanded_descriptor_list,dtype=np.int)
        print "unexpanded nr of descriptors = ",self.ktdlen
        print "The current list is: ",self.ktdlst
        
        # call BUXDES
        # buxdes: expand the descriptor list
        #         and fill the array ktdexp and the variable ktdexp
        #         [only needed when creating a bufr msg with table D entries
        #          but I'll run ot anyway for now since this usually is
        #          a cheap operation, so a user should not be bothered by it]
        
        # iprint=0 # default is to be silent
        iprint=1
        if (iprint == 1):
            print "------------------------"
            print " printing BUFR template "
            print "------------------------"

        # define and fill the list of replication factors
        self.kdata = np.zeros(self.nr_subsets*
                              BT.nr_of_delayed_repl_factors,dtype=np.int)
        i = 0
        for subset in range(self.nr_subsets):
            # Warning: just set the whole array to the maximum you wish to have.
            # Letting this number vary seems not to work with the current
            # ECMWF library. It will allways just look at the first element
            # in the kdata array. (or do I misunderstand the BUFR format here?)
            for max_repeats in BT.del_repl_max_nr_of_repeats_list:
                self.kdata[i] = max_repeats
                i += 1
                
        print "delayed replication factors: ",self.kdata

        ecmwfbufr.buxdes(iprint,
                         self.ksec1,
                         self.ktdlst,
                         self.kdata,
                         self.ktdexl,
                         self.ktdexp,
                         self.cnames,
                         self.cunits,
                         kerr)
        print "ktdlst = ",self.ktdlst
        selection = np.where(self.ktdexp>0)
        print "ktdexp = ",self.ktdexp[selection]
        # print "ktdexl = ",self.ktdexl # this one seems not to be filled ...?
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr,'buxdes'))

        # It is not clear to me why buxdes seems to correctly produce
        # the expanded descriptor list, but yet it does
        # not seem to fill the ktdexl value.
        # To fix this the next 2 lines have been added:
        selection2 = np.where(self.ktdexp > 0)
        self.ktdexl = len(selection2[0])

        # these are filled as well after the call to buxdes
        # print "cnames = ",self.cnames
        # print "cunits = ",self.cunits

        self.bufr_template_registered = True

        #  #]        
    def encode_data(self,values,cvals):
        #  #[ call bufren to encode a bufr message
        kerr   = 0

        if (not self.sections012_decoded):
            errtxt = "Sorry, in order to allow automatic allocation of the "+\
                     "values and cvals arrays the number of subsets is "+\
                     "needed. Therefore the fill_sections0123 "+\
                     "subroutine needs to be called "+\
                     "before entering the encode_data subroutine."
            raise EcmwfBufrLibError(errtxt)

        # calculate the needed size of the values and cvals arrays
        actual_nr_of_subsets = self.get_num_subsets()
        self.kvals = self.max_nr_expanded_descriptors*actual_nr_of_subsets

        # allocate space for decoding
        # note: float64 is the default, but it doesn't hurt to make it explicit
        #self.values = np.zeros(      self.kvals, dtype = np.float64)
        self.cvals  = np.zeros((self.kvals, 80), dtype = np.character)

        # define the output buffer
        num_bytes = 5000
        num_words = num_bytes/4
        words = np.zeros(num_words,dtype=np.int)

        # call BUFREN
        ecmwfbufr.bufren(self.ksec0, # input
                         self.ksec1, # input
                         self.ksec2, # input
                         self.ksec3, # input
                         self.ksec4, # input
                         self.ktdlst, # input: expanded descriptor list
                         self.kdata,  # input :list of max nr of del. replic.
                         self.ktdexl, # input: exp_descr_list_length,
                         values, # input: values to encode
                         cvals,  # input: strings to encode
                         words, # output: the encoded message
                         kerr)  # output: an error flag
        print "bufren call finished"
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr,'bufren'))

        print "words="
        print words
        nw = len(np.where(words>0)[0])
        print "encoded size: ",nw," words or ",nw*4," bytes"

        self.data_encoded = True
        #  #]
        
#  #]

class RawBUFRFile:
    #  #[
    """
    a class to read and write the binary BUFR messages from and
    to file. Is is ntended to replace the pbio routines from the ECMWF
    library which for some obscure reason cannot be interfaced
    easily to python using the f2py tool.
    """
    def __init__(self, verbose = False):
        #  #[
        self.bufr_fd  = None
        self.filename = None
        self.filemode = None
        self.filesize = None
        self.data     = None
        self.list_of_bufr_pointers = []
        self.nr_of_bufr_messages = 0
        self.last_used_msg = 0
        self.verbose = verbose
        #  #]
    def print_properties(self, prefix = "BUFRFile"):
        #  #[
        # this one causes trouble with the unittesting since it gives
        # different addresses each time, and is not so very interesting
        # to print, so leave it out for now
        #print prefix+": bufr_fd  = ", self.bufr_fd
        print prefix+": filename = ", self.filename
        print prefix+": filemode = ", self.filemode
        print prefix+": filesize = ", self.filesize
        if (self.data != None):
            print prefix+": len(data) = ", len(self.data)
        else:
            print prefix+": data = ", self.data
        print prefix+": list_of_bufr_pointers = ", \
              self.list_of_bufr_pointers
        print prefix+": nr_of_bufr_messages = ", self.nr_of_bufr_messages
        #print prefix+":  = ", self.
        #  #]
    def open(self, filename, mode, silent = False):
        #  #[
        # note: the silent switch is only intended to suppress
        # warning and error messages during unit testing.
        # During normal use it should never be set to True.
        
        self.filename = filename
        self.filemode = mode
        
        # filename should include the path specification as well
        assert(mode in ['r', 'w', 'a'])

        if (mode == 'r'):
            if (os.path.exists(filename)):
                self.filesize = os.path.getsize(filename)
            else:
                if (not silent):
                    print "ERROR in BUFRFile.open():"
                    print "Opening file: ", self.filename, " with mode: ", \
                          self.filemode, " failed"
                    print "This file was not found or is not accessible."
                raise IOError
        elif (mode == 'w'):
            self.filesize = 0
        elif (mode == 'a'):
            # when appending it is allowed to have a non-existing
            # file, in which case one will be generated, so test for
            # this condition
            if (os.path.exists(filename)):
                # in this case, try to find out the amount of BUFR messages
                # already present in this file, by temporary opening
                # it in reading mode
                tmp_BF = RawBUFRFile()
                tmp_BF.open(filename, 'r')
                #tmp_BF.print_properties(prefix = "tmp_BF (opened for reading)")
                count = tmp_BF.get_num_bufr_msgs()
                tmp_BF.close()
                del(tmp_BF)

                # then store the found number for later use
                self.nr_of_bufr_messages = count
                self.filesize = os.path.getsize(filename)

                if (count == 0):
                    if (self.filesize>0):
                        print "WARNING: appending to non-zero file, but could"
                        print "not find any BUFR messages in it. Maybe you are"
                        print "appending to a non-BUFR file??"
            else:
                self.filesize = 0            

        try:
            self.bufr_fd = open(filename, mode)
        except:
            if (not silent):
                print "ERROR in BUFRFile.open():"
                print "Opening file: ", self.filename, " with mode: ", \
                      self.filemode, " failed"
            raise IOError

        if (mode == 'r'):
            try:
                self.data = self.bufr_fd.read()
            except:
                if (not silent):
                    print "ERROR in BUFRFile.open():"
                    print "Reading data from file: ", self.filename, \
                          " with mode: ", self.filemode, " failed"
                raise IOError

            # split in separate BUFR messages
            self.split()

        #  #]
    def close(self):
        #  #[
        # close the file
        self.bufr_fd.close()
        # then erase all settings
        self.__init__()
        #  #]
    def split(self):
        #  #[
        # Purpose: scans the file for the string "BUFR"
        # which indicate the start of a new BUFR message,
        # counts the nr of BUFR messages, and stores file
        # pointers to the start of each BUFR message.

        # safety catch
        if (self.filesize == 0):
            self.nr_of_bufr_messages = 0
            return

        # note: this very simpple search algorithm might accidently
        # find the string "7777" in the middle of the data of a BUFR message.
        # To check on this, make sure the distance between the end of a
        # message and the start of a message if either 0 or 2 bytes
        # (this may happen if the file is padded with zeros to contain
        #  a multiple of 4 bytes)
        # Do the same check on the end of the file.

        inside_message   = False
        file_end_reached = False
        search_pos = 0
        start_pos  = -1
        end_pos    = -1
        txt_start  = "BUFR"
        txt_end    = "7777"
        while not file_end_reached:

            if (not inside_message):
                # try to find a txt_start string
                start_pos = self.data.find(txt_start, search_pos)
                if (self.verbose):
                    print "search_pos = ", search_pos, \
                          " start_pos = ", start_pos, \
                          " txt = ", txt_start

                if (start_pos != -1):
                    inside_message = True

                    # sanity check, see if distance to the previous BUFR
                    # message is no more than 4 bytes
                    if (end_pos != -1):
                        distance = (start_pos-end_pos)
                        if (self.verbose):
                            print "distance = ", distance, " bytes"
                        if (distance > 3):
                            # this means we have found a false "7777"
                            # end marker, so ignore the last added msg
                            # and start looking again
                            (prev_start_pos, prev_end_pos) = \
                                           self.list_of_bufr_pointers.pop()
                            # restore the previous msg start pos
                            # to allow trying to search again for a correct
                            # end marker
                            start_pos = prev_start_pos
                            if (self.verbose):
                                print "restored start_pos = ", start_pos

                            # step over the "7777" string to prepare for
                            #  searching the real end of the message
                            search_pos = end_pos
                        else:
                            # step over the "BUFR" string to prepare for
                            #  searching the end of the message
                            search_pos = start_pos+4


                else:
                    # check the distance to the fileend
                    # This should be no more than 4 bytes.
                    # If it is larger we have found a false "7777"
                    # end marker (or the file is corrupted and truncated)
                    distance = (self.filesize-end_pos)
                    if (self.verbose):
                        print "distance to fileend = ", distance, " bytes"
                    if (distance > 3):
                        # this means we have found a false "7777"
                        # end marker, so ignore the last added msg
                        # and start looking again
                        (prev_start_pos, prev_end_pos) = \
                                       self.list_of_bufr_pointers.pop()
                        # restore the previous msg start pos
                        # to allow trying to search again for a correct
                        # end marker
                        start_pos = prev_start_pos
                        if (self.verbose):
                            print "restored start_pos = ", start_pos
                        
                        # step over the "7777" string to prepare for
                        #  searching the real end of the message
                        search_pos = end_pos

                        # file end was not yet reached, keep on looking
                        file_end_reached = False
                        inside_message = True
                    else:
                        # file end was not really reached
                        file_end_reached = True

                    
            if (inside_message and not file_end_reached):
                # try to find a txt_end string
                end_pos = self.data.find(txt_end, search_pos)
                if (self.verbose):
                    print "search_pos = ", search_pos, \
                          " end_pos = ", end_pos, \
                          " txt = ", txt_end

                if (end_pos != -1):
                    inside_message = False

                    # point to the end of the four sevens
                    # (in slice notation, so the bufr msg data
                    # can be adressed as data[start_pos:end_pos])
                    end_pos = end_pos+4
                    
                    # step over the "7777" string to prepare for searching the
                    # end of the message
                    search_pos = end_pos

                    # store the found message
                    self.list_of_bufr_pointers.append((start_pos, end_pos))
                else:
                    file_end_reached = True

        # count howmany we found
        self.nr_of_bufr_messages = len(self.list_of_bufr_pointers)
        #  #]
    def get_num_bufr_msgs(self):
        #  #[
        if (self.bufr_fd == None):
            print "ERROR: a bufr file first needs to be opened"
            print "using BUFRFile.open() before you can request the"
            print "number of BUFR messages in a file .."
            raise IOError

        return self.nr_of_bufr_messages
        #  #]
    def get_raw_bufr_msg(self, msg_nr):
        #  #[
        # get the raw data for the bufr msg with given nr (start counting at 1)
        
        if (self.bufr_fd == None):
            print "ERROR: a bufr file first needs to be opened"
            print "using BUFRFile.open() before you can use the raw data .."
            raise IOError

        # sanity test
        if (msg_nr>self.nr_of_bufr_messages):
            print "WARNING: non-existing BUFR message: ", msg_nr
            print "This file only contains: ", self.nr_of_bufr_messages, \
                  " BUFR messages"
            return None

        if (msg_nr<1):
            print "WARNING: invalid BUFR message number: ", msg_nr
            print "For this file this number should be between 1 and: ", \
                  self.nr_of_bufr_messages
            return None

        self.last_used_msg = msg_nr
        (start_index, end_index) = self.list_of_bufr_pointers[msg_nr-1]

        size_bytes = (end_index-start_index)

        # +3 because we have to round upwards to make sure all
        # bytes fit into the array of words (otherwise the last
        # few might be truncated from the data, which will crash
        # the struct.unpack() call below)
        size_words = (size_bytes+3)/4
        padding_bytes = size_words*4-size_bytes

        if (self.verbose):
            print "size_bytes = ", size_bytes
            print "size_words = ", size_words
            print "size_words*4 = ", size_words*4
            print "padding_bytes = ", padding_bytes
            
        # make sure we take the padding bytes along
        end_index = end_index+padding_bytes
        
        raw_data_bytes = self.data[start_index:end_index]
        if (self.verbose):
            print "len(raw_data_bytes) = ", len(raw_data_bytes)

        # assume little endian for now when converting
        # raw bytes/characters to integers and vice-versa
        format = "<"+str(size_words)+"i"
        words = np.array(struct.unpack(format, raw_data_bytes))

        return words
        #  #]
    def get_next_raw_bufr_msg(self):
        #  #[
        return self.get_raw_bufr_msg(self.last_used_msg+1)
        #  #]
    def write_raw_bufr_msg(self, words):
        #  #[
        # input data should be an array of words!
        size_words = len(words)
        size_bytes = size_words*4
        if (self.verbose):
            print "size_bytes = ", size_bytes
            print "size_words = ", size_words

        # convert the words to bytes in a string and write them to file

        # question: is this conversion really needed, or could I also just
        # directly write the data as words?
        # Answer: yes this really is needed! If the words are just written
        # as such, python converts them to long integers and writes
        # 8 bytes for each word in stead of 4 !!!!!
        # activate the next 2 lines to test this:
        #self.bufr_fd.write(words)
        #return
        
        # assume little endian for now when converting
        # raw bytes/characters to integers and vice-versa
        format = "<i"
        for (i, w) in enumerate(words):
            data = struct.pack(format, w)
            self.bufr_fd.write(data)

            if i == 0:
                if (self.verbose):
                    print "w = ", w
                    print 'data = ', data
                    print 'data[:4] = ', data[:4]
                    print 'data[:4] = ', ';'.join(str(data[j])
                                                 for j in range(4) \
                                                 if data[j].isalnum())
                # safety check
                assert(data[:4] == 'BUFR')

        self.nr_of_bufr_messages = self.nr_of_bufr_messages + 1
        self.filesize = self.filesize + size_bytes
        #  #]
    #  #]

if __name__ == "__main__":
    #  #[ test program
    print "Starting test program:"

    #  import additional modules needed for testing
    import ecmwfbufr # import the just created wrapper module
    import unittest  # import the unittest functionality
    
    class CheckRawECMWFBUFR(unittest.TestCase):
        #  #[ 3 tests
        # note: tests MUST have a name starting with "test"
        #       otherwise the unittest module will not use them
        example_programs_dir = "example_programs/"
        def test_run_decoding_example(self):
            #  #[
            # run the provided example code and verify the output
            testprog = "example_for_using_ecmwfbufr_for_decoding.py"
            cmd = os.path.join(self.example_programs_dir, testprog)
            success = call_cmd_and_verify_output(cmd)
            self.assertEqual(success, True)                
            #  #]
        def test_run_encoding_example(self):
            #  #[
            # run the provided example code and verify the output
            testprog = "example_for_using_ecmwfbufr_for_encoding.py"
            cmd = os.path.join(self.example_programs_dir, testprog)
            success = call_cmd_and_verify_output(cmd)
            self.assertEqual(success, True)                
            #  #]
        def test_run_pb_routines_example(self):
            #  #[
            
            # NOTE: for debugging the pb-routines it is possible
            # to set the PBIO_PBOPEN environment setting to a value
            # of 1. From this it is clear that the pbopen code is
            # executed, and the problem is in the interfacingm which
            # leads to this error:
            #
            # SystemError: NULL result without error in PyObject_Call
            
            # run the provided example code and verify the output
            testprog = "example_for_using_pb_routines.py"
            cmd = os.path.join(self.example_programs_dir, testprog)
            success = call_cmd_and_verify_output(cmd)
            self.assertEqual(success, True)                
            #  #]
        #  #]

    class CheckBUFRInterfaceECMWF(unittest.TestCase):
        #  #[ 4 tests
        # note: tests MUST have a name starting with "test"
        #       otherwise the unittest module will not use them
        example_programs_dir = "example_programs/"
        def test_init(self):
            #  #[
            # just instantiate the class
            # since this was done already above, before starting the
            # sequence of unit tests, and since we omit the verbose
            # option, this should be silent
            BI = BUFRInterfaceECMWF()
            
            # check its type
            b1 = isinstance(BI, BUFRInterfaceECMWF)
            self.assertEqual(b1, True)
            b2 = isinstance(BI, int)
            self.assertEqual(b2, False)
            
            # check that a call with a non-defined keyword fails
            self.assertRaises(TypeError,
                              BUFRInterfaceECMWF, dummy = 42)
            
            # todo: implement this (if this turns out to be important)
            # the module does no typechecking (yet) on its
            # inputs, so this one is not yet functional
            # self.assertRaises(TypeError,
            #                  BUFRInterfaceECMWF, verbose = 42)
            
            #  #]
        def test_get_expected_ecmwf_bufr_table_names(self):
            #  #[
            center               = 210 # = ksec1( 3)
            subcenter            =   0 # = ksec1(16)
            local_version        =   1 # = ksec1( 8)
            master_table_version =   0 # = ksec1(15)
            edition_number       =   3 # =  ksec0( 3)
            master_table_number  =   0 # = ksec1(14)
            BI = BUFRInterfaceECMWF()

            # dont use this! This would need an import of helpers
            # which in turn imports pybufr_ecmwf so would give a circular
            # dependency ...
            # ecmwf_bufr_tables_dir = helpers.get_tables_dir()
            
            this_path,this_file = os.path.split(__file__)
            ecmwf_bufr_tables_dir = os.path.join(this_path,"ecmwf_bufrtables")
            if not os.path.exists(ecmwf_bufr_tables_dir):
                print "Error: could not find BUFR tables directory"
                raise IOError
            
            # make sure the path is absolute, otherwise the ECMWF library
            # might fail when it attempts to use it ...
            ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
        
            (b, d) = BI.get_expected_ecmwf_bufr_table_names(
                            ecmwf_bufr_tables_dir,
                            center,
                            subcenter,
                            local_version,
                            master_table_version,
                            edition_number,
                            master_table_number)

            # print "tabel name B: ", b
            # print "tabel name D: ", d
            self.assertEqual(b, 'B0000000000210000001.TXT')
            self.assertEqual(d, 'D0000000000210000001.TXT')
            #  #]
        def test_run_decoding_example(self):
            #  #[
            # run the provided example code and verify the output
            testprog = "example_for_using_bufrinterface_ecmwf_for_decoding.py"
            cmd = os.path.join(self.example_programs_dir, testprog)
                               
            success = call_cmd_and_verify_output(cmd)
            self.assertEqual(success, True)                
            #  #]
        def test_run_encoding_example(self):
            #  #[
            # run the provided example code and verify the output
            testprog = "example_for_using_bufrinterface_ecmwf_for_encoding.py"
            cmd = os.path.join(self.example_programs_dir, testprog)
                               
            success = call_cmd_and_verify_output(cmd)
            self.assertEqual(success, True)                
            #  #]

        #  #]
            
    class CheckRawBUFRFile(unittest.TestCase):
        #  #[ 4 tests
        # note: tests MUST have a name starting with "test"
        #       otherwise the unittest module will not use them
        #
        # common settings for the following tests
        input_test_bufr_file = 'testdata/Testfile3CorruptedMsgs.BUFR'
        def test_init(self):
            #  #[
            BF1 = RawBUFRFile(verbose = True)
            self.assertEqual(BF1.bufr_fd, None)
            self.assertEqual(BF1.filename, None)
            self.assertEqual(BF1.filemode, None)
            self.assertEqual(BF1.filesize, None)
            self.assertEqual(BF1.data, None)
            self.assertEqual(BF1.list_of_bufr_pointers, [])
            self.assertEqual(BF1.nr_of_bufr_messages, 0)
            self.assertEqual(BF1.last_used_msg, 0)
            self.assertEqual(BF1.verbose, True)
            BF2 = RawBUFRFile(verbose = False)
            self.assertEqual(BF2.verbose, False)
            #  #]
        def test_open(self):
            #  #[
            BF1 = RawBUFRFile(verbose = False)
            
            # check behaviour when mode is missing
            self.assertRaises(TypeError,
                              BF1.open, self.input_test_bufr_file)
            
            # check behaviour when mode is invalid
            self.assertRaises(AssertionError,
                              BF1.open, self.input_test_bufr_file, 'q')
            
            # check behaviour when filename is not a string
            self.assertRaises(TypeError, BF1.open, 123, 'r')
            
            # check behaviour when file does not exist
            self.assertRaises(IOError, BF1.open, 'dummy', 'r',
                              silent = True)
            
            # check behaviour when reading a file without proper permission
            testfile = "tmp_testfile.read.BUFR"
            if (os.path.exists(testfile)):
                # force the file to be readwrite
                os.chmod(testfile, 0666)
                os.remove(testfile)
            # create a small dummy fle
            fd = open(testfile, 'wt')
            fd.write('dummy data')
            fd.close()
            # force the file to be unaccessible
            os.chmod(testfile, 0000)
            # do the test
            self.assertRaises(IOError, BF1.open, testfile, 'r',
                              silent = True)
            # cleanup
            if (os.path.exists(testfile)):
                # force the file to be readwrite
                os.chmod(testfile, 0666)
                os.remove(testfile)
                    
            # check behaviour when writing to file without proper permission
            testfile = "tmp_testfile.write.BUFR"
            if (os.path.exists(testfile)):
                # force the file to be readwrite
                os.chmod(testfile, 0666)
                os.remove(testfile)
            # create a small dummy fle
            fd = open(testfile, 'wt')
            fd.write('dummy data')
            fd.close()
            # force the file to be readonly
            os.chmod(testfile, 0444)
            # do the test
            self.assertRaises(IOError, BF1.open, testfile, 'w',
                              silent = True)
            # cleanup
            if (os.path.exists(testfile)):
                # force the file to be readwrite
                os.chmod(testfile, 0666)
                os.remove(testfile)                
            #  #]
        def test_close(self):
            #  #[
            BF1 = RawBUFRFile(verbose = False)
            BF1.open(self.input_test_bufr_file, 'r')
            BF1.close()
            
            # check that a second close fails
            self.assertRaises(AttributeError, BF1.close)
            #  #]
        def test_run_example(self):
            #  #[
            # run the provided example code and verify the output
            cmd = "example_programs/example_for_using_rawbufrfile.py"
            success = call_cmd_and_verify_output(cmd)
            self.assertEqual(success, True)                
            #  #]
        #  #]

    # this just runs all tests
    print "Running unit tests:"
    unittest.main()
    #  #]
    
# still todo:
#
# add test calls to:
#   bupkey: pack ecmwf specific key into section 2
# and possibly to:
#   btable: tries to load a bufr-B table
#    [usefull for testing the presence of a needed table]
#   get_name_unit: get a name and unit string for a given descriptor
#   buprq: sets some switches that control the bufr library

