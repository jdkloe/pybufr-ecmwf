#!/usr/bin/env python

"""
This file defines the RawBUFRFile class, an alternative for
loading and writing the binary raw BUFR messages from and to file
(needed because I cannot get the interface to the pb routines defined
in the ECMWF BUFR library to work in a portable way)
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
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html
#
#  #]
#  #[ imported modules
from __future__ import (absolute_import, division,
                        print_function) #, unicode_literals)

import os          # operating system functions
import numpy as np # import numerical capabilities
import struct      # allow converting c datatypes and structs
#  #]

class RawBUFRFile:
    #  #[
    """
    a class to read and write the binary BUFR messages from and
    to file. Is is intended to replace the pbio routines from the ECMWF
    library which for some obscure reason cannot be interfaced
    easily to python using the f2py tool.
    """
    def __init__(self, verbose = False,
                 warn_about_bufr_size = True):
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
        self.warn_about_bufr_size = warn_about_bufr_size
        #  #]
    def print_properties(self, prefix = "BUFRFile"):
        #  #[
        """
        print the properties of the current RawBUFRFile instance
        """
        # this one causes trouble with the unittesting since it gives
        # different addresses each time, and is not so very interesting
        # to print, so leave it out for now
        #print(prefix+": bufr_fd  = ", self.bufr_fd)
        print(prefix+": filename = "+self.filename)
        print(prefix+": filemode = "+self.filemode)
        print(prefix+": filesize = "+str(self.filesize))
        if (self.data != None):
            print(prefix+": len(data) = "+str(len(self.data)))
        else:
            print(prefix+": data = "+str(self.data))
        print(prefix+": list_of_bufr_pointers = "+
              str(self.list_of_bufr_pointers))
        print(prefix+": nr_of_bufr_messages = "+
              str(self.nr_of_bufr_messages))
        #  #]
    def open(self, filename, mode, silent = False):
        #  #[
        """
        open a BUFR file to allow reading or writing raw BUFR messages
        """
        # note: the silent switch is only intended to suppress
        # warning and error messages during unit testing.
        # During normal use it should never be set to True.
        
        self.filename = filename
        self.filemode = mode
        
        # filename should include the path specification as well
        assert(mode in ['rb', 'wb', 'ab'])

        if (mode == 'rb'):
            if (os.path.exists(filename)):
                self.filesize = os.path.getsize(filename)
            else:
                if (not silent):
                    print("ERROR in BUFRFile.open():")
                    print("Opening file: ", self.filename, " with mode: ",
                          self.filemode, " failed")
                    print("This file was not found or is not accessible.")
                raise IOError
        elif (mode == 'wb'):
            self.filesize = 0
        elif (mode == 'ab'):
            # when appending it is allowed to have a non-existing
            # file, in which case one will be generated, so test for
            # this condition
            if (os.path.exists(filename)):
                # in this case, try to find out the amount of BUFR messages
                # already present in this file, by temporary opening
                # it in reading mode
                tmp_bf = RawBUFRFile()
                tmp_bf.open(filename, 'rb')
                #tmp_bf.print_properties(prefix = "tmp_bf (opened for reading)")
                count = tmp_bf.get_num_bufr_msgs()
                tmp_bf.close()
                del(tmp_bf)

                # then store the found number for later use
                self.nr_of_bufr_messages = count
                self.filesize = os.path.getsize(filename)

                if ((count == 0) and (self.filesize>0)):
                    print("WARNING: appending to non-zero file, but could")
                    print("not find any BUFR messages in it. Maybe you are")
                    print("appending to a non-BUFR file??")
            else:
                self.filesize = 0            

        try:
            self.bufr_fd = open(filename, mode)
        except:
            if (not silent):
                print("ERROR in BUFRFile.open():")
                print("Opening file: ", self.filename, " with mode: ",
                      self.filemode, " failed")
            raise IOError

        if (mode == 'rb'):
            try:
                self.data = self.bufr_fd.read()
            except:
                if (not silent):
                    print("ERROR in BUFRFile.open():")
                    print("Reading data from file: ", self.filename,
                          " with mode: ", self.filemode, " failed")
                raise IOError

            # split in separate BUFR messages
            self.split()

        #  #]
    def close(self):
        #  #[
        """
        close a BUFR file
        """
        # close the file
        self.bufr_fd.close()
        # then erase all settings
        self.__init__()
        #  #]
    def get_expected_msg_size(self, start_location):
        #  #[
        """ a routine to extract the expected message size from
        a BUFR message, needed to verify which start tag BUFR matches
        which end tag 7777. It also helps in excluding corrupted
        and falsely identified messages.
        """
        # According to ECMWF's BUFR User Guide:
        # http://www.ecmwf.int/products/data/software/bufr_user_guide.pdf
        # the first 8 bytes of a BUFR message should contain:
        # 1-4 : the four letters BUFR
        # 5-7 : total length of BUFR msg in bytes
        # 8   : BUFR Edition number (newest one currently is 4)
        #       valid edition numbers are 0,1,2,3,4
        # However, the oldest edition numbers 0 and 1 are exceptions
        # they do not have the full message lenght in section0, and in
        # fact only have a 4 byte section 0.
        # See the WMO BUFR Guide
        # http://www.wmo.int/pages/prog/www/WMOCodes/...
        #        Guides/BUFRCREX/Layer3-English-only.pdf
        # which is available from:
        # http://www.wmo.int/pages/prog/www/WMOCodes/...
        #        Guides/BUFRCREXPreface_en.html
        # Luckily the fourth byte of section 1 still gives the edition
        # number for these cases (although in later editions this byte
        # indicates the Bufr master Table version)
        # For these editions it is needed to retrieve the sections lenghts by
        # scanning each of the 6 sections and add them manually ...
        
        # Note: I hope to never see cray-blocked files again in my life
        # so this routine will not properly handle these ...
        # (these types of BUFR files do not conform to the BUFR
        #  standard anyway, so nobody should use them, but they might
        #  pop-up now and then from some old archive)
        # If you need to use this kind of files, write your own correction
        # routine to remove the 8 byte control-words inserted at every
        # 4096 bytes by this weird fileformat before trying to use them.

        # section nr               0 1 2 3 4 5
        section_sizes           = [0,0,0,0,0,0]
        section_start_locations = [0,0,0,0,0,0]

        # self.verbose = True
        if (self.verbose):
            print('getting size of BUFR message at start location: ',
                  start_location)
        try:
            raw_edition_number = self.data[start_location+8-1:start_location+8]
            edition_number = ord(raw_edition_number)
            if (self.verbose):
                print('edition_number = ', edition_number)
        except IndexError:
             # 0 signals this is not a valid BUFR msg, might be a false
             # start BUFR string, or a corrupted or truncated file
            return (0, section_sizes, section_start_locations)

        # note: the headers seem to use big-endian encoding
        # even on little endian machines, for the msg size.
        dataformat = ">1i"

        try:
            #  #[ retrieve size of section 0 and if possible the msg_size
            start_section0 = start_location
            if edition_number > 1:
                # get bytes 5 to 7 which should hold the total length of the
                # current BUFR message
                raw_bytes = b'\x00'+self.data[start_section0+5-1:
                                              start_section0+7]
                try:
                    msg_size = struct.unpack(dataformat, raw_bytes)[0]
                except:
                    # 0 signals this is not a valid BUFR msg, might be a false
                    # start BUFR string, or a corrupted or truncated file
                    return (0, section_sizes, section_start_locations)

                #if self.verbose:
                #    print('section 0, byte 5: ', ord(raw_bytes[1]))
                #    print('section 0, byte 6: ', ord(raw_bytes[2]))
                #    print('section 0, byte 7: ', ord(raw_bytes[3]))
            if edition_number <= 1:
                size_section0 = 4
                # i.e. only the 4 characters 'BUFR'
            else:
                size_section0 = 8
                # i.e. the 4 characters 'BUFR',
                # AND the BUFR msg size (3 bytes) and the BUFR edition nr.

            if (self.verbose):
                print('size_section0 = ', size_section0,
                      'start_section0 = ', start_section0,
                      '[', hex(start_section0), ']')
            #  #]
            #  #[ retrieve size of section 1
            offset = size_section0
            start_section1 = start_location + offset
            # get length of section 1 from bytes 1 to 3
            raw_bytes = b'\x00'+self.data[start_section1+1-1:
                                          start_section1+3]
            try:
                size_section1 = struct.unpack(dataformat, raw_bytes)[0]
            except:
                # 0 signals this is not a valid BUFR msg, might be a false
                # start BUFR string, or a corrupted or truncated file
                return (0, section_sizes, section_start_locations)

            if (self.verbose):
                print('size_section1 = ', size_section1,
                      ' start_section1 = ', start_section1,
                      '[', hex(start_section1), ']')
            #  #]
            #  #[ retrieve size of section 2
            
            # see if the optional section 2 is present or not
            # this is indicated by bit 1 of byte 10 of section 1
            # bit 1 is the most significant bit, and corresponds
            # to the byte having an integer value of 128

            # NOTE: the documentation is inconsistent on this flag...
            # The WMO document WMO_BUFR_Guide_Layer3-English-only.pdf
            # states in the table on page L3-8 (the 10th page in the pdf)
            # that byte 8 signals presence of section 2.
            # The ECMWF document bufr_user_guide.pdf states in the
            # table on page 7 that byte 10 signals the presence of section 2,
            # however, in the text below it states that byte 8 should be used!
            #
            # Looking at the actual fortran code in the ECMWF BUFR library
            # the situation seems more subtle, and depends on the
            # BUFR edition version used...
            # 
            # Edition      0 1 2 3 4       available in ksec0(3) and ksec1(2)
            # sec1 length  3 3 3 3 3 bytes copied to ksec1(1)
            # master table 1 1 1 1 1 bytes copied to ksec1(2) if edition<1
            #                              else it is copied to ksec1(14)
            # orig. table  2 2 2 2 4 bytes copied to ksec1(3) and ksec1(16) 
            # seq. number  1 1 1 1 1 bytes copied to ksec1(4)
            # sec2presence 1 1 1 1 1 bytes copied to ksec1(5)
            
            if edition_number < 4:
                byte_to_use = 8
            else:
                byte_to_use = 10

            sec2_presence_flag = \
                 ord(self.data[start_location+offset+byte_to_use-1:
                               start_location+offset+byte_to_use])
                               
            section2_present = False

            #if (sec2_presence_flag & 1):
            if (sec2_presence_flag > 0):
                section2_present = True
                
            # retrieve size of section 2
            offset = size_section0 + size_section1
            start_section2 = start_location + offset
            if section2_present:
                # get length of section 2 from bytes 1 to 3
                raw_bytes = b'\x00'+self.data[start_section2+1-1:
                                              start_section2+3]
                try:
                    size_section2 = struct.unpack(dataformat, raw_bytes)[0]
                except:
                    # 0 signals this is not a valid BUFR msg, might be a false
                    # start BUFR string, or a corrupted or truncated file
                    return (0, section_sizes, section_start_locations)
            else:
                size_section2 = 0

            if (self.verbose):
                print('size_section2 = ',size_section2,
                      ' start_section2 = ', start_section2,
                      '[', hex(start_section2), ']')
            #  #]
            #  #[ retrieve size of section 3
            offset = size_section0 + size_section1 + size_section2
            start_section3 = start_location + offset
            # get length of section 3 from bytes 1 to 3
            raw_bytes = b'\x00'+self.data[start_section3+1-1:
                                          start_section3+3]
            try:
                size_section3 = struct.unpack(dataformat, raw_bytes)[0]
            except:
                # 0 signals this is not a valid BUFR msg, might be a false
                # start BUFR string, or a corrupted or truncated file
                return (0, section_sizes, section_start_locations)

            if (self.verbose):
                print('size_section3 = ',size_section3,
                      ' start_section3 = ', start_section3,
                      '[', hex(start_section3), ']')
            #  #]
            #  #[ retrieve size of section 4
            offset = size_section0 + size_section1 + \
                     size_section2 + size_section3
            start_section4 = start_location + offset
            # get length of section 4 from bytes 1 to 3
            raw_bytes = b'\x00'+self.data[start_section4+1-1:
                                          start_section4+3]
            #if self.verbose:
            #    print('section 4, byte 1: ',
            #          ord(raw_bytes[1]), hex(ord(raw_bytes[1])))
            #    print('section 4, byte 2: ',
            #          ord(raw_bytes[2]), hex(ord(raw_bytes[1])))
            #    print('section 4, byte 3: ',
            #          ord(raw_bytes[3]), hex(ord(raw_bytes[1])))

            try:
                size_section4 = struct.unpack(dataformat, raw_bytes)[0]
            except:
                # 0 signals this is not a valid BUFR msg, might be a false
                # start BUFR string, or a corrupted or truncated file
                return (0, section_sizes, section_start_locations)

            if (self.verbose):
                print('size_section4 = ',size_section4,
                      ' start_section4 = ', start_section4,
                      '[', hex(start_section4), ']')
            #  #]
            #  #[ retrieve size of section 5
            offset = size_section0 + size_section1 + \
                     size_section2 + size_section3 + size_section4
            start_section5 = start_location + offset

            size_section5 = 4

            if (self.verbose):
                print('size_section5 = ',size_section5,
                      ' start_section5 = ', start_section5)
            #  #]
            calculated_msg_size = size_section0 + size_section1 + \
                                  size_section2 + size_section3 + \
                                  size_section4 + size_section5

            if edition_number <= 1:
                # for editions 0 and 1 the msg_size is not contained
                # in section 0, and still needs to be set:
                msg_size = calculated_msg_size
            else:
                # extra sanity check
                if msg_size != calculated_msg_size:
                    print('ERROR! msg_size from section0 does not match')
                    print('msg_size calculated from individual '+
                          'section lengths!')
                    print('msg_size from section0: ',msg_size)
                    print('calculated msg_size;    ',calculated_msg_size)
                    print('SKIPPING this message...')
                    return (0, section_sizes, section_start_locations)
                
        except IndexError:
            # 0 signals this is not a valid BUFR msg, might be a false
            # start BUFR string, or a corrupted or truncated file
            return (0, section_sizes, section_start_locations)
        
        section_sizes           = [size_section0, size_section1,
                                   size_section2, size_section3,
                                   size_section4, size_section5]
        # note: the start locations stored above are relative to
        # the beginning of the file, but for further use it is more
        # convenient to have them relative to the beginning
        # of the BUFR message, so subtract start_location  from them
        section_start_locations = [start_section0-start_location,
                                   start_section1-start_location,
                                   start_section2-start_location,
                                   start_section3-start_location,
                                   start_section4-start_location,
                                   start_section5-start_location]
        
        # see: p.L3-3 (p.5) of the file Layer3-English-only.pdf
        #      mentioned above.
        # 
        # this limit was raised from 15kb to 500kb on 7-Nov-2007
        # see: http://www.wmo.int/pages/prog/www/ois/Operational_Information/ \
        #             Newsletters/2000_2009/2005/Sept05/GTS.html

        if self.warn_about_bufr_size:
            if msg_size > 500000:
                print("WARNING: by convention BUFR messages should not be "+
                      "larger than 500kb to allow transmission over the GTS. "+
                      "Size of current message is: ", msg_size, " bytes")

        return (msg_size, section_sizes, section_start_locations)
        #  #]        
    def split(self):
        #  #[
        """
        scan a BUFR file to detect the start and end locations of the
        separate BUFR messages. Note that a BUFR file may contain
        additional junk, like GTS headers and such. The code should be
        robust enough to handle this.
        """
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

        txt_start  = b'BUFR'
        txt_end    = b'7777'
        list_of_start_locations = []
        list_of_end_locations   = []

        # try to find the start strings
        search_pos = 0
        file_end_reached = False
        while not file_end_reached:
            start_pos = self.data.find(txt_start, search_pos)
            if (start_pos == -1):
                file_end_reached = True
            else:
                list_of_start_locations.append(start_pos)
                search_pos = start_pos + 4

        # try to find the end strings
        search_pos = 0
        file_end_reached = False
        while not file_end_reached:
            end_pos = self.data.find(txt_end, search_pos)
            if (end_pos == -1):
                file_end_reached = True
            else:
                list_of_end_locations.append(end_pos)
                search_pos = end_pos + 4

        self.list_of_bufr_pointers = []

        # try each BUFR message; extract its length and see if
        # it matches an end location. If not we found a false start
        # marker or a corrupt BUFR message. If it matches, assume
        # the BUFR message is valid and add it to the list
        for start_location in list_of_start_locations:
            expected_msg_size, section_sizes, section_start_locations = \
                               self.get_expected_msg_size(start_location)
            if (self.verbose):
                print('expected_msg_size = ', expected_msg_size)
            expected_msg_end_location = start_location + expected_msg_size - 4
            if expected_msg_end_location in list_of_end_locations:
                if (self.verbose):
                    print('message seems alright, adding it to the list')
                # point to the end of the four sevens
                # (in slice notation, so the bufr msg data
                # can be adressed as data[start_pos:end_pos])
                # and store it
                self.list_of_bufr_pointers.append((start_location,
                                                   expected_msg_end_location+4,
                                                   section_sizes,
                                                   section_start_locations))
        

        # count howmany we found
        self.nr_of_bufr_messages = len(self.list_of_bufr_pointers)

        if (self.verbose):
            print("list_of_start_locations = ", list_of_start_locations)
            print("list_of_end_locations   = ", list_of_end_locations)

        #  #]
    def get_num_bufr_msgs(self):
        #  #[
        """
        request the number of BUFR messages in the current file
        """
        if (self.bufr_fd == None):
            print("ERROR: a bufr file first needs to be opened")
            print("using BUFRFile.open() before you can request the")
            print("number of BUFR messages in a file ..")
            raise IOError

        return self.nr_of_bufr_messages
        #  #]
    def get_raw_bufr_msg(self, msg_nr):
        #  #[
        """
        get the raw data for the BUFR message with given msg_nr
        (start counting at 1)
        """
        
        if (self.bufr_fd == None):
            print("ERROR: a bufr file first needs to be opened")
            print("using BUFRFile.open() before you can use the raw data ..")
            raise IOError

        # sanity test
        if (msg_nr>self.nr_of_bufr_messages):
            print("WARNING: non-existing BUFR message: ", msg_nr)
            print("This file only contains: ", self.nr_of_bufr_messages,
                  " BUFR messages")
            return (None, None, None)

        if (msg_nr<1):
            print("WARNING: invalid BUFR message number: ", msg_nr)
            print("For this file this number should be between 1 and: ",
                  self.nr_of_bufr_messages)
            return (None, None, None)

        self.last_used_msg = msg_nr
        (start_index, end_index, section_sizes, section_start_locations) = \
                      self.list_of_bufr_pointers[msg_nr-1]

        size_bytes = (end_index-start_index)

        # +3 because we have to round upwards to make sure all
        # bytes fit into the array of words (otherwise the last
        # few might be truncated from the data, which will crash
        # the struct.unpack() call below)
        size_words = (size_bytes+3)//4
        padding_bytes = size_words*4-size_bytes

        if (self.verbose):
            print("size_bytes = ", size_bytes)
            print("size_words = ", size_words)
            print("size_words*4 = ", size_words*4)
            print("padding_bytes = ", padding_bytes)
            
        # make sure we take the padding bytes along
        end_index = end_index+padding_bytes
        
        raw_data_bytes = self.data[start_index:end_index]

        # make sure the raw datastream is padded with zero bytes
        # to a multiple of 4 bytes. The ECMWF software may crash
        # if this is not the case ...
        nbytes = len(raw_data_bytes)
        nbytes_rounded = 4*(nbytes//4)
        if nbytes != nbytes_rounded:
            # print('padding problem found! fixing it ...')
            # print('nbytes = ',nbytes)
            # print('nbytes_rounded = ',nbytes_rounded)
            num_zeros_to_add = nbytes_rounded+4-nbytes
            # print('num_zeros_to_add = ',num_zeros_to_add)
            str_to_add = b''.join(b'\x00' for i in range(num_zeros_to_add))
            raw_data_bytes = raw_data_bytes + str_to_add

        if (self.verbose):
            print("len(raw_data_bytes) = ", len(raw_data_bytes))

        # assume little endian for now when converting
        # raw bytes/characters to integers and vice-versa
        dataformat = "<"+str(size_words)+"i"
        try:
            words = np.array(struct.unpack(dataformat, raw_data_bytes))
        except:
            # 0 signals this is not a valid BUFR msg, might be a false
            # start BUFR string, or a corrupted or truncated file
            return (0, section_sizes, section_start_locations)

        return (words, section_sizes, section_start_locations)
        #  #]
    def get_next_raw_bufr_msg(self):
        #  #[
        """
        get the raw data for the next BUFR message.
        This routine uses the internal instance variable last_used_msg
        to store the index of the last read BUFR message.
        """
        if (self.last_used_msg == self.nr_of_bufr_messages):
            raise EOFError
        
        return self.get_raw_bufr_msg(self.last_used_msg+1)
        #  #]
    def write_raw_bufr_msg(self, words):
        #  #[
        """
        write the raw BUFR message data to the BUFR file
        """
        # input data should be an array of words!
        size_words = len(words)
        size_bytes = size_words*4
        if (self.verbose):
            print("size_bytes = ", size_bytes)
            print("size_words = ", size_words)

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
        dataformat = "<i"
        for (i, word) in enumerate(words):
            data = struct.pack(dataformat, word)
            self.bufr_fd.write(data)

            if i == 0:
                if (self.verbose):
                    print("word = ", word)
                    print('data = ', data)
                    print('data[:4] = ', data[:4])
                    print('data[:4] = ', ';'.join(str(data[j])
                                                  for j in range(4)
                                                  if data[j].isalnum()))
                # safety check
                assert(data[:4] == b'BUFR')

        self.nr_of_bufr_messages = self.nr_of_bufr_messages + 1
        self.filesize = self.filesize + size_bytes
        #  #]
    #  #]
