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

class BUFRInterfaceECMWF:
    #  #[
    """
    a class of wrapper and helper functions to allow easier use of the
    raw ECMWF BUFR interface wrapper
    """
    size_ksup  =    9
    size_ksec0 =    3
    size_ksec1 =   40
    size_ksec2 = 4096
    size_key   = 52
    
    def __init__(self):
        self.ksup   = np.zeros(self.size_ksup,  dtype = np.int)
        self.ksec0  = np.zeros(self.size_ksec0, dtype = np.int)
        self.ksec1  = np.zeros(self.size_ksec1, dtype = np.int)
        self.ksec2  = np.zeros(self.size_ksec2, dtype = np.int)
        self.key    = np.zeros(self.size_key,   dtype = np.int)

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
    def decode_sections_012(self,words):
        #  #[ wrapper for bus012
        kerr   = 0
       
        print "calling: ecmwfbufr.bus012():"
        ecmwfbufr.bus012(words, self.ksup,
                         self.ksec0, self.ksec1, self.ksec2, kerr)
        if (kerr != 0):
            raise EcmwfBufrLibError(self.explain_error(kerr,'bus012'))
        #  #]
    def setup_tables(self,table_B_to_use=None,table_D_to_use=None):
        #  #[
        print 'inside setup_tables() ...'

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

        print 'ecmwf_bufr_tables_dir = ',ecmwf_bufr_tables_dir

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
        
        print '(expected_name_table_b, expected_name_table_d) = ',\
              (expected_name_table_b, expected_name_table_d)

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

        # define our own location for storing (symlinks to) the BUFR tables
        private_bufr_tables_dir = os.path.abspath("./tmp_BUFR_TABLES")
        if (not os.path.exists(private_bufr_tables_dir)):
            os.mkdir(private_bufr_tables_dir)

        destination_b = os.path.join(private_bufr_tables_dir,
                                     expected_name_table_b)
        destination_d = os.path.join(private_bufr_tables_dir,
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
            
        print 'Tables names expected by the library:'
        print destination_b
        print destination_d
        print 'Tables to be used:'
        print source_b
        print source_d
        
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
        env["BUFR_TABLES"] = private_bufr_tables_dir+os.path.sep
    
        #  #]
    def print_sections_012(self):
        print 'ksup = ', self.ksup
        print '------------------------------'
        
        print "printing content of section 0:"
        print "sec0 : ", self.ksec0
        ecmwfbufr.buprs0(self.ksec0)
        print '------------------------------'
        print "printing content of section 1:"
        print "sec1 : ", self.ksec1
        ecmwfbufr.buprs1(self.ksec1)

        sec2_len = self.ksec2[0]
        print '------------------------------'
        
        print "length of sec2: ", sec2_len
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
            print "sec2 : ", self.ksec2
            print "printing content of section 2:"
            ecmwfbufr.buprs2(self.ksup,
                             self.key)
        else:
            print 'skipping section 2 [since it seems unused]'
        
    # todo: pass these values as optional parameters to the decoder
    #       and check whether they pass the library maximum or not.
    #       (and choose sensible defaults if not provided)
    #max_nr_descriptors          =  20 # 300
    #max_nr_expanded_descriptors = 140 # 160000 # max is JELEM=320.000
    #max_nr_subsets              = 361 # 25


    def explain_error(kerr, subroutine_name):
        #  #[ explain error codes returned by the bufrlib routines
        # to be implemented, for now just print the raw code
        return 'libbufr subroutine '+subroutine_name+\
               ' reprted error code: kerr = '+str(kerr)
        #  #]
    #  #]
class RawBUFRFile:
    #  #[
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
            cmd = os.path.join(self.example_programs_dir,
                               "example_for_using_ecmwfbufr_for_decoding.py")
            success = call_cmd_and_verify_output(cmd)
            self.assertEqual(success, True)                
            #  #]
        def test_run_encoding_example(self):
            #  #[
            # run the provided example code and verify the output
            cmd = os.path.join(self.example_programs_dir,
                               "example_for_using_ecmwfbufr_for_encoding.py")
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
            cmd = os.path.join(self.example_programs_dir,
                               "example_for_using_pb_routines.py")
            success = call_cmd_and_verify_output(cmd)
            self.assertEqual(success, True)                
            #  #]
        #  #]

    class CheckBUFRInterfaceECMWF(unittest.TestCase):
        #  #[ 2 tests
        # note: tests MUST have a name starting with "test"
        #       otherwise the unittest module will not use them
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
            self.assertEqual(b, 'B0000000000210000001')
            self.assertEqual(d, 'D0000000000210000001')
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
    sys.exit(0)
    
    #  #[ handle BUFR tables [should this be part of the install step?]
    print '------------------------------'
    
    # define our own location for storing (symlinks to) the BUFR tables
    private_bufr_tables_dir = os.path.abspath("./tmp_BUFR_TABLES")
    if (not os.path.exists(private_bufr_tables_dir)):
        os.mkdir(private_bufr_tables_dir)
        
    # make the needed symlinks
    ecmwf_bufr_tables_dir = "ecmwf_bufrtables"
    ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
    needed_B_table    = "B0000000000210000001.TXT"
    needed_D_table    = "D0000000000210000001.TXT"
    available_B_table = "B0000000000098013001.TXT"
    available_D_table = "D0000000000098013001.TXT"
    
    # NOTE: the naming scheme used by ECMWF is such, that the table name can
    #       be derived from elements from sections 0 and 1, which can be
    #       decoded without loading bufr tables.
    # TODO: implement this
    
    source      = os.path.join(ecmwf_bufr_tables_dir,  available_B_table)
    destination = os.path.join(private_bufr_tables_dir, needed_B_table)
    if (not os.path.exists(destination)):
        os.symlink(source, destination)
        
    source      = os.path.join(ecmwf_bufr_tables_dir,  available_D_table)
    destination = os.path.join(private_bufr_tables_dir, needed_D_table)
    if (not os.path.exists(destination)):
        os.symlink(source, destination)
        
    # make sure the BUFR tables can be found
    # also, force a slash at the end, otherwise the library fails
    # to find the tables
    e = os.environ
    e["BUFR_TABLES"] = private_bufr_tables_dir+os.path.sep
    
    #  #]
    #  #[ handle BUFR tables [dito]
    
    # define our own location for storing (symlinks to) the BUFR tables
    private_bufr_tables_dir = os.path.abspath("./tmp_BUFR_TABLES")
    if (not os.path.exists(private_bufr_tables_dir)):
        os.mkdir(private_bufr_tables_dir)
        
    # make the needed symlinks
    ecmwf_bufr_tables_dir = "ecmwf_bufrtables"
    ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
    needed_B_table    = "B0000000000098015001.TXT"
    needed_D_table    = "D0000000000098015001.TXT"
    available_B_table = "B0000000000098013001.TXT"
    available_D_table = "D0000000000098013001.TXT"
    
    # NOTE: the naming scheme used by ECMWF is such, that the table name can
    #       be derived from elements from sections 0 and 1, which can be
    #       decoded without loading bufr tables.
    # TODO: implement this
    
    source      = os.path.join(ecmwf_bufr_tables_dir,  available_B_table)
    destination = os.path.join(private_bufr_tables_dir, needed_B_table)
    if (not os.path.exists(destination)):
        os.symlink(source, destination)
        
    source      = os.path.join(ecmwf_bufr_tables_dir,  available_D_table)
    destination = os.path.join(private_bufr_tables_dir, needed_D_table)
    if (not os.path.exists(destination)):
        os.symlink(source, destination)
        
    # make sure the BUFR tables can be found
    # also, force a slash at the end, otherwise the library fails
    # to find the tables
    e = os.environ
    e["BUFR_TABLES"] = private_bufr_tables_dir+os.path.sep
    
    #  #]

    # todo: turn all the testcode below either into unittests
    #       or into little example programs, or both ...
        
    #  #[ read the binary data using the RawBUFRFile class
    input_test_bufr_file = 'Testfile.BUFR'
    BF = RawBUFRFile()
    BF.open(input_test_bufr_file, 'r')
    words = BF.get_next_raw_bufr_msg()
    BF.close()
    #  #]

    #  #[ define the needed constants
    
    max_nr_descriptors          =  20 # 300
    max_nr_expanded_descriptors = 140 # 160000 # max is JELEM=320.000
    max_nr_subsets              = 361 # 25

    
    
    ktdlen = max_nr_descriptors
    # krdlen = max_nr_delayed_replication_factors
    kelem  = max_nr_expanded_descriptors
    kvals  = max_nr_expanded_descriptors*max_nr_subsets
    # jbufl  = max_bufr_msg_size
    # jsup   = length_ksup
    
    #  #]
    #  #[ call BUS012
    print '------------------------------'
    ksup   = np.zeros(         9, dtype = np.int)
    ksec0  = np.zeros(         3, dtype = np.int)
    ksec1  = np.zeros(        40, dtype = np.int)
    ksec2  = np.zeros(      4096, dtype = np.int)
    kerr   = 0
    
    print "calling: ecmwfbufr.bus012():"
    ecmwfbufr.bus012(words, ksup, ksec0, ksec1, ksec2, kerr)
    # optional parameters: kbufl)
    print "returned from: ecmwfbufr.bus012()"
    if (kerr != 0):
        print "kerr = ", kerr
        sys.exit(1)
    print 'ksup = ', ksup
    #  #]
    #  #[ call BUPRS0
    print '------------------------------'
    print "printing content of section 0:"
    print "sec0 : ", ksec0
    ecmwfbufr.buprs0(ksec0)
    #  #]
    #  #[ call BUPRS1
    print '------------------------------'
    print "printing content of section 1:"
    print "sec1 : ", ksec1
    ecmwfbufr.buprs1(ksec1)
    #  #]
    #  #[ call BUUKEY
    key = np.zeros(52, dtype = np.int)
    sec2_len = ksec2[0]
    if (sec2_len > 0):
        # buukey expands local ECMWF information from section 2
        # to the key array
        print '------------------------------'
        print "calling buukey"
        ecmwfbufr.buukey(ksec1, ksec2, key, ksup, kerr)
    #  #]
    #  #[ call BUPRS2
    print '------------------------------'
    print "length of sec2: ", sec2_len
    if (sec2_len > 0):
        print "sec2 : ", ksec2
        print "printing content of section 2:"
        ecmwfbufr.buprs2(ksup, key)
    else:
        print 'skipping section 2 [since it seems unused]'
    #  #]
    #  #[ call BUFREX
    
    # WARNING: getting this to work is rather tricky
    # any wrong datatype in these definitions may lead to
    # the code entering an infinite loop ...
    # Note that the f2py interface only checks the lengths
    # of these arrays, not the datatype. It will accept
    # any type, as long as it is numeric for the non-string items
    # If you are lucky you will get a MemoryError when you make a mistake
    # but often this will not be the case, and the code just fails or
    # produces faulty results without apparant reason.
    
    # these 4 are filled by the BUS012 call above
    # ksup   = np.zeros(         9, dtype = np.int)
    # ksec0  = np.zeros(         3, dtype = np.int)
    # ksec1  = np.zeros(        40, dtype = np.int)
    # ksec2  = np.zeros(      4096, dtype = np.int)
    
    print '------------------------------'
    ksec3  = np.zeros(          4, dtype = np.int)
    ksec4  = np.zeros(          2, dtype = np.int)
    cnames = np.zeros((kelem, 64), dtype = np.character)
    cunits = np.zeros((kelem, 24), dtype = np.character)
    values = np.zeros(      kvals, dtype = np.float64) # this is the default
    cvals  = np.zeros((kvals, 80), dtype = np.character)
    kerr   = 0
    
    print "calling: ecmwfbufr.bufrex():"
    ecmwfbufr.bufrex(words, ksup, ksec0, ksec1, ksec2, ksec3, ksec4,
                     cnames, cunits, values, cvals, kerr)
    # optional parameters: sizewords, kelem, kvals)
    print "returned from: ecmwfbufr.bufrex()"
    if (kerr != 0):
        print "kerr = ", kerr
        sys.exit(1)
    #  #]
    #  #[ print a selection of the decoded numbers
    print '------------------------------'
    print "Decoded BUFR message:"
    print "ksup : ", ksup
    print "sec0 : ", ksec0
    print "sec1 : ", ksec1
    print "sec2 : ", ksec2
    print "sec3 : ", ksec3
    print "sec4 : ", ksec4
    print "cnames [cunits] : "
    for (i, cn) in enumerate(cnames):
        cu = cunits[i]
        txtn = ''.join(c for c in cn)
        txtu = ''.join(c for c in cu)
        if (txtn.strip() != ''):
            print '[%3.3i]:%s [%s]' % (i, txtn, txtu)
            
    print "values : ", values
    txt = ''.join(str(v)+';' for v in values[:20] if v>0.)
    print "values[:20] : ", txt
    
    nsubsets  = ksec3[2] # 361 # number of subsets in this BUFR message
    nelements = ksup[4] # 44 # size of one expanded subset
    lat = np.zeros(nsubsets)
    lon = np.zeros(nsubsets)
    for s in range(nsubsets):
        # index_lat = nelements*(s-1)+24
        # index_lon = nelements*(s-1)+25
        index_lat = max_nr_expanded_descriptors*(s-1)+24
        index_lon = max_nr_expanded_descriptors*(s-1)+25
        lat[s] = values[index_lat]
        lon[s] = values[index_lon]
        if (30*(s/30) == s):
            print "s = ", s, "lat = ", lat[s], " lon = ", lon[s]

    print "min/max lat", min(lat), max(lat)
    print "min/max lon", min(lon), max(lon)
    #  #]
    #  #[ call BUSEL
    print '------------------------------'
    # busel: fill the descriptor list arrays (only needed for printing)   
    
    # warning: this routine has no inputs, and acts on data stored
    #          during previous library calls
    # Therefore it only produces correct results when either bus0123
    # or bufrex have been called previously on the same bufr message.....
    # However, it is not clear to me why it seems to correctly produce
    # the descriptor lists (both bare and expanded), but yet it does
    # not seem to fill the ktdlen and ktdexl values.
    
    ktdlen = 0
    ktdlst = np.zeros(max_nr_descriptors, dtype = np.int)
    ktdexl = 0
    ktdexp = np.zeros(max_nr_expanded_descriptors, dtype = np.int)
    kerr   = 0
    
    print "calling: ecmwfbufr.busel():"
    ecmwfbufr.busel(ktdlen, # actual number of data descriptors
                    ktdlst, # list of data descriptors
                    ktdexl, # actual number of expanded data descriptors
                    ktdexp, # list of expanded data descriptors
                    kerr)   # error  message
    print "returned from: ecmwfbufr.busel()"
    if (kerr != 0):
        print "kerr = ", kerr
        sys.exit(1)
        
    print 'busel result:'
    print "ktdlen = ", ktdlen
    print "ktdexl = ", ktdexl
    
    selection1 = np.where(ktdlst > 0)
    #print 'selection1 = ', selection1[0]
    ktdlen = len(selection1[0])
    selection2 = np.where(ktdexp > 0)
    #print 'selection2 = ', selection2[0]
    ktdexl = len(selection2[0])
    
    print 'fixed lengths:'
    print "ktdlen = ", ktdlen
    print "ktdexl = ", ktdexl
    
    print 'descriptor lists:'
    print "ktdlst = ", ktdlst[:ktdlen]
    print "ktdexp = ", ktdexp[:ktdexl]
    
    #  #]
    #  #[ call BUPRS3
    print '------------------------------'
    print "printing content of section 3:"
    print "sec3 : ", ksec3
    ecmwfbufr.buprs3(ksec3,
                     ktdlst, # list of data descriptors
                     ktdexp, # list of expanded data descriptors
                     cnames) # descriptor names
    #  #]
    #  #[ reinitialise all arrays
    print '------------------------------'
    print 'reinitialising all arrays...'
    print '------------------------------'
    ksup   = np.zeros(          9, dtype = np.int)
    ksec0  = np.zeros(          3, dtype = np.int)
    ksec1  = np.zeros(         40, dtype = np.int)
    ksec2  = np.zeros(       4096, dtype = np.int)
    key    = np.zeros(         52, dtype = np.int)
    ksec3  = np.zeros(          4, dtype = np.int)
    ksec4  = np.zeros(          2, dtype = np.int)
    cnames = np.zeros((kelem, 64), dtype = np.character)
    cunits = np.zeros((kelem, 24), dtype = np.character)
    values = np.zeros(      kvals, dtype = np.float64) # this is the default
    cvals  = np.zeros((kvals, 80), dtype = np.character)
    ktdlen = 0
    ktdlst = np.zeros(max_nr_descriptors, dtype = np.int)
    ktdexl = 0
    ktdexp = np.zeros(max_nr_expanded_descriptors, dtype = np.int)
    kerr   = 0
    #  #]
    #  #[ fill sections 0, 1, 2 and 3
    
    bufr_edition              =   4
    bufr_code_centre          =  98 # ECMWF
    bufr_obstype              =   3 # sounding
    bufr_subtype_L1B          = 251 # L1B
    bufr_table_local_version  =   1
    bufr_table_master         =   0
    bufr_table_master_version =  15
    bufr_code_subcentre       =   0 # L2B processing facility
    bufr_compression_flag     =   0 #  64=compression/0=no compression
    
    (year, month, day, hour, minute, second,
     weekday, julianday, isdaylightsavingstime) = time.localtime()
    
    num_subsets = 4
    
    # fill section 0
    ksec0[1-1] = 0
    ksec0[2-1] = 0
    ksec0[3-1] = bufr_edition
    
    # fill section 1
    ksec1[ 1-1] =  22                       # length sec1 bytes
    #                                        [filled by the encoder]
    # however, a minimum of 22 is obliged here
    ksec1[ 2-1] = bufr_edition              # bufr edition
    ksec1[ 3-1] = bufr_code_centre          # originating centre
    ksec1[ 4-1] =   1                       # update sequence
    ksec1[ 5-1] =   0                       # (PRESENCE SECT 2)
    #                                        (0/128 = no/yes)
    ksec1[ 6-1] = bufr_obstype              # message type 
    ksec1[ 7-1] = bufr_subtype_L1B          # subtype
    ksec1[ 8-1] = bufr_table_local_version  # version of local table
    ksec1[ 9-1] = (year-2000)               # Without offset year - 2000
    ksec1[10-1] = month                     # month
    ksec1[11-1] = day                       # day
    ksec1[12-1] = hour                      # hour
    ksec1[13-1] = minute                    # minute
    ksec1[14-1] = bufr_table_master         # master table
    ksec1[15-1] = bufr_table_master_version # version of master table
    ksec1[16-1] = bufr_code_subcentre       # originating subcentre
    ksec1[17-1] =   0
    ksec1[18-1] =   0
    
    # a test for ksec2 is not yet defined
    
    # fill section 3
    ksec3[1-1] = 0
    ksec3[2-1] = 0
    ksec3[3-1] = num_subsets                # no of data subsets
    ksec3[4-1] = bufr_compression_flag      # compression flag
    
    #  #]
    #  #[ define a descriptor list
    
    ktdlen = 6 # length of unexpanded descriptor list
    ktdlst = np.zeros(ktdlen, dtype = np.int)
    
    # add descriptor 1
    dd_d_date_YYYYMMDD = 301011 # date
    # this defines the sequence:
    # 004001 ! year
    # 004002 ! month
    # 004003 ! day
    
    # add descriptor 2
    dd_d_time_HHMM = 301012 # time 
    # this defines the sequence:
    # 004004 ! hour 
    # 004005 ! minute 
    
    # add descriptor 3
    dd_pressure = int('007004', 10) # pressure [pa]  
    
    # WARNING: filling the descriptor variable with 007004 will fail
    # because python will interpret this as an octal value, and thus
    # automatically convert 007004 to the decimal value 3588
    
    # add descriptor 4
    dd_temperature = int('012001', 10) # [dry-bulb] temperature [K]  
    
    # add descriptor 5
    dd_latitude_high_accuracy = int('005001', 10)
    # latitude (high accuracy) [degree] 
    
    # add descriptor 6
    dd_longitude_high_accuracy = int('006001', 10)
    # longitude (high accuracy) [degree] 
    
    ktdlst[0] = dd_d_date_YYYYMMDD
    ktdlst[1] = dd_d_time_HHMM
    ktdlst[2] = dd_pressure
    ktdlst[3] = dd_temperature
    ktdlst[4] = dd_latitude_high_accuracy
    ktdlst[5] = dd_longitude_high_accuracy
    
    #  #]
    #  #[ call BUXDES
    # buxdes: expand the descriptor list
    #         and fill the array ktdexp and the variable ktdexp
    #         [only usefull when creating a bufr msg with table D entries
    
    #iprint = 0 # default is to be silent
    iprint = 1
    if (iprint == 1):
        print "------------------------"
        print " printing BUFR template "
        print "------------------------"
        
    kdata = np.zeros(1, dtype = np.int) # list of replication factors 
    ecmwfbufr.buxdes(iprint, ksec1, ktdlst, kdata,
                     ktdexl, ktdexp, cnames, cunits, kerr)
    print "ktdlst = ", ktdlst
    print "ktdexp = ", ktdexp
    print "ktdexl = ", ktdexl # this one seems not to be filled ...?
    if (kerr != 0):
        print "kerr = ", kerr
        sys.exit(1)
        
    #print "cnames = ", cnames
    #print "cunits = ", cunits

    # retrieve the length of the expanded descriptor list
    exp_descr_list_length = len(np.where(ktdexp>0)[0])
    print "exp_descr_list_length = ", exp_descr_list_length
    #  #]
    #  #[ fill the values array with some dummy varying data
    num_values = exp_descr_list_length*num_subsets
    values = np.zeros(num_values, dtype = np.float64) # this is the default
    
    for subset in range(num_subsets):
        # note that python starts counting with 0, unlike fortran,
        # so there is no need to take (subset-1)
        i = subset*exp_descr_list_length
        
        values[i]        = 1999 # year
        i = i+1; values[i] =   12 # month
        i = i+1; values[i] =   31 # day
        i = i+1; values[i] =   23 # hour
        i = i+1; values[i] =   59    -        subset # minute
        i = i+1; values[i] = 1013.e2 - 100.e2*subset # pressure [pa]
        i = i+1; values[i] = 273.15  -    10.*subset # temperature [K]
        i = i+1; values[i] = 51.82   +   0.05*subset # latitude
        i = i+1; values[i] =  5.25   +    0.1*subset # longitude
        
    #  #]
    #  #[ call BUFREN
    #   bufren: encode a bufr message
    
    sizewords = 200
    kbuff = np.zeros(num_values, dtype = np.int)
    cvals = np.zeros((num_values, 80), dtype = np.character)
    
    print "kvals = ", kvals
    print "cvals = ", cvals
    ecmwfbufr.bufren(ksec0, ksec1, ksec2, ksec3, ksec4,
                     ktdlst, kdata, exp_descr_list_length,
                     values, cvals, words, kerr)
    print "bufren call finished"
    if (kerr != 0):
        print "kerr = ", kerr
        sys.exit(1)
    #  #]
    
    # add test calls to:
    #   bupkey: pack ecmwf specific key into section 2
    # and possibly to:
    #   btable: tries to load a bufr-B table
    #    [usefull for testing the presence of a needed table]
    #   get_name_unit: get a name and unit string for a given descriptor
    #   buprq: sets some switches that control the bufr library
    #
    #  #]

