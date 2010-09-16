#!/usr/bin/env python

"""
This file defines the BUFRInterfaceECMWF class, a higher level
interface around the raw ecmwfbufr fortran-to-c-to-python interface,
to make it a bit easier in dayly use.
"""

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
#import sys         # system functions
import time        # handling of date and time
import numpy as np # import numerical capabilities

# import some home made helper routines
from helpers import EcmwfBufrLibError
from helpers import EcmwfBufrTableError

# import the raw wrapper interface to the ECMWF BUFR library
import ecmwfbufr
from bufr_template import BufrTemplate

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
    def __init__(self, encoded_message=None,
                 max_nr_descriptors=20,
                 max_nr_expanded_descriptors=140):
        #  #[
        """
        initialise all module parameters needed for encoding and decoding
        BUFR messages
        """
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
        """
        derive the BUFR table names as expected by the ECMWF software
        from a number of parameters that should be available in
        sections 0, 1 and 2.
        """
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
        """
        decode sections 0, 1 and 2 using bus012
        """
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
            raise EcmwfBufrLibError(self.explain_error(kerr, 'bus012'))

        self.sections012_decoded = True
        #  #]
    def decode_sections_0123(self):
        #  #[ wrapper for bus0123
        """
        decode sections 0, 1, 2 and 3 using bus0123
        """

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
            raise EcmwfBufrLibError(self.explain_error(kerr, 'bus0123'))

        self.sections012_decoded  = True
        self.sections0123_decoded = True
        #  #]
    def setup_tables(self, table_b_to_use=None, table_d_to_use=None):
        #  #[ routine for easier handling of tables
        """
        helper routine, to enable automatic or manual setting of table names,
        which in turn are transferred to the ECMWF library using an
        appropriate environment setting
        """
        
        if (not self.sections012_decoded):
            errtxt = "Sorry, setting up BUFR tables is only possible after "+\
                     "sections 0,1,2 of a BUFR message have been decoded "+\
                     "with a call to decode_sections_012"
            raise EcmwfBufrLibError(errtxt)

        # dont use this! This would need an import of helpers
        # which in turn imports pybufr_ecmwf so would give a circular
        # dependency ...
        #ecmwf_bufr_tables_dir = helpers.get_tables_dir()

        this_path = os.path.split(__file__)[0]
        ecmwf_bufr_tables_dir = os.path.join(this_path, "ecmwf_bufrtables")
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

        if ( (table_b_to_use is not None) and
             (table_d_to_use is not None)    ):
            # case 1)
            # create symbolic links from the provided tables to the
            # expected names in the private_bufr_tables_dir
            source_b = table_b_to_use
            source_d = table_d_to_use
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
        """
        print content of sections 0, 1 and 2 using buprs0/1/2
        """

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
            kerr = 0
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
        kerr = 0

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
        if self.ksec4[0] == 0:
            errtxt = "Sorry, call to bufrex failed, Maybe you have choosen "+\
                     "a too small value for max_nr_expanded_descriptors?"
            raise EcmwfBufrLibError(errtxt)
        
        self.data_decoded = True
        #  #]
    def print_sections_012_metadata(self):
        #  #[
        """
        print metadata and content of sections 0, 1 and 2
        """
        
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
        """
        print metadata and content of sections 0, 1, 2 and 3
        """
        
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
        """
        print metadata and content of sections 0, 1, 2 and 3
        """

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
        """
        print names and units for the current expanded descriptor list
        """

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
    def explain_error(self, kerr, subroutine_name):
        #  #[ explain error codes returned by the bufrlib routines
        """
        a helper subroutine to print some helpfull information
        if one of the library routines returns with an error
        """

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
        """
        a helper function to request the number of subsets for the
        current BUFR message
        """
        
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
        """
        a helper function to request the number of elements in each subset
        for the current BUFR message
        """

        if (not self.sections012_decoded):
            errtxt = "Sorry, the number of elements is only available after "+\
                     "a BUFR message has been decoded with a call to "+\
                     "decode_sections_012"
            raise EcmwfBufrLibError(errtxt)
        return self.ksup[4]
        #  #]
    def get_values(self, i):
        #  #[ get the i th number from each subset as an array
        """
        a helper function to request the i th value from each subset
        for the current BUFR message as an array
        """
        if (not self.data_decoded):
            errtxt = "Sorry, retrieving values is only possible after "+\
                     "a BUFR message has been decoded with a call to "+\
                     "decode_data"
            raise EcmwfBufrLibError(errtxt)

        nsubsets  = self.get_num_subsets()
        nelements = self.get_num_elements()
        if i > nelements-1:
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
    def get_element_name_and_unit(self, i):
        #  #[
        """
        a helper routine to request the element name and unit
        for the given index in the expanded descriptor list of the
        current BUFR message
        """
        if (not self.data_decoded):
            errtxt = "Sorry, names and units are only available after "+\
                     "a BUFR message has been decoded with a call to "+\
                     "decode_data"
            raise EcmwfBufrLibError(errtxt)

        nelements = self.get_num_elements()
        if i > nelements-1:
            errtxt = "Sorry, this BUFR message has only "+str(nelements)+\
                     " elements per subset, so requesting name and unit for "+\
                     "index "+str(i)+" is not possible "+\
                     "(remember the arrays are counted starting with 0)"
            raise EcmwfBufrLibError(errtxt)

        txtn = ''.join(c for c in self.cnames[i])
        txtu = ''.join(c for c in self.cunits[i])

        return (txtn.strip(), txtu.strip())
        #  #]
    def fill_descriptor_list(self):
        #  #[ fills both the normal and expanded descriptor lists
        """
        fill the normal and expanded descriptor lists (defines the
        names and units, which is needed only in case you wish to request
        and or print these)
        """
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
            raise EcmwfBufrLibError(self.explain_error(kerr, 'bufrex'))

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
        """
        request the raw descriptor list in numeric form
        """
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
        """
        request the expanded descriptor list in numeric form
        """
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
        """
        print the raw and expanded descriptor lists (names and units)
        using the buprs3 library routine (not that fill_descriptor_list
        nees to be called first before this will work)
        """

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
        """
        helper routine to fill sections 0, 2, 3 and 3 of a BUFR
        message, using symbolic names to make this easier (and
        hopefully prevent mistakes)
        """

        # fill section 0
        self.ksec0[1-1] = 0 # length of sec0 in bytes
        #                     [filled by the encoder]
        self.ksec0[2-1] = 0 # total length of BUFR message in bytes
        #                     [filled by the encoder]
        self.ksec0[3-1] = bufr_edition

        # fill section 1
        self.ksec1[ 1-1] =  22               # length sec1 bytes
        #                                     [filled by the encoder]
        # (note: this may depend on the bufr_edition nr.)
        
        # however,a minimum of 22 is obliged here
        self.ksec1[ 2-1] = bufr_edition      # bufr edition
        self.ksec1[ 3-1] = bufr_code_centre  # originating centre
        self.ksec1[ 4-1] =   1               # update sequence number
        # usually 1, only updated if the same data is re-issued after
        # reprocessing or so to fix some bug/problem
        self.ksec1[ 5-1] =   0               # (Flags presence of section 2)
        #                                     (0/128 = no/yes)
        self.ksec1[ 6-1] = bufr_obstype              # message type
        self.ksec1[ 7-1] = bufr_subtype              # subtype
        self.ksec1[ 8-1] = bufr_table_local_version  # version of local table
        # (this determines the name of the BUFR table to be used)

        # fill the datetime group. Note that it is not yet clear to me
        # whether this should refer to the encoding datetime or to the
        # actual measurement datetime. So allow the user to set the value,
        # but use the current localtime if not provided.
        if datetime is not None:
            (year, month, day, hour, minute, second,
             weekday, julianday, isdaylightsavingstime) = datetime
        else:
            (year, month, day, hour, minute, second,
             weekday, julianday, isdaylightsavingstime) = time.localtime()
            
        self.ksec1[ 9-1] = (year-2000) # Without offset year - 2000
        self.ksec1[10-1] = month       # month
        self.ksec1[11-1] = day         # day
        self.ksec1[12-1] = hour        # hour
        self.ksec1[13-1] = minute      # minute

        self.ksec1[14-1] = bufr_table_master         # master table
        # (this determines the name of the BUFR table to be used)
        self.ksec1[15-1] = bufr_table_master_version # version of master table
        # (this determines the name of the BUFR table to be used)

        # NOTE on filling items 16,17,18: this is the way to do it in edition 3
        # TODO: adapt this procedure to edition 4, which requires
        # filling 2 more datetime groups en the actual latitude
        # and longitude ranges
        # See bufrdc/buens1.F for some details.

        # ksec1 items 16 and above are to indicate local centre information
        self.ksec1[16-1] = bufr_code_subcentre       # originating subcentre
        # (this determines the name of the BUFR table to be used)
        self.ksec1[17-1] =   0
        self.ksec1[18-1] =   0

        # a test for filling ksec2 is not yet defined
    
        # fill section 3
        self.ksec3[1-1] = 0
        self.ksec3[2-1] = 0
        self.ksec3[3-1] = num_subsets                # no of data subsets
        self.ksec3[4-1] = bufr_compression_flag      # compression flag

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
    def register_and_expand_descriptors(self, BT):
        #  #[
        """
        expand the descriptor list, generating the expanded list
        from the raw list by calling buxdes, with some additional
        logic to make it easier to use delayed replication in your
        templates.
        """
        kerr   = 0

        # input: BT must be an instance of the BufrTemplate class
        # so check this:
        assert(isinstance(BT, BufrTemplate))
        
        # length of unexpanded descriptor list
        self.ktdlen = len(BT.unexpanded_descriptor_list)
        # convert the unexpanded descriptor list to a numpy array
        self.ktdlst = np.array(BT.unexpanded_descriptor_list, dtype=np.int)
        print "unexpanded nr of descriptors = ", self.ktdlen
        print "The current list is: ", self.ktdlst
        
        # call BUXDES
        # buxdes: expand the descriptor list
        #         and fill the array ktdexp and the variable ktdexp
        #         [only needed when creating a bufr msg with table D entries
        #          but I'll run ot anyway for now since this usually is
        #          a cheap operation, so a user should not be bothered by it]
        
        # iprint = 0 # default is to be silent
        iprint = 1
        if (iprint == 1):
            print "------------------------"
            print " printing BUFR template "
            print "------------------------"

        # define and fill the list of replication factors
        self.kdata = np.zeros(self.nr_subsets*
                              BT.nr_of_delayed_repl_factors, dtype=np.int)
        i = 0
        for subset in range(self.nr_subsets):
            # Warning: just set the whole array to the maximum you wish to have.
            # Letting this number vary seems not to work with the current
            # ECMWF library. It will allways just look at the first element
            # in the kdata array. (or do I misunderstand the BUFR format here?)
            for max_repeats in BT.del_repl_max_nr_of_repeats_list:
                self.kdata[i] = max_repeats
                i += 1
                
        print "delayed replication factors: ", self.kdata

        ecmwfbufr.buxdes(iprint,
                         self.ksec1,
                         self.ktdlst,
                         self.kdata,
                         self.ktdexl,
                         self.ktdexp,
                         self.cnames,
                         self.cunits,
                         kerr)
        print "ktdlst = ", self.ktdlst
        selection = np.where(self.ktdexp>0)
        print "ktdexp = ", self.ktdexp[selection]
        # print "ktdexl = ", self.ktdexl # this one seems not to be filled ...?
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr, 'buxdes'))

        # It is not clear to me why buxdes seems to correctly produce
        # the expanded descriptor list, but yet it does
        # not seem to fill the ktdexl value.
        # To fix this the next 2 lines have been added:
        selection2 = np.where(self.ktdexp > 0)
        self.ktdexl = len(selection2[0])

        # these are filled as well after the call to buxdes
        # print "cnames = ", self.cnames
        # print "cunits = ", self.cunits

        self.bufr_template_registered = True

        #  #]        
    def encode_data(self, values, cvals):
        #  #[ call bufren to encode a bufr message
        """
        encode all header sections and the data section to construct
        the BUFR message in binary/compressed form
        """
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
        words = np.zeros(num_words, dtype=np.int)

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
            raise EcmwfBufrLibError(self.explain_error(kerr, 'bufren'))

        print "words="
        print words
        nw = len(np.where(words>0)[0])
        print "encoded size: ", nw, " words or ", nw*4, " bytes"

        self.data_encoded = True
        #  #]
        
#  #]
