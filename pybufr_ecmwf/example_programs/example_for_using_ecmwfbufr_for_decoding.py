#!/usr/bin/env python

"""
This is a small example program intended to demonstrate
how the raw wrapper interface to the ECMWF BUFR library may be
used for decoding a BUFR message.
"""

# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
# Written by: J. de Kloe, KNMI, Initial version 21-Jan-2010    
#
# License: GPL v2.

import os          # operating system functions
import sys         # system functions
import numpy as np # import numerical capabilities

# import the RawBUFRFile class to load the encoded raw BUFR data
module_found = False
module_name = "pybufr_ecmwf"
for path in sys.path:
    if os.path.isdir(path):
        if module_name in os.listdir(path):
            module_found = True
            print "module "+module_name+" found in path: "+path
            break

# make sure if we execute from within the source package, to let that
# version have preference over a system wide module installation with the
# same name, by having its path in front.
path = ".."
if os.path.isdir(os.path.join(path, module_name)):
    sys.path.insert(0, path)
    print "module "+module_name+" found in path: "+path

path = "../.."
if os.path.isdir(os.path.join(path, module_name)):
    sys.path.insert(0, path)
    print "module "+module_name+" found in path: "+path

print "sys.path = ", sys.path

from pybufr_ecmwf import RawBUFRFile#, BUFRInterfaceECMWF
# import the raw wrapper interface to the ECMWF BUFR library
from pybufr_ecmwf import ecmwfbufr

import pybufr_ecmwf
print "pybufr_ecmwf.__path__ = ", pybufr_ecmwf.__path__

