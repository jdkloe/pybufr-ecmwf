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
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

#
#  #]
#  #[ imported modules
from __future__ import (absolute_import, division,
                        print_function) #, unicode_literals)
import os          # operating system functions
import sys         # system functions
import time        # handling of date and time
import numpy as np # import numerical capabilities
import struct      # allow converting c datatypes and structs
import tempfile    # handling temporary files
import uuid        # get unique id strings

# import the raw wrapper interface to the ECMWF BUFR library
try:
    from . import ecmwfbufr
except ImportError as e:
    print('import of ecmwfbufr failed.')
    print('sys.path = ', sys.path)
    raise e

from . import ecmwfbufr_parameters
from .bufr_template import BufrTemplate
from .bufr_table import (BufrTable,
                         Short_Delayed_Descr_Repl_Factor,
                         Delayed_Descr_Repl_Factor,
                         Extended_Delayed_Descr_Repl_Factor,
                         Delayed_Descr_and_Data_Rep_Factor,
                         Ext_Delayed_Descr_and_Data_Rep_Factor)
from .helpers import python3
from .custom_exceptions import (EcmwfBufrLibError, EcmwfBufrTableError,
                                IncorrectUsageError)
#  #]

class BUFRInterfaceECMWF:
    #  #[
    """
    a class of wrapper and helper functions to allow easier use of the
    raw ECMWF BUFR interface wrapper
    """
    #  #[ local constant parameters

    # some default array sizes used by the ecmwf interface
    size_ksup  = ecmwfbufr_parameters.JSUP
    size_ksec0 = ecmwfbufr_parameters.JSEC0
    size_ksec1 = ecmwfbufr_parameters.JSEC1
    size_ksec2 = ecmwfbufr_parameters.JSEC2
    size_key   = ecmwfbufr_parameters.JKEY
    size_ksec3 = ecmwfbufr_parameters.JSEC3
    size_ksec4 = ecmwfbufr_parameters.JSEC4

    bufr_tables_env_setting_set_by_script = False
    
    #  #]
    def __init__(self, encoded_message=None, section_sizes=None,
                 section_start_locations=None, verbose=False,
                 expand_flags=False):
        #  #[
        """
        initialise all module parameters needed for encoding and decoding
        BUFR messages
        """
        # this array will hold the binary message before decoding from
        # or after encoding to the raw BUFR format
        # (usually stored as a 4-byte integer array)
        self.encoded_message = encoded_message

        # these tuples hold some metadata that was retrieved by the raw
        # reading method get_raw_bufr_msg defined in raw_bufr_file.py
        self.section_sizes = section_sizes
        self.section_start_locations = section_start_locations

        self.verbose = verbose

        # NOTE: the ECMWF BUFR library provides the functions
        # bufrdc/getflag.F and bufrdc/getcode.F for flag handling
        # but I find it easier to handle them entirely inside python
        # so I added custom code for this,
        self.expand_flags = expand_flags

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

        # define the needed sizes.
        # At the moment these are only used during encoding.
        #self.max_nr_descriptors          = 20 # 44
        self.max_nr_expanded_descriptors = 50

        self.actual_nr_of_expanded_descriptors = None
        
        self.nr_of_descriptors_startval = 50
        #self.nr_of_descriptors_maxval   = 400000000
        self.nr_of_descriptors_maxval   = 500000
        self.nr_of_descriptors_multiplyer = 10
        
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

        # self.krdlen = self.max_nr_delayed_replication_factors

        # filling this one is delayed in case of decoding
        # since the nr of subsets is only known after decoding
        # sections 0 upto 3. 
        # self.kvals  = self.max_nr_expanded_descriptors*self.max_nr_subsets
        self.kvals = None
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
        self.ktdlst = None # will hold unexpanded descriptor list
        self.ktdexl = 0 # will hold nr of expanded descriptors
        self.ktdexp = None # will hold expanded descriptor list

        # the list of max nr of delayed replications is filled
        # inside the register_and_expand_descriptors method
        self.kdata = None
        
        # arrays to hold the actual numerical and string values
        self.cnames = None
        self.cunits = None

        # note: these next 2 arrays might become very large, especially
        # the cvals array, so in order to keep them as small as possible
        # I'll only define and allocate them after the number of subsets
        # has been retrieved (so just before entering the bufrex routine)
        self.values = None
        self.cvals  = None
        
        # location for storing temporary files, include the uid
        # in the name to make sure the path is unique for each user
        self.temp_dir = ('/tmp/pybufr_ecmwf_temporary_files_'+
                         str(os.getuid()))

        # ensure the directory needed to store temporary files is present
        if not os.path.exists(self.temp_dir):
            os.mkdir(self.temp_dir)

        # path in which symlinks will be created to the BUFR tables we need
        # (note that it must be an absolute path! this is required by the
        #  ecmwf library)
        self.private_bufr_tables_dir = \
             os.path.abspath(os.path.join(self.temp_dir,
                                          'tmp_BUFR_TABLES'))
    

        # ensure the directory exsists in which we will create
        # symbolic links to the bufr tables to be used
        if (not os.path.exists(self.private_bufr_tables_dir)):
            os.mkdir(self.private_bufr_tables_dir)

        # store the user supplied environment setting for BUFR_TABLES
        # to allow later use by the setup_tables method
        self.bufr_tables_env_setting = None
        if not self.__class__.bufr_tables_env_setting_set_by_script:
            if 'BUFR_TABLES' in os.environ:
                self.bufr_tables_env_setting = os.environ['BUFR_TABLES']

        # make sure the BUFR tables can be found
        # also, force a slash at the end, otherwise the library fails
        # to find the tables (at least this has been the case for many
        # library versions I worked with)
        os.environ["BUFR_TABLES"] = (self.private_bufr_tables_dir +
                                     os.path.sep)
        # the above works just fine for me, no need for this one:
        #os.putenv("BUFR_TABLES",self.private_bufr_tables_dir+os.path.sep)

        self.tables_have_been_setup = False
        self.table_b_file_to_use = None
        self.table_d_file_to_use = None
        self.ecmwf_bufr_tables_dir = None
        
        # lists used by the python extraction of the descriptors
        self.py_num_subsets = 0
        self.py_unexp_descr_list = None
        self.py_expanded_descr_list = None
        self.delayed_repl_present = False
        self.delayed_repl_problem_reported = False
        
        self.outp_file = None

        # to store the loaded BUFR table information
        self.bt = None

        # to store the loaded BUFR template information
        self.BufrTemplate = None
        #  #]        
    def get_expected_ecmwf_bufr_table_names(self,
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

        # some codes to define the conventions
        conv_undefined = -1
        conv_short     =  1
        conv_medium    =  2
        conv_long      =  3

        #-------------------------------------------------------------
        # see which BUFR tables naming convention is used (short/long)
        #-------------------------------------------------------------
        bufrtable_naming_convention = conv_undefined

        testfile = os.path.join(self.ecmwf_bufr_tables_dir, testfile_short)
        if (os.path.exists(testfile)):
            #print("Using short BUFRtables naming convention ...")
            bufrtable_naming_convention = conv_short

        testfile = os.path.join(self.ecmwf_bufr_tables_dir, testfile_medium)
        if (os.path.exists(testfile)):
            #print("Using medium length BUFRtables naming convention ...")
            bufrtable_naming_convention = conv_medium

        testfile = os.path.join(self.ecmwf_bufr_tables_dir, testfile_long)
        if (os.path.exists(testfile)):
            #print("Using long BUFRtables naming convention ...")
            bufrtable_naming_convention = conv_long

        if (bufrtable_naming_convention == conv_undefined):
            print("Sorry, unable to detect which BufrTable naming convention")
            print("should be used. Assuming the short convention .....")
            bufrtable_naming_convention = conv_short

        copy_center            = center
        copy_subcenter         = subcenter
        copy_mastertablenumber = MasterTableNumber
        copy_localversion      = LocalVersion
        
        # exception: if version of local table is set to 0 or 255
        # then use WMO origination centre ID
        if ( (LocalVersion == 0) or (LocalVersion == 255) ):
            copy_center       = 0 # xx (WMO)
            copy_subcenter    = 0 # ww
            copy_localversion = 0 # zz

            zz=0 # local table version

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
                                           MasterTableVersion,
                                           copy_localversion)
            
        elif (bufrtable_naming_convention == conv_medium):
            table_format = "%3.3i%4.4i%4.4i%2.2i%2.2i"
            if (EditionNumber <= 2):
                copy_subcenter         = 0
                copy_mastertablenumber = 0
            numeric_part = table_format % (copy_mastertablenumber,
                                           copy_subcenter, copy_center,
                                           MasterTableVersion,
                                           copy_localversion)

        elif (bufrtable_naming_convention == conv_long):
            table_format = "%3.3i%5.5i%5.5i%3.3i%3.3i"
            if (EditionNumber <= 2):
                copy_subcenter         = 0
                copy_mastertablenumber = 0
            numeric_part = table_format % (copy_mastertablenumber,
                                           copy_subcenter, copy_center,
                                           MasterTableVersion,
                                           copy_localversion)

        name_table_b = 'B'+numeric_part+'.TXT'
        name_table_c = 'C'+numeric_part+'.TXT' # beware, may be missing!
        name_table_d = 'D'+numeric_part+'.TXT'

        # Note that this naming scheme is specific for the ECMWF library
        # and is not related to any BUFR file format requirement
        # Other BUFR file handling libraries might use other conventions.

        # This naming scheme is defined in these BUFR library source files:
        # bufr_*/bufrdc/buetab.F and bufr_*/bufrdc/bugbts.F

        # xx=KSEC1(3)  = kcenter
        # yy=KSEC1(15) = kMasterTableVersion
        # zz=KSEC1(08) = kLocalVersion
        #
        # for bufr editions 1 and 2
        # ww=0
        # ss=0
        #
        # for bufr editions 3 and 4
        # ww=KSEC1(16) = ksubcenter
        # ss=KSEC1(14) = kMasterTableNumber
        #
        # if standard tables used, use WMO origination centre ID
        # so: in case ksec1(8)==0 OR ksec1(8)==255 use
        # xx=0
        # ww=0
        # zz=0
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
        #             B/C/D  - BUFR TABLE B/C/D
        #             SSS    - MASTER TABLE NUMBER (zero for WMP tables)
        #             WWWWW  - ORIGINATING SUB-CENTRE
        #             XXXXX  - ORIGINATING CENTRE
        #             YYY    - VERSION NUMBER OF MASTER
        #                      TABLE USED( CURRENTLY 12 )
        #             ZZZ    - VERSION NUMBER OF LOCAL TABLE USED
        
        return (name_table_b, name_table_c, name_table_d)
        #  #]
    def store_fortran_stdout(self):
        #  #[
        """
        Set the 'STD_OUT' environment variable to redirect the
        fortran output to a temporary file named fort.12
        (or whatever the number in STD_OUT is)
        This is needed because otherwise the fortran and python/c
        output get written to 2 different output buffers, and will
        be mixed in inpredictable ways (which makes it impossible
        to interpret the output or to define unit test cases ...)
        """
        if 'STD_OUT' in os.environ:
            outp_fileunit = os.environ['STD_OUT']
        else:
            outp_fileunit = '12'
            os.environ['STD_OUT'] = outp_fileunit

        # suppres the default ECMWF welcome message which
        # is not yet redirected to the above defined fileunit
        os.environ['PRINT_TABLE_NAMES'] = 'FALSE'

        # Determine filename to use to redirect the fortran stdout stream
        # Note that we cannot directly use the file object returned
        # by tempfile.NamedTemporaryFile() because the actual file
        # will be used inside the underlying fortran library.
        # Therefore just extract the filename and close the file again.

        try:
            # add a random uuid as prefix
            # and the PID as suffix to really make sure there
            # will be no name clashes.
            temp = tempfile.NamedTemporaryFile(suffix='_'+str(os.getpid()), 
                                               prefix=str(uuid.uuid4())+'_', 
                                               dir=self.temp_dir)

            self.fortran_stdout_tmp_file = os.path.split(temp.name)[1]
            temp.close()
        except:
            self.fortran_stdout_tmp_file = 'tmp_fortran_stdout.txt'
        
        # print('fortran_stdout_tmp_file = ', self.fortran_stdout_tmp_file)

        # self.outp_file = 'fort.'+str(outp_fileunit)
        self.outp_file = os.path.join(self.temp_dir,
                                      self.fortran_stdout_tmp_file)
        ecmwfbufr.open_fortran_stdout(self.outp_file)
        #  #]
    def get_fortran_stdout(self):
        #  #[
        """
        retrieve the fortran output that was stored in the temporary
        file by the store_fortran_stdout method
        """

        # close the fortran stdout() channel. This should flush all
        # output may still be buffered at this point
        ecmwfbufr.close_fortran_stdout()
        
        # now read the temporary file and display the output
        if os.path.exists(self.outp_file):
            lines = open(self.outp_file).readlines()
        else:
            lines = []
        
        # finally remove the temporary file
        if os.path.exists(self.outp_file):
            os.remove(self.outp_file)

        return lines
        #  #]        
    def display_fortran_stdout(self,lines):
        #  #[
        """
        display the fortran output that was retrieved by get_fortran_stdout
        """
        if len(lines)>0:
            print('detected ',len(lines),' lines of fortran stdout:')
            for line in lines:
                print('FORTRAN STDOUT: '+line,end='')
        #  #]        
    def decode_sections_012(self):
        #  #[ wrapper for bus012
        """
        decode sections 0, 1 and 2 using bus012
        """
        # running of this routine yields enough meta-data to enable
        # figuring out how to name the expected BUFR tables
        
        kerr = 0

        if self.verbose:
            print("calling: ecmwfbufr.bus012():")
        self.store_fortran_stdout()
        ecmwfbufr.bus012(self.encoded_message, # input
                         self.ksup,  # output
                         self.ksec0, # output
                         self.ksec1, # output
                         self.ksec2, # output
                         kerr)       # output
        lines = self.get_fortran_stdout()
        self.display_fortran_stdout(lines)
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
       
        if self.verbose:
            print("calling: ecmwfbufr.bus012():")
        self.store_fortran_stdout()
        ecmwfbufr.bus0123(self.encoded_message, # input
                          self.ksup,  # output
                          self.ksec0, # output
                          self.ksec1, # output
                          self.ksec2, # output
                          self.ksec3, # output
                          kerr)       # output
        lines = self.get_fortran_stdout()
        self.display_fortran_stdout(lines)
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr, 'bus0123'))

        self.sections012_decoded  = True
        self.sections0123_decoded = True
        #  #]
    def setup_tables(self, table_b_to_use=None, table_c_to_use=None,
                     table_d_to_use=None, tables_dir=None):
        #  #[ routine for easier handling of tables
        """
        helper routine, to enable automatic or manual setting of table names,
        which in turn are transferred to the ECMWF library using an
        appropriate environment setting
        """
        debug=False
        if debug:
            self.verbose = True
            
        if (not self.sections012_decoded):
            errtxt = ("Sorry, setting up BUFR tables is only possible after "+
                      "sections 0,1,2 of a BUFR message have been decoded "+
                      "with a call to decode_sections_012")
            raise EcmwfBufrLibError(errtxt)

        # retrieve the location where this current script is installed
        # because the default ecmwf tables dir should be next to it
        this_path = os.path.dirname(__file__)
        ecmwf_bufr_tables_dir = os.path.join(this_path, "ecmwf_bufrtables")
        if not os.path.exists(ecmwf_bufr_tables_dir):
            print("Error: could not find BUFR tables directory")
            raise IOError

        # make sure the path is absolute, otherwise the ECMWF library
        # might fail when it attempts to use it ...
        self.ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
        # print('self.ecmwf_bufr_tables_dir = ',self.ecmwf_bufr_tables_dir)

        # allow the user to set a tables directory using the BUFR_TABLES
        # environment variable
        self.user_tables_dir = None
        if self.bufr_tables_env_setting:
            if debug:
                print('setup_tables: the user provided a directory to look for')
                print('BUFR tables: ')
                print("==> os.environ['BUFR_TABLES'] = ",
                      self.bufr_tables_env_setting)
            self.user_tables_dir = os.path.abspath(self.bufr_tables_env_setting)

        # allow the user to excplicitely set the tables_dir as an argument
        # to this setup_tables method
        if tables_dir is not None:
            # the user provided a dir to look in for BUFR tables so store it
            # if present, this one overrides the environment setting
            if debug:
                print('setup_tables: the user provided a directory to look for')
                print('BUFR tables: ')
                print('==> tables_dir = ',tables_dir)
            self.user_tables_dir = os.path.abspath(tables_dir)

        # The tables_dir_has_been_defined setting should be preserved
        # between different instances of BUFRInterfaceECMWF.
        # At the second call of setup_tables() the BUFR_TABLES environment
        # variable has already been set by this module, even if the user
        # did not set it, so then this check should not be done.
        # Therefore it has to be a class variable, not an instance variable.
        tables_dir_has_been_defined = False
        if hasattr(self.__class__,'tables_dir_has_been_defined'):
            tables_dir_has_been_defined = \
                   self.__class__.tables_dir_has_been_defined
            
        if not tables_dir_has_been_defined:
            # prohibit the use of the temporary folder below /tmp used
            # by this module to create symlinks to the actual tables
            # because this will mess up the symlinking and produce
            # circular symlink references pointing to nowhere ...
            if self.user_tables_dir is not None:
                if self.user_tables_dir == self.private_bufr_tables_dir:
                    print('ERROR: it is not allowed to explicitely provide '+
                          'the table directory below /tmp used by the')
                    print('pybufr-ecmwf software (which it uses to create '+
                          'symlinks to user provided BUFR tables) as input.')
                    print( 'Please choose another table directory.')
                    sys.exit(1)

            self.__class__.tables_dir_has_been_defined = True
            
        EditionNumber      = self.ksec0[3-1]

        center             = self.ksec1[3-1]
        DataCategory       = self.ksec1[6-1] # or Bufr message type
        LocalVersion       = self.ksec1[8-1]
        MasterTableNumber  = self.ksec1[14-1]
        MasterTableVersion = self.ksec1[15-1]
        subcenter          = self.ksec1[16-1]

        # these category codes are defined in Table A
        if DataCategory == 11:
            print("WARNING: this BUFR msg contains a BUFR table!")
            print("so possibly this BUFR file cannot be decoded by")
            print("using the ECMWF BUFR tables ...")
            print("ecoding BUFR tables provided in the same file")
            print("as the data itself, as is done by NCEP for example,")
            print("is not yet implemented.")
            sys.exit(1)

        ( expected_name_table_b,
          expected_name_table_c,
          expected_name_table_d ) = \
              self.get_expected_ecmwf_bufr_table_names(
                       center, subcenter,
                       LocalVersion, MasterTableVersion,
                       EditionNumber, MasterTableNumber)
        
        if debug:
            print('DEBUG: (expected_name_table_b, expected_name_table_d) = ',
                  (expected_name_table_b, expected_name_table_d))

        userpath_table_b = None
        userpath_table_c = None
        userpath_table_d = None
        if self.user_tables_dir:
            userpath_table_b = os.path.join(self.user_tables_dir,
                                            expected_name_table_b)
            userpath_table_c = os.path.join(self.user_tables_dir,
                                            expected_name_table_c)
            userpath_table_d = os.path.join(self.user_tables_dir,
                                            expected_name_table_d)
            
        fullpath_table_b = os.path.join(self.ecmwf_bufr_tables_dir,
                                        expected_name_table_b)
        fullpath_table_c = os.path.join(self.ecmwf_bufr_tables_dir,
                                        expected_name_table_c)
        fullpath_table_d = os.path.join(self.ecmwf_bufr_tables_dir,
                                        expected_name_table_d)
        fullpath_default_table_b = os.path.join(self.ecmwf_bufr_tables_dir,
                                                'B_default.TXT')
        fullpath_default_table_c = os.path.join(self.ecmwf_bufr_tables_dir,
                                                'C_default.TXT')
        fullpath_default_table_d = os.path.join(self.ecmwf_bufr_tables_dir,
                                                'D_default.TXT')
        if debug:
            print('Debug:')
            print('userpath_table_b:',userpath_table_b)
            print('userpath_table_c:',userpath_table_c)
            print('userpath_table_d:',userpath_table_d)
            print('fullpath_table_b:',fullpath_table_b)
            print('fullpath_table_c:',fullpath_table_c)
            print('fullpath_table_d:',fullpath_table_d)
            print('fullpath_default_table_b:',fullpath_default_table_b)
            print('fullpath_default_table_c:',fullpath_default_table_c)
            print('fullpath_default_table_d:',fullpath_default_table_d)

        # OK, the trick now is to create a symbolic link in a tmp_BUFR_TABLES
        # directory from the name expected by the ecmwf bufr library to:
        #   1) the provided table names (if given) OR
        #   2) the expected table names if present in the user provided
        #      tables directory location OR
        #   3) the expected table names (if present in the ECMWF sources) OR
        #   4) the default tables (and hope they will contain the needed
        #      descriptors to allow proper decoding or encoding)

        # note that self.private_bufr_tables_dir  is defined in __init__
        # now, since this one needs to be set before the bus012 call
        # (while this setup_tables method will be called after the bus012
        #  call because it needs some numbers from the sections 0,1,2)
        
        destination_b = os.path.join(self.private_bufr_tables_dir,
                                     expected_name_table_b)
        destination_c = os.path.join(self.private_bufr_tables_dir,
                                     expected_name_table_c)
        destination_d = os.path.join(self.private_bufr_tables_dir,
                                     expected_name_table_d)

        source_b = None
        source_c = None
        source_d = None
        
        if (table_b_to_use and table_d_to_use):
            if (os.path.exists(table_b_to_use) and
                os.path.exists(table_d_to_use)    ):
                # case 1)
                # create symbolic links from the provided tables to the
                # expected names in the private_bufr_tables_dir
                if debug:
                    print('using user specified tables:')
                    print('table_b_to_use = ',table_b_to_use)
                    print('table_d_to_use = ',table_d_to_use)
                source_b = table_b_to_use
                source_d = table_d_to_use

        # may be absent for now, so handle this one separately
        if table_c_to_use:
            if os.path.exists(table_c_to_use):
                source_c = table_c_to_use
                
        if ( (not source_b) and (not source_d) ):
            if (userpath_table_b and userpath_table_d):
                if (os.path.exists(userpath_table_b) and
                    os.path.exists(userpath_table_d)   ):
                    # case 2)
                    if debug:
                        print('table b and d found in user specified location:')
                        print('userpath_table_b = ',userpath_table_b)
                        print('userpath_table_d = ',userpath_table_d)
                    source_b = userpath_table_b
                    source_d = userpath_table_d
                    # may be absent for now, so put an extra test on it
                    if os.path.exists(userpath_table_c):
                        source_c = userpath_table_c
                
        if ( (not source_b) and (not source_d) ):
            if (os.path.exists(fullpath_table_b) and
                os.path.exists(fullpath_table_d)    ):
                # case 3)
                if debug:
                    print('table b and d found in ecmwf tables collection:')
                    print('fullpath_table_b = ',fullpath_table_b)
                    print('fullpath_table_d = ',fullpath_table_d)
                source_b = fullpath_table_b
                source_d = fullpath_table_d
                # may be absent for now, so put an extra test on it
                if os.path.exists(fullpath_table_c):
                    source_c = fullpath_table_c
                
        if ( (not source_b) and (not source_d) ):
            if (os.path.exists(fullpath_default_table_b) and
                os.path.exists(fullpath_default_table_d)    ):
                # case 4)
                if debug:
                    print('using default tables:')
                    print('fullpath_default_table_b = ',
                          fullpath_default_table_b)
                    print('fullpath_default_table_d = ',
                          fullpath_default_table_d)
                source_b = fullpath_default_table_b
                source_d = fullpath_default_table_d
                if os.path.exists(fullpath_default_table_c):
                    source_c = fullpath_default_table_c

        if ( (not source_b) and (not source_d) ):
            errtxt = ('ERROR: no BUFR tables seem available.' +
                      'please point explicitely to the tables ' +
                      'you wish to use')
            raise EcmwfBufrTableError(errtxt)

        if not source_c:
            print('Warning: no matching C table available for B,D tables')
            print('==>', os.path.split(source_b)[1])
            print('==>', os.path.split(source_d)[1])
            
        # full names, containing full path, are not nice to print
        # in the unit tests since they will differ on different
        # machines, so print the bare filename only
        if self.verbose:
            print('Table names expected by the library:')
            print(os.path.split(destination_b)[1])
            print(os.path.split(destination_c)[1])
            print(os.path.split(destination_d)[1])
            print('Tables to be used:')
            print(os.path.split(source_b)[1])
            if source_c:
                print(os.path.split(source_c)[1])
            else:
                print('[C table is missing]')
            print(os.path.split(source_d)[1])
        
        # make sure any old symbolic link is removed
        # (since it may point to an unwanted location)
        if ( os.path.islink(destination_b) or
             os.path.exists(destination_b)   ):
            os.remove(destination_b)
        if ( os.path.islink(destination_c) or
             os.path.exists(destination_c)   ):
            os.remove(destination_c)
        if ( os.path.islink(destination_d) or
             os.path.exists(destination_d)   ):
            os.remove(destination_d)

        #print("TEST: making symlink from ", source_b,
        #      " to ", destination_b)
        os.symlink(os.path.abspath(source_b), destination_b)
        if source_c:
            #print("TEST: making symlink from ", source_c,
            #      " to ", destination_c)
            os.symlink(os.path.abspath(source_c), destination_c)
        #print("TEST: making symlink from ", source_d,
        #      " to ", destination_d)
        os.symlink(os.path.abspath(source_d), destination_d)
            
        # make sure the BUFR tables can be found
        # also, force a slash at the end, otherwise the library fails
        # to find the tables (at least this has been the case for many
        # library versions I worked with)
        os.environ["BUFR_TABLES"] = (self.private_bufr_tables_dir +
                                     os.path.sep)
        self.__class__.bufr_tables_env_setting_set_by_script = True
        
        self.tables_have_been_setup = True
        self.table_b_file_to_use = destination_b
        self.table_c_file_to_use = None
        if source_c:
            self.table_c_file_to_use = destination_c
        self.table_d_file_to_use = destination_d

        # finally load the tables into memory
        self.bt = BufrTable(tables_dir=self.private_bufr_tables_dir,
                            verbose=False, report_warnings=False)
        #                    verbose=True, report_warnings=True)
        
        # setup_tables already has created the symlinks to the BUFR tables
        # so don't use this autolink feature for now
        # bt = BufrTable(autolink_tablesdir=self.private_bufr_tables_dir,
        #                verbose=False)
        self.bt.load(self.table_b_file_to_use)
        if source_c:
            self.bt.load(self.table_c_file_to_use)
        self.bt.load(self.table_d_file_to_use)

        #  #]
    def print_sections_012(self):
        #  #[ wrapper for buprs0, buprs1, buprs2
        """
        print content of sections 0, 1 and 2 using buprs0/1/2
        """

        if (not self.sections012_decoded):
            errtxt = ("Sorry, printing sections 0,1,2 of a BUFR message " +
                      "is only possible after " +
                      "sections 0,1,2 of a BUFR message have been decoded " +
                      "with a call to decode_sections_012")
            raise EcmwfBufrLibError(errtxt)

        print('------------------------------')
        print("printing content of section 0:")
        self.store_fortran_stdout()
        ecmwfbufr.buprs0(self.ksec0)
        lines = self.get_fortran_stdout()
        self.display_fortran_stdout(lines)
        print('------------------------------')
        print("printing content of section 1:")
        self.store_fortran_stdout()
        ecmwfbufr.buprs1(self.ksec1)
        lines = self.get_fortran_stdout()
        self.display_fortran_stdout(lines)
        print('------------------------------')
        sec2_len = self.ksec2[0]        
        if (sec2_len > 0):
            # buukey expands local ECMWF information
            # from section 2 to the key array
            print('------------------------------')
            print("calling buukey")
            kerr = 0
            self.store_fortran_stdout()
            ecmwfbufr.buukey(self.ksec1,
                             self.ksec2,
                             self.key,
                             self.ksup,
                             kerr)
            lines = self.get_fortran_stdout()
            self.display_fortran_stdout(lines)
            print("printing content of section 2:")
            self.store_fortran_stdout()
            ecmwfbufr.buprs2(self.ksup,
                             self.key)
            lines = self.get_fortran_stdout()
            self.display_fortran_stdout(lines)
        else:
            print('skipping section 2 [since it seems unused]')
        #  #]
    def decode_data(self):
        #  #[
        if (not self.sections012_decoded):
            errtxt = ("Sorry, in order to allow automatic allocation of the "+
                      "values and cvals arrays the number of subsets is "+
                      "needed. Therefore the decode_sections012 or "+
                      "decode_sections_0123 subroutine needs to be called "+
                      "before entering the decode_data subroutine.")
            raise EcmwfBufrLibError(errtxt)

        if not self.tables_have_been_setup:
            errtxt = ("Sorry, you need to tell this module which BUFR tables "+
                      "to use, by calling the setup_tables() method, before "+
                      "you can actually decode a BUFR message.")
            raise EcmwfBufrLibError(errtxt)
                     
        # fill the descriptor list arrays ktdexp and ktdlst
        # this is not strictly needed before entering the decoding
        # but is is the only way to get an accurate value of the actual
        # number of expanded data descriptors, which in turn is needed
        # to limit the memory that we need to pre-allocate for the
        # cvals and values arrays (and especially the cvals array can become
        # rather huge ...)

        # these 2 next methods are python implementations. This is needed
        # because at this point the message is not yet (partially) decoded
        # and no information of the template size is available yet.
        # Howver, this is required to allocated the needed arrays to interface
        # with the ecmwf library, so there is no easy workaround here.
        self.extract_raw_descriptor_list()
        self.expand_raw_descriptor_list()
        # this last method also sets: self.delayed_repl_present

        # after these 2 method calls, these arrays and variables are filled:
        # len(self.py_expanded_descr_list)
        # len(self.py_unexp_descr_list)
        # self.py_num_subsets
        
        # HOWEVER, in case of delayed replication py_expanded_descr_list
        # cannot be filled yet and will be set to None.

        # print('DEBUG: len(self.py_unexp_descr_list) = ',
        #       len(self.py_unexp_descr_list))
        # print('DEBUG: self.py_unexp_descr_list = ',
        #       self.py_unexp_descr_list)
        # if self.py_expanded_descr_list:
        #     print('DEBUG: len(self.py_expanded_descr_list) = ',
        #           len(self.py_expanded_descr_list))
        # else:
        #     print('DEBUG: self.py_expanded_descr_list = ',
        #           self.py_expanded_descr_list)
        # print('DEBUG: self.py_expanded_descr_list = ', 
        #       self.py_expanded_descr_list)
        # self.fill_descriptor_list()
        # self.print_descriptors()
        
        # calculate the needed size of the values and cvals arrays
        nr_of_subsets = self.get_num_subsets()

        # double check: see if both methods to extract num_subsets
        # yield the same number:
        if nr_of_subsets != self.py_num_subsets:
            errtxt = ("a programming error occurred! " +
                      "get_num_subsets() yielded "+str(nr_of_subsets) +
                      " subsets, but extract_raw_descriptor_list() yielded " +
                      str(self.py_num_subsets)+" subsets. " +
                      "These numbers should be identical !!")
            raise EcmwfBufrLibError(errtxt)
        
        # NOTE: this size is the maximum array size that is needed DURING
        # the decoding process. This ALSO includes modification
        # descriptors (with f=2) which are removed again in the
        # final expanded descriptor list. This final list may be
        # smaller in some cases (for example for ERS2 data) than
        # the maximum intermediate size needed....
        if self.py_expanded_descr_list:
            nr_of_descriptors = len(self.py_expanded_descr_list)
        else:
            nr_of_descriptors = self.nr_of_descriptors_startval

        increment_arraysize = True
        while increment_arraysize:
            try:
                self.try_decode_data(nr_of_descriptors, nr_of_subsets)
                increment_arraysize = False
            except EcmwfBufrLibError as e:
                nr_of_descriptors = (nr_of_descriptors *
                                     self.nr_of_descriptors_multiplyer)
                if nr_of_descriptors>self.nr_of_descriptors_maxval:
                    lines = self.get_fortran_stdout()
                    self.display_fortran_stdout(lines)
                    raise e
                else:
                    if self.verbose:
                        print('retrying with: nr_of_descriptors = ',
                              nr_of_descriptors)
        # done
        self.actual_nr_of_expanded_descriptors = self.ksup[4]
        
        # if self.py_expanded_descr_list:
        #     self.actual_nr_of_expanded_descriptors = \
        #                        len(self.py_expanded_descr_list)
        # else:
        #     count = 0
        #     for cname in self.cnames:
        #         # glue the ndarray of characters together to form strings
        #         cname_str = "".join(cname).strip()
        #         if cname_str != '':
        #             count += 1
        #     self.actual_nr_of_expanded_descriptors = count
        # print('DEBUG: self.actual_nr_of_expanded_descriptors = ',
        #       self.actual_nr_of_expanded_descriptors)
        # print('self.ksup[4] = ', self.ksup[4] # real num of exp. elements)
        # print('self.ksup[6] = ', self.ksup[6] # real num of elements in cvals)

        #  #]
    def try_decode_data(self, nr_of_descriptors, nr_of_subsets):
        #  #[ try decoding for a given array length

        kerr = 0

        # calc. needed array sizes
        self.kvals  = nr_of_descriptors*nr_of_subsets
        self.actual_kelem = nr_of_descriptors
        
        # debug
        #self.kvals = self.kvals*120
        
        # print('DEBUG: nr_of_descriptors = ', nr_of_descriptors)
        # print('DEBUG: nr_of_subsets = ', nr_of_subsets)
        # print('DEBUG: self.kvals = ',self.kvals)

        # print('DEBUG: breakpoint')
        #sys.exit(1)

        # allocate space for decoding
        # note: float64 is the default, but it doesn't hurt to make it explicit
        self.values = np.zeros(      self.kvals, dtype = np.float64)
        self.cvals  = np.zeros((self.kvals, 80), dtype = np.character)
        self.cnames = np.zeros((nr_of_descriptors, 64), dtype = '|S1')
        self.cunits = np.zeros((nr_of_descriptors, 24), dtype = '|S1')

        # print('DEBUG: len(self.ksec0)=',len(self.ksec0))
        # print('DEBUG: len(self.ksec1)=',len(self.ksec1))
        # print('DEBUG: len(self.ksec2)=',len(self.ksec2))
        # print('DEBUG: len(self.ksec3)=',len(self.ksec3))
        # print('DEBUG: len(self.ksec4)=',len(self.ksec4))
        # print('DEBUG: len(self.cnames)=',len(self.cnames))
        # print('DEBUG: len(self.cunits)=',len(self.cunits))
        # print('DEBUG: len(self.values)=',len(self.values))
        # print('DEBUG: len(self.cvals)=',len(self.cvals))
        
        self.store_fortran_stdout()
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
        lines = self.get_fortran_stdout()
        # self.display_fortran_stdout(lines)

        # print('DEBUG: self.ksup  = ',self.ksup)
        # print('DEBUG: self.ksec0 = ',self.ksec0)
        # print('DEBUG: self.ksec1 = ',self.ksec1)
        # print('DEBUG: self.ksec2 = ',self.ksec2)
        # print('DEBUG: self.ksec3 = ',self.ksec3)
        # print('DEBUG: self.ksec4 = ',self.ksec4)
        
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr,'bufrex'))

        # note: something seems to fail in case self.kvals (also known
        # as kelem) is too small. bufrex should return with error 25,
        # but in my tests it seems to return with 0.
        # Note that this condition may occur if the user gives a wrong
        # value for max_nr_expanded_descriptors in __init__.
        #
        # Also in case a descriptor is missing from a BUFR table
        # kerr remains zero. This happens if a wrong BUFR table is supplied.
        #
        # Therefore check to see if sec4 was decoded allright (it should
        # contain the length of the encoded section 4 in bytes, so if it
        # remains zero something is very wrong):
        if self.ksec4[0] == 0:
            errtxt = self.analyse_errors_in_fortran_stdout(lines,'bufrex')
            raise EcmwfBufrLibError(errtxt)
        
        self.data_decoded = True
        # self.BufrTemplate = ...
        #  #]
    def print_sections_012_metadata(self):
        #  #[
        """
        print metadata and content of sections 0, 1 and 2
        """
        
        if (not self.sections012_decoded):
            errtxt = ("Sorry, printing sections 0,1,2 of a BUFR message " +
                      "is only possible after a BUFR message has been " +
                      "partially decoded with a call to decode_sections_012")
            raise EcmwfBufrLibError(errtxt)
        
        print("ksup : ", self.ksup)
        print("sec0 : ", self.ksec0)
        print("sec1 : ", self.ksec1)
        print("sec2 : ", self.ksec2)
        #  #]
    def print_sections_0123_metadata(self):
        #  #[
        """
        print metadata and content of sections 0, 1, 2 and 3
        """
        
        if (not self.sections0123_decoded):
            errtxt = ("Sorry, printing sections 0,1,2,3 of a BUFR message " +
                      "is only possible after a BUFR message has been " +
                      "partially decoded with a call to decode_sections_0123")
            raise EcmwfBufrLibError(errtxt)
        
        print("ksup : ", self.ksup)
        print("sec0 : ", self.ksec0)
        print("sec1 : ", self.ksec1)
        print("sec2 : ", self.ksec2)
        print("sec3 : ", self.ksec3)
        #  #]
    def print_sections_01234_metadata(self):
        #  #[
        """
        print metadata and content of sections 0, 1, 2 and 3
        """

        if (not self.data_decoded):
            errtxt = ("Sorry, printing sections 0,1,2,3,4 of a BUFR message "+
                      "is only possible after a BUFR message has been decoded "+
                      "with a call to decode_data")
            raise EcmwfBufrLibError(errtxt)
        
        print("ksup : ", self.ksup)
        print("sec0 : ", self.ksec0)
        print("sec1 : ", self.ksec1)
        print("sec2 : ", self.ksec2)
        print("sec3 : ", self.ksec3)
        print("sec4 : ", self.ksec4)
        #  #]
    def print_names_and_units(self, subset=1):
        #  #[
        """
        print names and units for the current expanded descriptor list
        """

        if (not self.data_decoded):
            errtxt = ("Sorry, names and units are only available after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_data")
            raise EcmwfBufrLibError(errtxt)

        (list_of_names, list_of_units) = self.get_names_and_units(subset)

        print("[index] cname [cunit] : ")

        for i, (txtn, txtu) in enumerate(zip(list_of_names, list_of_units)):
            print('[%3.3i]:%-64s [%-24s]' % (i, txtn, txtu))

        #  #]
    def get_names_and_units(self, subset=1):
        #  #[ request name and unit of each descriptor for the given subset

        if (not self.data_decoded):
            errtxt = ("Sorry, names are only available after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_data")
            raise EcmwfBufrLibError(errtxt)

        if self.delayed_repl_present:
            # each subset may have a different list of descriptors
            # after expansion, so reload the list of names for this subset
            self.expand_descriptors_for_decoding(subset)

        list_of_names = []
        list_of_units = []
        for i in range(self.ktdexl):
            # get the names/units as numpy arrays of characters
            cname = self.cnames[i,:]
            cunit = self.cunits[i,:]
            # glue the ndarray of characters together to form strings
            cname_str = b''.join(cname).strip()
            cunit_str = b''.join(cunit).strip()
            # append the string to the list and quote them
            if python3:
                txtn = cname_str.decode()
                txtu = cunit_str.decode()
            else:
                txtn = cname_str
                txtu = cunit_str

            #if (txtn.strip() != ''):
            list_of_names.append(txtn)
            list_of_units.append(txtu)

        return (list_of_names, list_of_units)
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

        return ('libbufr subroutine ' + subroutine_name +
                ' reported error code: kerr = ' + str(kerr))
        #  #]
    def analyse_errors_in_fortran_stdout(self,lines,funcname):
        #  #[ explain error codes returned by the bufrlib routines
        """
        a helper subroutine to print some helpfull information
        if one of the library routines returns with an error
        indicated by a ksec4[0]==0 condition, while still reporting
        kerr=0. In this case inspect the fortran stdout to see what
        might be wrong.
        """
        
        #errtxt = "Sorry, call to bufrex failed, 

        fortran_errors = [('TABLE B REFERENCE NOT FOUND.',
                           'did you supply the correct BUFR tables?'),
                          ('TABLE D REFERENCE NOT FOUND.',
                           'did you supply the correct BUFR tables?'),
                          ('KELEM ARGUMENT TOO SMALL',
                           'Maybe you have choosen a too small value for '+
                           'max_nr_expanded_descriptors?"')]
        error_list= []
        for l in lines:
            for (ferr, fmsg) in fortran_errors:
                if ferr in l:
                    error_list.append((ferr, fmsg))
                    
        errtxt = ('Sorry, call to '+funcname+' failed, '+
                  'reported fortran error(s)" '+
                  ';'.join('%s (%s)' % (ferr, fmsg)
                           for (ferr, fmsg) in error_list))
        return errtxt
        #  #]
    def get_num_subsets(self):
        #  #[ return number of subsets in this BUFR message
        """
        a helper function to request the number of subsets for the
        current BUFR message
        """
        
        if (not self.sections012_decoded):
            errtxt = ("Sorry, the number of subsets is only available after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_sections_012")
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

        # note: "the current subset is not well defined here"
        # so prevent using this one in case of delayed replication
        self.delayed_repl_check_for_incorrect_use()

        if (not self.data_decoded):
            errtxt = ("Sorry, the number of elements is only available after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_data")
            raise EcmwfBufrLibError(errtxt)
    
        if (not self.sections012_decoded):
            errtxt = ("Sorry, the number of elements is only available after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_sections_012")
            raise EcmwfBufrLibError(errtxt)

        return self.ksup[4]
        #  #]
    def convert_flag_values_to_text(self, values, i):
        #  #[ convert flags to text if needed
        flag_text_values = []
        ref = int(self.ktdexp[i])
        unit = ''.join(c.decode() for c in self.cunits[i])
        if 'TABLE' in unit:
            if ref in self.bt.table_c:
                for v in values:
                    try:
                        flag_text = self.bt.table_c[ref].flag_dict[int(v)]
                    except:
                        flag_text = '<UNDEFINED VALUE>'
                    flag_text_values.append(flag_text)

                return flag_text_values

        # default fallback in case flag seems not defined
        # or C-table is missing or descriptor is numeric after all
        return values
        #  #]
    def get_value(self, i, j, autoget_cval=False):
        #  #[ get the i th value from subset j
        """
        a helper function to request the i th value from subset j
        for the current BUFR message
        Note that subsets start counting at 1!
        """
        if (not self.data_decoded):
            errtxt = ("Sorry, retrieving values is only possible after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_data")
            raise EcmwfBufrLibError(errtxt)

        nsubsets  = self.get_num_subsets()
        nelements = self.get_num_elements()
        if i > nelements-1:
            errtxt = ("Sorry, this BUFR message has only "+str(nelements)+
                      " elements per subset, so requesting index "+
                      str(i)+" is not possible (remember the arrays are "+
                      "counted starting with 0)")
            raise EcmwfBufrLibError(errtxt)

        if j > nsubsets:
            errtxt = ("Sorry, this BUFR message has only "+str(nsubsets)+
                      " subsets, so requesting subset "+
                      str(j)+" is not possible (remember the arrays are "+
                      "counted starting with 0)")
            raise EcmwfBufrLibError(errtxt)
        
        selection = self.actual_kelem*(j-1) + i
        value = self.values[selection]

        if autoget_cval:
            descr = self.ktdexp[i]
            try:
                unit = self.bt.table_b[descr].unit
                if unit == 'CCITTIA5':
                    cvals_index = int(value/1000)-1
                    text = ''.join(c for c in self.cvals[cvals_index,:])
                    return text.strip()
            except:
                # this may happen for ModificationCommand descriptors
                # like 224000, since these have no unit attribute
                pass

        if self.expand_flags:
            values = self.convert_flag_values_to_text([value,], i)
            value = values[0]

        return value
        #  #]
    def get_values(self, i, autoget_cval=False):
        #  #[ get the i th value from each subset as an array
        """
        a helper function to request the i th value from each subset
        for the current BUFR message as an array.
        """
        if (not self.data_decoded):
            errtxt = ("Sorry, retrieving values is only possible after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_data")
            raise EcmwfBufrLibError(errtxt)

        nsubsets  = self.get_num_subsets()
        nelements = self.get_num_elements()
        if i > nelements-1:
            errtxt = ("Sorry, this BUFR message has only "+str(nelements)+
                      " elements per subset, so requesting index "+
                      str(i)+" is not possible (remember the arrays are "+
                      "counted starting with 0)")
            raise EcmwfBufrLibError(errtxt)

        if self.delayed_repl_present and not self.delayed_repl_problem_reported:
            print('WARNING: the current template uses delayed replication! ')
            print('Therefore the actual expanded descriptor list may be')
            print('different for each subset within this BUFR message!')
            print('and retrieving an array of data values spanning multiple')
            print('subsets will not be possible.')
            exp_descr_list, delayed_repl_present = \
                   self.bt.expand_descriptor_list(self.py_unexp_descr_list)
            print('exp_descr_list = ',exp_descr_list)
            self.delayed_repl_problem_reported = True
            
        selection = self.actual_kelem*np.array(range(nsubsets))+i
        values = self.values[selection]

        if autoget_cval:
            cvalues = []
            exp_descr_list_length = self.ktdexl
            template_offset = selection % exp_descr_list_length
            descr = self.ktdexp[template_offset]
            unit = self.bt.table_b[descr[0]].unit
            if unit == 'CCITT IA5':
                for subset in range(nsubsets):
                    cvals_index = int(values[subset]/1000)-1
                    text = ''.join(c for c in self.cvals[cvals_index,:])
                    cvalues.append(text.strip())
                return cvalues

        if self.expand_flags:
            values = self.convert_flag_values_to_text(values, i)
            
        # print('i, self.values[selection] = '+str(i)+' '+str(values))
        return values
        #  #]
    def get_subset_values(self, subset_nr, autoget_cval=False):
        #  #[ get the values for a given subset as an array
        """
        a helper function to request the values of the i th subset
        for the current BUFR message as an array
        Note that subsets start counting at 1!
        """
        if (not self.data_decoded):
            errtxt = ("Sorry, retrieving values is only possible after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_data")
            raise EcmwfBufrLibError(errtxt)

        nsubsets  = self.get_num_subsets()
        #nelements = self.get_num_elements()
        if subset_nr > nsubsets:
            errtxt = ("Sorry, this BUFR message has only "+str(nsubsets)+
                      " subsets, so requesting subset "+
                      str(subset_nr)+" is not possible "+
                      "(remember the subsets are "+
                      "counted starting with 1)")
            raise EcmwfBufrLibError(errtxt)

        selection = (self.actual_kelem*(subset_nr-1) +
                     np.array(range(self.ktdexl)))
        # it seems possible to have bufr messages without any
        # descriptors, so make sure we return an empty list in this case.
        if len(selection)>0:
            values = self.values[selection]
        else:
            values = np.array([])
            return
        
        if autoget_cval:
            # convert numpy values array to standard list to make it mutable
            values = list(values)
            for i, descr in enumerate(self.ktdexp):
                try:
                    unit = self.bt.table_b[descr].unit
                    if unit == 'CCITTIA5':
                        selection = self.actual_kelem*(subset_nr-1) + i
                        cvals_index = int(values[selection]/1000)-1
                        text = ''.join(c for c in self.cvals[cvals_index,:])
                        cvalue = text.strip()
                        values[i] = cvalue
                except:
                    # this may happend for ModificationCommand descriptors
                    # like 224000, since these have no unit attribute
                    pass
                
        if self.expand_flags:
            values = [self.convert_flag_values_to_text([value,], i)[0]
                      for i, value in enumerate(values)]

        # print('i, self.values[selection] = '+str(i)+' '+str(values))
        return values
        #  #]
    def get_element_name_and_unit(self, i):
        #  #[ routine to get name and unit of a given element
        """
        a helper routine to request the element name and unit
        for the given index in the expanded descriptor list of the
        current BUFR message
        """
        if (not self.data_decoded):
            errtxt = ("Sorry, names and units are only available after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_data")
            raise EcmwfBufrLibError(errtxt)

        nelements = self.get_num_elements()
        if i > nelements-1:
            errtxt = ("Sorry, this BUFR message has only "+str(nelements)+
                      " elements per subset, so requesting name and unit for "+
                      "index "+str(i)+" is not possible "+
                      "(remember the arrays are counted starting with 0)")
            raise EcmwfBufrLibError(errtxt)

        if python3:
            txtn = ''.join(c.decode() for c in self.cnames[i])
            txtu = ''.join(c.decode() for c in self.cunits[i])
        else:
            txtn = ''.join(c for c in self.cnames[i])
            txtu = ''.join(c for c in self.cunits[i])
            
        return (txtn.strip(), txtu.strip())
        #  #]
    def delayed_repl_check_for_incorrect_use(self):
        #  #[ check routine for delayed replication usage
        '''
        a method to be used by methods  that assume no delayed replication
        is present (typically methods that return 1D/2D arrays of data)
        '''
        if self.delayed_repl_present:
            errtxt =  ('ERROR: the current template uses delayed replication! '
                       'Therefore the actual expanded descriptor list may be '
                       'different for each subset within this BUFR message! '
                       'and retrieving an array of data values spanning '
                       'multiple subsets may yield unintended results ! '
                       'Please loop over the subsets in your own script using '
                       'the get_subset_values or get_value methods of the '
                       'pybufr_ecmwf.bufr.BUFRReader or '
                       'pybufr_ecmwf.bufr_interface_ecmwf.BUFRInterfaceECMWF '
                       'classes to retrieve the data for this type of '
                       'messages.')
            raise IncorrectUsageError(errtxt)
        #  #]
    def extract_raw_descriptor_list(self):
        #  #[ extract the raw descriptor list from the binary bufr msg
        """
        Extract the raw descriptor list from the binary BUFR message,
        without having to decode the whole BUFR message. This is needed
        to estimate the needed array sizes before decoding the actual
        BUFR message.
        Extracting only the descriptor list seems not possible with
        the routines provided by the ECMWF BUFR library, therefore
        this is implemented in python here.
        """

        # print("extracting raw descriptor list:")
        
        # method to implement
        # use get_expected_msg_size from raw_bufr_file.py
        # to get all relevant section start pointers
        # and use this to start extracting this data.

        # available meta data:
        # self.section_sizes
        # self.section_start_locations
        # available data:
        # self.encoded_message

        # assume little endian for now when converting
        # raw bytes/characters to integers and vice-versa
        dataformat = "<i"
        size_words = len(self.encoded_message)
        size_bytes = size_words*4

        list_of_raw_data_bytes = []
        for (i, word) in enumerate(self.encoded_message):
            list_of_raw_data_bytes.append(struct.pack(dataformat, word))
        raw_data_bytes = b''.join(rdb for rdb in list_of_raw_data_bytes)

        # note: the headers seem to use big-endian encoding
        # even on little endian machines, for the msg size.
        dataformat = ">1i"
        
        start_section3 = self.section_start_locations[3]
        # print('start_section3 = ',start_section3)
        # extract the number of subsets from bytes 5 and 6
        raw_bytes = b'\x00'*2+raw_data_bytes[start_section3+5-1:
                                             start_section3+6]
        self.py_num_subsets = struct.unpack(dataformat, raw_bytes)[0]
        # print('self.py_num_subsets = ',self.py_num_subsets)

        # print('length section3: ', self.section_sizes[3])
        num_descriptors = int(0.5*(self.section_sizes[3]-7))
        # print('num descriptors: ',num_descriptors)

        # do the actual extraction of the raw/unexpanded descriptors
        self.py_unexp_descr_list = []
        for i in range(num_descriptors):
            # extract the unexpanded descriptors
            raw_bytes = raw_data_bytes[start_section3+8-1+i*2:
                                       start_section3+8+1+i*2]
            #print('raw_bytes = '+'.'.join(str(ord(b)) for b in raw_bytes))
            f = (ord(raw_bytes[0:1]) & (128+64))//64
            x = ord(raw_bytes[0:1]) & (64-1)
            y = ord(raw_bytes[1:2])
            #print('extracted descriptor: f,x,y = %1.1i.%2.2i.%3.3i' % (f,x,y))
            self.py_unexp_descr_list.append('%1.1i%2.2i%3.3i' % (f,x,y))

        # print('self.py_unexp_descr_list = ',self.py_unexp_descr_list)
        # print('with length = ',len(self.py_unexp_descr_list))
        #  #]
    def expand_raw_descriptor_list(self):
        #  #[ python implementation of the expansion
        '''
        a method to recursively replace D table entries with corresponding
        lists of B table entries. It does not take subsets into account
        and may not work correct in case delayed replication is present.
        '''
        if self.bt is None:
            errtxt = ("ERROR in expand_raw_descriptor_list: " + 
                      "you need to setup BUFR tables before " +
                      "expanding raw descriptor lists is possible.")
            raise EcmwfBufrLibError(errtxt)
            
        exp_descr_list, delayed_repl_present = \
                        self.bt.expand_descriptor_list(self.py_unexp_descr_list)

        if delayed_repl_present:
            self.py_expanded_descr_list = []
            self.delayed_repl_present = True
        else:
            self.py_expanded_descr_list = exp_descr_list
            self.delayed_repl_present = False
            
        #for descr in 
        #    if descr[0]=='3':
        #        # print('expanding: ',descr)
        #        tmp_list = bt.table_d[int(descr)].expand()
        #        for int_descr in tmp_list:
        #            str_descr = '%6.6i' % int_descr
        #            self.py_expanded_descr_list.append(str_descr)
        #    else:
        #        # print('keeping: ',descr)
        #        self.py_expanded_descr_list.append(descr)

        # print('result:')
        # print('self.delayed_repl_present = ', self.delayed_repl_present)
        # print('self.py_expanded_descr_list: ',self.py_expanded_descr_list)
        # print('with length: ',len(self.py_expanded_descr_list))
        #  #]
    def derive_delayed_repl_factors(self):
        #  #[ extract these factors from the self.ktdexp array
        select = np.where(self.ktdexp != 0)
        ktdexp = list(self.ktdexp[select])
        ndr = ktdexp.count(Delayed_Descr_Repl_Factor)

        select = np.where(self.ktdexp in
                          [Short_Delayed_Descr_Repl_Factor,
                           Delayed_Descr_Repl_Factor,
                           Extended_Delayed_Descr_Repl_Factor,
                           Delayed_Descr_and_Data_Rep_Factor,
                           Ext_Delayed_Descr_and_Data_Rep_Factor])
        delayed_repl_data = self.values[select]
        # print('delayed_repl_data = ', delayed_repl_data)
        return delayed_repl_data
        #  #]
    def fill_descriptor_list(self, nr_of_expanded_descriptors=None):
        #  #[ fills both the normal and expanded descriptor lists
        """
        fill the normal and expanded descriptor lists (defines the
        names and units, which is needed only in case you wish to request
        and or print these).
        This one seems not to take subset into account and may not
        give correct output for delayed replication templates.
        """
        if ( (not self.data_decoded) and
             (not self.sections012_decoded)):
            errtxt = ("Sorry, filling descriptor lists of a BUFR message "+
                      "is only possible after a BUFR message has been decoded "+
                      "with a call to decode_data or decode_sections_012")
            raise EcmwfBufrLibError(errtxt)

        # busel: fill the descriptor list arrays (only needed for printing)   
    
        # warning: this routine has no inputs, and acts on data stored
        #          during previous library calls
        # Therefore it only produces correct results when either bus012
        # or bufrex have been called previously on the same bufr message.....

        actual_nr_of_descriptors = len(self.py_unexp_descr_list)
        if nr_of_expanded_descriptors:
            actual_nr_of_expanded_descriptors = nr_of_expanded_descriptors
        else:
            actual_nr_of_expanded_descriptors = len(self.py_expanded_descr_list)

        # arrays to hold the descriptors
        self.ktdlen = 0 # will hold nr of descriptors
        self.ktdlst = np.zeros(actual_nr_of_descriptors,
                               dtype = np.int)
        self.ktdexl = 0 # will hold nr of expanded descriptors
        self.ktdexp = np.zeros(actual_nr_of_expanded_descriptors,
                               dtype = np.int)
    
        kerr   = 0

        if self.verbose:
            print("calling: ecmwfbufr.busel():")
        self.store_fortran_stdout()
        ecmwfbufr.busel(self.ktdlen, # actual number of data descriptors
                        self.ktdlst, # list of data descriptors
                        self.ktdexl, # actual nr of expanded data descriptors
                        self.ktdexp, # list of expanded data descriptors
                        kerr)   # error  message
        lines = self.get_fortran_stdout()
        self.display_fortran_stdout(lines)
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr, 'busel'))

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
    def fill_descriptor_list_subset(self, subset):
        #  #[ fills both the normal and expanded descriptor lists
        """
        fill the normal and expanded descriptor lists (defines the
        names and units, which is needed only in case you wish to request
        and or print these) for a given subset.
        """

        if ( (not self.data_decoded) and
             (not self.sections012_decoded)):
            errtxt = ("Sorry, filling descriptor lists of a BUFR message "+
                      "is only possible after a BUFR message has been decoded "+
                      "with a call to decode_data or decode_sections_012")
            raise EcmwfBufrLibError(errtxt)

        # busels: fill the descriptor list arrays (only needed for printing)   
    
        # warning: this routine has no inputs, and acts on data stored
        #          during previous library calls
        # Therefore it only produces correct results when either bus012
        # or bufrex have been called previously on the same bufr message.....

        # kelem  = 500 #self.max_nr_expanded_descriptors
        kerr   = 0

        actual_nr_of_descriptors = len(self.py_unexp_descr_list)

        # define space for decoding text strings
        kelem  = self.actual_kelem
        self.cnames = np.zeros((kelem, 64), dtype = '|S1')
        self.cunits = np.zeros((kelem, 24), dtype = '|S1')

        # arrays to hold the descriptors
        self.ktdlen = 0 # will hold nr of descriptors
        self.ktdlst = np.zeros(actual_nr_of_descriptors,
                               dtype = np.int)
        self.ktdexl = 0 # will hold nr of expanded descriptors
        self.ktdexp = np.zeros(kelem,
                               dtype = np.int)
    
        if self.verbose:
            print("calling: ecmwfbufr.busel2():")
            # print("SUBSETNR = ",subset)
            # print('kelem = ', kelem)
            # print('self.ktdlen = ', self.ktdlen)
            # print('self.ktdlst = ', self.ktdlst)
            # print('self.ktdexl = ', self.ktdexl)
            # print('self.ktdexp.shape = ', self.ktdexp.shape)
            # print('self.cnames.shape = ', self.cnames.shape)
            # print('self.cunits.shape = ', self.cunits.shape)
            # print('kerr = ', kerr)
            # print('self.actual_kelem = ', self.actual_kelem)
            
        self.store_fortran_stdout()
        ecmwfbufr.busel2(subset,      # subset to be inspected
                         kelem,       # Max number of expected elements
                         # outputs:
                         self.ktdlen, # actual number of data descriptors
                         self.ktdlst, # list of data descriptors
                         self.ktdexl, # actual nr of expanded data descriptors
                         self.ktdexp, # list of expanded data descriptors
                         self.cnames, # descriptor names
                         self.cunits, # descriptor units
                         kerr)        # error code
        lines = self.get_fortran_stdout()
        self.display_fortran_stdout(lines)
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr, 'busel2'))

        # It is not clear to me why busel seems to correctly produce
        # the descriptor lists (both bare and expanded), but yet it does
        # not seem to fill the ktdlen and ktdexl values.
        # To fix this the next 4 lines have been added:
        
        selection1 = np.where(self.ktdlst > 0)
        self.ktdlst = self.ktdlst[selection1]
        self.ktdlen = len(self.ktdlst)
        
        selection2 = np.where(self.ktdexp > 0)
        self.ktdexp = self.ktdexp[selection2]
        self.ktdexl = len(self.ktdexp)
        self.ksup[4] = self.ktdexl
        
        self.descriptors_list_filled = True
        #  #]
    def get_descriptor_list(self):
        #  #[
        """
        request the raw descriptor list in numeric form
        """
        if (not self.descriptors_list_filled):
            errtxt = ("Sorry, retrieving the list of descriptors of a "+
                      "BUFR message is only possible after a BUFR message "+
                      "has been decoded with a call to decode_data or "+
                      "decode_sections_012, and subsequently the lists have "+
                      "been filled with a call to fill_descriptor_list")
            raise EcmwfBufrLibError(errtxt)

        return self.ktdlst[:self.ktdlen]
        #  #]
    def get_expanded_descriptor_list(self):
        #  #[
        """
        request the expanded descriptor list in numeric form
        """
        if (not self.descriptors_list_filled):
            errtxt = ("Sorry, retrieving the list of descriptors of a "+
                      "BUFR message is only possible after a BUFR message "+
                      "has been decoded with a call to decode_data or "+
                      "decode_sections_012, and subsequently the lists have "+
                      "been filled with a call to fill_descriptor_list")
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
            errtxt = ("Sorry, retrieving the list of descriptors of a "+
                      "BUFR message is only possible after a BUFR message "+
                      "has been decoded with a call to decode_data or "+
                      "decode_sections_012, and subsequently the lists have "+
                      "been filled with a call to fill_descriptor_list")
            raise EcmwfBufrLibError(errtxt)

        # Note: this next call will print self.max_nr_descriptors
        # descriptors and self.max_nr_expanded_descriptors
        # extended descriptors, one line for each, including
        # explanation.
        # They will also print zeros for all not used elements of
        # these ktdlst and ktdexp arrays

        self.store_fortran_stdout()
        ecmwfbufr.buprs3(self.ksec3,
                         self.ktdlst,
                         self.ktdexp,
                         self.cnames)
        lines = self.get_fortran_stdout()
        self.display_fortran_stdout(lines)
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

        # if needed,the update sequence number can be added to the
        # input parameters of this method

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
        self.ksec1[ 4-1] =   0               # update sequence number
        # usually 0, only updated if the same data is re-issued after
        # reprocessing or so to fix some bug/problem
        # The ECMWF bufr_user_guide_2008.pdf writes:
        #   Update sequence number (zero for original BUFR messages;
        #   incremented by one for updates)
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

        # edition 3 and before requires year-of-century
        # edition 4 and later requires 4 digit years here
        # (now you try to find this in the documentation ....)
        if bufr_edition<4:
            self.ksec1[ 9-1] = (year-2000) # Without offset year - 2000
        else:
            self.ksec1[ 9-1] = year
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
        # for edition 3 and below
        
        self.ksec1[16-1] = bufr_code_subcentre       # originating subcentre
        # (this determines the name of the BUFR table to be used)

        if bufr_edition<4:
            self.ksec1[17-1] = 0 # reserved
            self.ksec1[18-1] = 0 # reserved
        else:
            self.ksec1[17-1] = 0 # international sub-category
            self.ksec1[18-1] = second

        # items 19 and above are Local ADP centre information (byte by byte)

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
    def fill_delayed_repl_data(self, del_repl_max_nr_of_repeats_list):
        #  #[ define and fill the list of replication factors
        self.kdata = np.zeros(self.nr_subsets*
                              len(del_repl_max_nr_of_repeats_list),
                              dtype=np.int)
        #                      nr_of_delayed_repl_factors, dtype=np.int)
        i = 0
        for subset in range(self.nr_subsets):
            # Warning: just set the whole array to the maximum you wish to have.
            # Letting this number vary seems not to work with the current
            # ECMWF library. It will allways just look at the first element
            # in the kdata array. (or do I misunderstand the BUFR format here?)
            for max_repeats in del_repl_max_nr_of_repeats_list:
                self.kdata[i] = max_repeats
                i += 1
                
        # print("DEBUG: delayed replication factors: ", self.kdata)
        #  #]
    def register_and_expand_descriptors(self, BT):
        #  #[ estimate exp. descr. list size and needed bytes for encoding
        """
        expand the descriptor list, generating the expanded list
        from the raw list by calling buxdes, with some additional
        logic to make it easier to use delayed replication in your
        templates.
        WARNING: setting max_nr_expanded_descriptors to a too low value will
        cause very ugly runtime memory corruption (malloc) errors!
        Make sure you set this value to a large enough value for your template.
        Unfortunately I have no idea yet how to catch this error.
        If you have any idea please let me know ...
        """
        kerr   = 0

        # input: BT must be an instance of the BufrTemplate class
        # so check this:
        assert(isinstance(BT, BufrTemplate))
        
        # length of unexpanded descriptor list
        unexpanded_descriptor_list = BT.get_unexpanded_descriptor_list()
        self.ktdlen = len(unexpanded_descriptor_list)
        # convert the unexpanded descriptor list to a numpy array
        # print("DEBUG: ",[str(d) for d in unexpanded_descriptor_list])

        self.ktdlst = np.array(unexpanded_descriptor_list, dtype=np.int)
        print("unexpanded nr of descriptors = ", self.ktdlen)
        print("The current list is: ", self.ktdlst)

        # ensure all descriptors mentioned in the template exist in the
        # choosen BUFR tables
        for descr in self.ktdlst:
            if not self.bt.is_defined(descr):
                errtxt = ('you tried to use a descriptor in your template '+
                          'that is not available in the current ' +
                          'BUFR tables: '+str(descr)
                          )
                raise EcmwfBufrLibError(errtxt)
        
        self.max_nr_expanded_descriptors = \
                BT.get_max_nr_expanded_descriptors(self.bt)

        #sys.exit(1)

        # define a list to store the expanded descriptor list
        self.ktdexp = np.zeros(self.max_nr_expanded_descriptors, dtype = np.int)

        # define space for decoding text strings
        kelem  = self.max_nr_expanded_descriptors
        self.cnames = np.zeros((kelem, 64), dtype = '|S1')
        self.cunits = np.zeros((kelem, 24), dtype = '|S1')

        # call BUXDES
        # buxdes: expand the descriptor list
        #         and fill the array ktdexp and the variable ktdexp
        #         [only needed when creating a bufr msg with table D entries
        #          but I'll run ot anyway for now since this usually is
        #          a cheap operation, so a user should not be bothered by it]
        
        iprint = 0 # default is to be silent
        # iprint = 1
        if (iprint == 1):
            print("------------------------")
            print(" printing BUFR template ")
            print("------------------------")

        # define and fill the list of replication factors
        self.fill_delayed_repl_data(BT.del_repl_max_nr_of_repeats_list)

        # print('DEBUG: self.ksec1 ',self.ksec1)
        # print('DEBUG: self.ktdlst ',self.ktdlst)
        # print('DEBUG: self.kdata = ',self.kdata)

        # print('DEBUG: self.ktdexl = ',self.ktdexl)
        # print('DEBUG: self.ktdexp = ',self.ktdexp)
        # print('DEBUG: self.ktdexp.shape = ',self.ktdexp.shape)
        # print('DEBUG: self.cnames = ',self.cnames.shape)
        # print('DEBUG: self.cunits = ',self.cunits.shape)
        
        self.store_fortran_stdout()
        ecmwfbufr.buxdes(iprint,      # input
                         self.ksec1,  # input
                         self.ktdlst, # input
                         self.kdata,  # input
                         self.ktdexl, # output
                         self.ktdexp, # output
                         self.cnames, # output
                         self.cunits, # output
                         kerr)        # output
        lines = self.get_fortran_stdout()
        self.display_fortran_stdout(lines)
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr, 'buxdes'))

        print("ktdlst = ", self.ktdlst)
        selection = np.where(self.ktdexp > 0)

        # note: this seems to be an empty list in case
        #       delayed replication is used!
        print("ktdexp = ", self.ktdexp[selection])
        #print("ktdexl = ", self.ktdexl) # this one seems not to be filled ...?

        # It is not clear to me why buxdes seems to correctly produce
        # the expanded descriptor list, but yet it does
        # not seem to fill the ktdexl value.
        # To fix this the next line has been added:
        self.ktdexl = len(selection[0])

        # estimate number of bits and bytes needed for the encoded message
        num_bits = 0
        norm_ktdexp = self.bt.normalise_descriptor_list(self.ktdexp[selection])
        for d in norm_ktdexp:
            num_bits += d.get_num_bits()
        data_bytes = int(num_bits/8)+1
        descriptor_bytes = self.ktdlen # just guessing here
        # add sizes of header sections (in bytes)
        size_sec0 = 8 # bufr editions 0 and 1 had 4 bytes here
        size_sec1 = 17 # or ...
        size_sec2 = 0 # optional section, not used by this python module
        size_sec3 = 7+descriptor_bytes # template definition
        size_sec4 = 4+data_bytes
        size_sec5 = 4
        num_bytes = size_sec0+size_sec1+size_sec2+size_sec3+size_sec4+size_sec5
        # add extra bytes to compensate for extra header bytes
        # and estimation errors in descriptor_bytes and data_bytes
        num_bytes += 15000

        # NOTE: this triggers a segmentation fault during encoding
        # I have no idea how to reliably catch this.
        # num_bytes += -10
        
        # print('num_bits = ',num_bits)
        # print('num_bytes = ',num_bytes)

        self.estimated_num_bytes_for_encoding = num_bytes
        # print('self.estimated_num_bytes_for_encoding = ',
        #       self.estimated_num_bytes_for_encoding)

        # these are filled as well after the call to buxdes
        # print("cnames = ", self.cnames)
        # print("cunits = ", self.cunits)

        self.bufr_template_registered = True
        self.BufrTemplate = BT
        #  #]        
    def expand_descriptors_for_decoding(self, subset):
        #  #[ expand descriptor list for a given subset
        """
        expand the descriptor list, generating the expanded list
        from the raw list by calling buxdes. The output may differ
        for each subset in case the bufr message uses delayed replication.
        
        WARNING: setting max_nr_expanded_descriptors to a too low value will
        cause very ugly runtime memory corruption (malloc) errors!
        Make sure you set this value to a large enough value for your template.
        Unfortunately I have no idea yet how to catch this error.
        If you have any idea please let me know ...
        """

        if (not self.sections0123_decoded):
            # note: for delayed replication we even need to do the decoding
            # first, otherwise the kdata array is not available
            errtxt = ("Sorry, to expand the descriptor list sections 0,1,2,3 "
                      "of a BUFR message must be available." +
                      "This is only the case after a BUFR message has been " +
                      "partially decoded with a call to decode_sections_0123")
            raise EcmwfBufrLibError(errtxt)
        
        kerr   = 0

        # define and fill the list of replication factors (kdata)
        # assume this one is already filled by the decode_data method
        # self.fill_delayed_repl_data(BT.del_repl_max_nr_of_repeats_list)
        if self.delayed_repl_present:
            self.fill_descriptor_list_subset(subset)
        else:
            # arrays to hold the descriptors
            actual_nr_of_descriptors = len(self.py_unexp_descr_list)
            
            # self.ktdlen = 0 # will hold nr of descriptors
            # self.ktdlst = np.zeros(actual_nr_of_descriptors,
            #                        dtype = np.int)
            # self.ktdexl = 0 # will hold nr of expanded descriptors
            # self.ktdexp = np.zeros(actual_nr_of_expanded_descriptors,
            #                        dtype = np.int)
            
            self.ktdexp = np.zeros(self.max_nr_expanded_descriptors,
                                   dtype = np.int)
            
            # define space for decoding text strings
            kelem  = self.max_nr_expanded_descriptors
            self.cnames = np.zeros((kelem, 64), dtype = '|S1')
            self.cunits = np.zeros((kelem, 24), dtype = '|S1')

            # call BUXDES
            # buxdes: expand the descriptor list
            #         and fill the array ktdexp and the variable ktdexl
            
            iprint = 0 # default is to be silent
            # iprint = 1
            if (iprint == 1):
                print("------------------------")
                print(" printing BUFR template ")
                print("------------------------")

            # print('DEBUG: self.ksec1 ',self.ksec1)
            # print('DEBUG: self.kdata = ',self.kdata)
            
            # print('DEBUG: self.ktdexl = ',self.ktdexl)
            # print('DEBUG: self.ktdexp = ',self.ktdexp)
            # print('DEBUG: self.ktdexp.shape = ',self.ktdexp.shape)
            # print('DEBUG: self.cnames = ',self.cnames.shape)
            # print('DEBUG: self.cunits = ',self.cunits.shape)
            
            self.store_fortran_stdout()
            ecmwfbufr.buxdes(iprint,      # input
                             self.ksec1,  # input
                             self.ktdlst, # input
                             self.kdata,  # input
                             self.ktdexl, # output
                             self.ktdexp, # output
                             self.cnames, # output
                             self.cunits, # output
                             kerr)        # output
            lines = self.get_fortran_stdout()
            self.display_fortran_stdout(lines)
            if (kerr != 0):
                raise EcmwfBufrLibError(self.explain_error(kerr, 'buxdes'))

            #print("DEBUG expand_descriptors_for_decoding: ",
            #      "ktdlst = ", self.ktdlst)
            
            selection = np.where(self.ktdexp > 0)
            
            # note: this seems to be an empty list in case
            #       delayed replication is used!
            #print("DEBUG expand_descriptors_for_decoding: ",
            #      "ktdexp = ", self.ktdexp[selection])
            # this one seems not to be filled ...?
            # print("ktdexl = ", self.ktdexl)
        
            # It is not clear to me why buxdes seems to correctly produce
            # the expanded descriptor list, but yet it does
            # not seem to fill the ktdexl value.
            # To fix this the next line has been added:
            self.ktdexl = len(selection[0])


        #  #]        
    def encode_data(self, values, cvals):
        #  #[ call bufren to encode a bufr message
        """
        encode all header sections and the data section to construct
        the BUFR message in binary/compressed form
        """
        kerr   = 0

        if (not self.sections012_decoded):
            errtxt = ("Sorry, in order to allow automatic allocation of the "+
                      "values and cvals arrays the number of subsets is "+
                      "needed. Therefore the fill_sections0123 "+
                      "subroutine needs to be called "+
                      "before entering the encode_data subroutine.")
            raise EcmwfBufrLibError(errtxt)

        # calculate the needed size of the values and cvals arrays
        actual_nr_of_subsets = self.get_num_subsets()
        self.kvals = self.max_nr_expanded_descriptors*actual_nr_of_subsets

        # copy incoming data into instance namespace
        self.values = values
        self.cvals  = cvals

        #cval_strings = np.zeros(self.kvals, dtype = '|S64')
        #for i in range(self.kvals):
        #    cval_strings[i] = ''.join(c for c in cvals[i,:])

        # define the output buffer
        num_bytes = self.estimated_num_bytes_for_encoding
        # num_bytes = 15000
        num_words = num_bytes//4
        words = np.zeros(int(num_words), dtype=np.int)

        # call BUFREN
        self.store_fortran_stdout()
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
#                         cval_strings,  # input: strings to encode
                         words, # output: the encoded message
                         kerr)  # output: an error flag
        lines = self.get_fortran_stdout()
        self.display_fortran_stdout(lines)
        if self.verbose:
            print("bufren call finished")
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr, 'bufren'))

        #for i in range(len(values)):
        #    print('i,cvals[i] = '+str(i)+' "'+
        #          (''.join(c for c in cvals[i,:])).strip()+'"')
        #          

        if self.verbose:
            print("words = ")
            print(words)

        nonzero_locations = np.where(words!=0)
        #print('nonzero_locations = ',nonzero_locations[0])
        nw = nonzero_locations[0][-1] + 1
        if self.verbose:
            print("encoded size: ", nw, " words or ", nw*4, " bytes")

        self.encoded_message = words[:nw]
        
        self.data_encoded = True
        #  #]
    def verify_in_range(self, i, v):
        #  #[ verify value to be packed
        """
        check whether the value to be packed into the BUFR message
        fits in the range defined by the template, and give a proper
        warning and exit if it does not.
        """
        exp_descr_list_length = self.ktdexl
        template_offset = i % exp_descr_list_length
        descr = self.ktdexp[template_offset]
        minval, maxval, step = self.bt.table_b[descr].get_min_max_step()
        name = self.bt.table_b[descr].name
        if (v<minval) or (v>maxval):
            txt = ('ERROR: value to be packed it out of range! '+
                   'descriptor: %s (name: %s) min/max: %s %s value: %s' %
                   (str(descr), str(name), str(minval), str(maxval), str(v)))
            raise EcmwfBufrTableError(txt)

        #  #]
    def get_header_info(self):
        #  #[ get all header info in a dictionary
        if (not self.data_decoded):
            errtxt = ("Sorry, retrieving header info is only possible after "+
                      "a BUFR message has been decoded with a call to "+
                      "decode_data")
            raise EcmwfBufrLibError(errtxt)

        bufr_edition = self.ksec0[3-1]

        if bufr_edition < 2:
            # older edition 0 and 1 dont have bufr msg size in sec0
            defs_ksec0 = ['Length of section 0 in bytes',          # 1
                          'Bufr Edition number']                   # 2
        else:
            defs_ksec0 = ['Length of section 0 in bytes',          # 1
                          'Total length of Bufr message in bytes', # 2
                          'Bufr Edition number']                   # 3
        
        defs_ksec1 = ['Length of section 1 in bytes',       # 1
                      'Bufr Edition number',                # 2
                      'Originating centre',                 # 3
                      'Update sequence number',             # 4
                      'Flag (presence of Section 2 in the message)', # 5
                      'Bufr message type (Bufr Table A)',   # 6 or DataCategory
                      'Bufr message subtype (local use)',   # 7
                      'Version number of local table used', # 8
                      'Year',   #  9 includes century for bufr_edition > 3
                      'Month',  # 10
                      'Day',    # 11
                      'Hour',   # 12
                      'Minute', # 13
                      'Bufr Master Table used',              # 14
                      ]
        if bufr_edition > 1:
            defs_ksec1.extend([
                      'Version number of Master table used', # 15
                      ])
        if bufr_edition == 3:
            defs_ksec1.extend([
                      'Originating sub-centre',              # 16
                      'Reserved',                            # 17
                      ])
                      # items 18 and onward are Local ADP centre
                      # information (byte by byte) and can not be interpreted
                      # in a generic way

        if bufr_edition > 3:
            defs_ksec1.extend([
                      'Originating sub-centre',              # 16
                      'International sub-category',          # 17
                      'Second', # 18
                      # metadata items, commented out in ECMWF source code
                      # so they are not available for the moment
                      #'year',   # 19
                      #'month',  # 20
                      #'day',    # 21
                      #'hour',   # 22
                      #'minute', # 23
                      #'Second', # 24
                      #'year',   # 25
                      #'month',  # 26
                      #'day',    # 27
                      #'hour',   # 28
                      #'minute', # 29
                      #'Second', # 30
                      #'most southern latitude (-90 to 90)', # 31
                      #'most western longitude (0-360)', # 32
                      #'most northern latitude (-90 to 90)', # 33
                      #'most eastern longitude (0-360)', # 34
                      ])
                      # items 35 and onward are Local ADP centre
                      # information (byte by byte) and can not be interpreted
                      # in a generic way
        
        defs_ksec2 = ['Length of Section 2 in bytes',        # 1
                      'Report Data Base key in packed form', # 2-
                      ]
                      
        defs_ksec3 = ['Length of Section 3 in bytes',  # 1
                      'Reserved',                      # 2
                      'Number of subsets',             # 3
                      'Flag (data type, compression)', # 4
                      ]
        
        defs_ksec4 = ['Length of Section 4 in bytes', # 1
                      'Reserved',                     # 2-
                      ]
                      
        defs_ksup = ['Dimension of KSEC1 array',               # 1
                     'Dimension of KSEC2 array',               # 2
                     'Dimension of KSEC3 array',               # 3
                     'Dimension of KSEC4 array',               # 4
                     'Real number of expanded elements',       # 5
                     'Number of subsets',                      # 6
                     'Real number of elements in CVALS array', # 7
                     'Total Bufr message length in bytes',     # 8
                     'Dimension of KSEC0 array',               # 9
                     ]

        #  convert kseco,1,2,3,4 and ksup to a dict
        hdr_info = {}

        for key_defs, sec_name, section in \
                [(defs_ksec0, 'ksec0', self.ksec0),
                 (defs_ksec1, 'ksec1', self.ksec1),
                 (defs_ksec2, 'ksec2', self.ksec2),
                 (defs_ksec3, 'ksec3', self.ksec3),
                 (defs_ksec4, 'ksec4', self.ksec4),
                 (defs_ksup, 'ksup', self.ksup),
                 ]:
            for i, key in enumerate(key_defs):
                if key is not 'Reserved':
                    hdr_info[sec_name+'.'+key] = section[i]
        
        #for i, key in enumerate(defs_ksec0):
        #    hdr_info['ksec0.'+key] = self.ksec0[i]

        #for i, key in enumerate(defs_ksec1):
        #    hdr_info['ksec1.'+key] = self.ksec1[i]

        #for i, key in enumerate(defs_ksec2):
        #    hdr_info['ksec2.'+key] = self.ksec2[i]

        #for i, key in enumerate(defs_ksec3):
        #    hdr_info['ksec3.'+key] = self.ksec3[i]

        #for i, key in enumerate(defs_ksec4):
        #    hdr_info['ksec4.'+key] = self.ksec4[i]

        #for i, key in enumerate(defs_ksup):
        #    hdr_info['ksup.'+key] = self.ksup[i]

        #self.key
        
        return hdr_info
        #  #]
#  #]