# decoding_excample
def decoding_example():
    """
    wrap the example in a function to circumvent the pylint
    convention of requiring capitals for constants in the global
    scope (since most of these variables are not constants at all))
    """

    # read the binary data using the BUFRFile class
    # make sure it finds the testfile from the main module dir
    # and from within the example_programs dir
    if os.path.exists('testdata'):
        input_test_bufr_file = 'testdata/Testfile.BUFR'
    else:
        input_test_bufr_file = '../testdata/Testfile.BUFR'
        
    rbf = RawBUFRFile()
    rbf.open(input_test_bufr_file, 'r')
    words = rbf.get_next_raw_bufr_msg()
    rbf.close()
    
    # define the needed constants
    max_nr_descriptors          =     20 # 300
    max_nr_expanded_descriptors =    140 # 160000
    max_nr_subsets              =    361 # 25
    
    ktdlen = max_nr_descriptors
    # krdlen = max_nr_delayed_replication_factors
    kelem  = max_nr_expanded_descriptors
    kvals  = max_nr_expanded_descriptors*max_nr_subsets
    # jbufl  = max_bufr_msg_size
    # jsup   = length_ksup
    
    # handle BUFR tables
    print '------------------------------'
    
    # define our own location for storing (symlinks to) the BUFR tables
    private_bufr_tables_dir = os.path.abspath("./tmp_BUFR_TABLES")
    if (not os.path.exists(private_bufr_tables_dir)):
        os.mkdir(private_bufr_tables_dir)
    
    # make the needed symlinks
    
    ecmwf_bufr_tables_dir = os.path.join(pybufr_ecmwf.__path__[0],
                                         "ecmwf_bufrtables")
    if not os.path.exists(ecmwf_bufr_tables_dir):
        print "Error: could not find BUFR tables directory"
        raise IOError

    ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
    needed_b_table    = "B0000000000210000001.TXT"
    needed_d_table    = "D0000000000210000001.TXT"
    available_b_table = "B0000000000098013001.TXT"
    available_d_table = "D0000000000098013001.TXT"
    
    source      = os.path.join(ecmwf_bufr_tables_dir, available_b_table)
    destination = os.path.join(private_bufr_tables_dir, needed_b_table)
    if (not os.path.exists(destination)):
        os.symlink(source, destination)
    
    source      = os.path.join(ecmwf_bufr_tables_dir, available_d_table)
    destination = os.path.join(private_bufr_tables_dir, needed_d_table)
    if (not os.path.exists(destination)):
        os.symlink(source, destination)
            
    # make sure the BUFR tables can be found
    # also, force a slash at the end, otherwise the library fails
    # to find the tables
    env = os.environ
    env["BUFR_TABLES"] = private_bufr_tables_dir+os.path.sep
    
    ksup   = np.zeros(         9, dtype = np.int)
    ksec0  = np.zeros(         3, dtype = np.int)
    ksec1  = np.zeros(        40, dtype = np.int)
    ksec2  = np.zeros(      4096, dtype = np.int)
    kerr   = 0
    
    print "calling: ecmwfbufr.bus012():"
    ecmwfbufr.bus012(words, ksup, ksec0, ksec1, ksec2, kerr)
    if (kerr != 0):
        print "kerr = ", kerr
        sys.exit(1)
    print 'ksup = ', ksup
    print '------------------------------'
    print "printing content of section 0:"
    print "sec0 : ", ksec0
    ecmwfbufr.buprs0(ksec0)
    print '------------------------------'
    print "printing content of section 1:"
    print "sec1 : ", ksec1
    ecmwfbufr.buprs1(ksec1)
    key = np.zeros(52, dtype = np.int)
    sec2_len = ksec2[0]
    print '------------------------------'
    print "length of sec2: ", sec2_len
    if (sec2_len > 0):
        # buukey expands local ECMWF information from section 2 to the key array
        print '------------------------------'
        print "calling buukey"
        ecmwfbufr.buukey(ksec1, ksec2, key, ksup, kerr)
        print "sec2 : ", ksec2
        print "printing content of section 2:"
        ecmwfbufr.buprs2(ksup, key)
    else:
        print 'skipping section 2 [since it seems unused]'

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
    if (kerr != 0):
        print "kerr = ", kerr
        sys.exit(1)
        
    # print a selection of the decoded numbers
    print '------------------------------'
    print "Decoded BUFR message:"
    print "ksup : ", ksup
    print "sec0 : ", ksec0
    print "sec1 : ", ksec1
    print "sec2 : ", ksec2
    print "sec3 : ", ksec3
    print "sec4 : ", ksec4
    print "cnames [cunits] : "
    for (i, cnm) in enumerate(cnames):
        cun = cunits[i]
        txtn = ''.join(c for c in cnm)
        txtu = ''.join(c for c in cun)
        if (txtn.strip() != ''):
            print '[%3.3i]:%s [%s]' % (i, txtn, txtu)

    print "values : ", values
    txt = ''.join(str(v)+';' for v in values[:20] if v>0.)
    print "values[:20] : ", txt
    
    nsubsets  = ksec3[2] # 361 # number of subsets in this BUFR message

    #not yet used:
    #nelements = ksup[4] # 44 # size of one expanded subset
    
    lat = np.zeros(nsubsets)
    lon = np.zeros(nsubsets)
    for subs in range(nsubsets):
        # index_lat = nelements*(s-1)+24
        # index_lon = nelements*(s-1)+25
        index_lat = max_nr_expanded_descriptors*(subs-1)+24
        index_lon = max_nr_expanded_descriptors*(subs-1)+25
        lat[subs] = values[index_lat]
        lon[subs] = values[index_lon]
        if (30*(subs/30) == subs):
            print "subs = ", subs, "lat = ", lat[subs], " lon = ", lon[subs]
            print "min/max lat", min(lat), max(lat)
            print "min/max lon", min(lon), max(lon)
            
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
    if (kerr != 0):
        print "kerr = ", kerr
        sys.exit(1)

    print 'busel result:'
    print "ktdlen = ", ktdlen
    print "ktdexl = ", ktdexl
    
    selection1 = np.where(ktdlst > 0)
    ktdlen = len(selection1[0])
    selection2 = np.where(ktdexp > 0)
    ktdexl = len(selection2[0])
    
    print 'fixed lengths:'
    print "ktdlen = ", ktdlen
    print "ktdexl = ", ktdexl
    
    print 'descriptor lists:'
    print "ktdlst = ", ktdlst[:ktdlen]
    print "ktdexp = ", ktdexp[:ktdexl]
    
    print '------------------------------'
    print "printing content of section 3:"
    print "sec3 : ", ksec3
    ecmwfbufr.buprs3(ksec3, ktdlst, ktdexp, cnames)


print "-"*50
print "BUFR decoding example"
print "-"*50

decoding_example()

print "-"*50
print "done"
print "-"*50
