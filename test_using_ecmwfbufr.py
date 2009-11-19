#!/usr/bin/env python

#  #[ modules used
#from pylab import *
import numpy as np
import struct
import os
import ecmwfbufr
#  #]
#  #[ read the binary data
fd=open('Testfile.BUFR','rb')
data=fd.read()
len(data)

sizewords=len(data)/4
words = np.array(struct.unpack("<"+str(sizewords)+"i",data))
#print 'data[:4] = ',data[:4]
print 'data[:4] = ',';'.join(str(data[i]) for i in range(4) if data[i].isalnum())
print 'words[:4] = ',words[:4]
#  #]
#  #[ define the needed constants

# note: this block of constant parameters defining all array sizes
#       in the interfaces to this ecmwf library seems not available
#       through the f2py interface
#       It is defined in file:
#           ecmwf_bufr_lib/bufr_000380/bufrdc/parameter.F
#
#      PARAMETER(JSUP =   9,JSEC0=   3,JSEC1= 40,JSEC2=4096,JSEC3=   4,
#     1          JSEC4=2,JELEM=320000,JSUBS=400,JCVAL=150 ,JBUFL=512000,
#     2          JBPW =  32,JTAB =3000,JCTAB=3000,JCTST=9000,JCTEXT=9000,
#     3          JWORK=4096000,JKEY=46, JTMAX=10,JTCLAS=64,JTEL=255)

# TODO: read this file from python, in stead of hardcoding the numbers below

MAXNRDESCR    =     20 # 300
MAXNREXPDESCR =    140 # 160000
MAXNRSUBSETS  =    361 # 25

ktdlen = MAXNRDESCR
#krdlen = MAXNRDELREPLFACTORS
kelem  = MAXNREXPDESCR
kvals  = MAXNREXPDESCR*MAXNRSUBSETS
#jbufl  = MAXBUFRMSGSIZE
#jsup   = LENGTHKSUP

#  #]
#  #[ handle BUFR tables

# define our own location for storing (symlinks to) the BUFR tables
private_BUFR_TABLES_dir = os.path.abspath("./tmp_BUFR_TABLES")
if (not os.path.exists(private_BUFR_TABLES_dir)):
      os.mkdir(private_BUFR_TABLES_dir)

# make the needed symlinks
ecmwf_BUFR_TABLES_dir = os.path.abspath("ecmwf_bufr_lib/bufr_000380/bufrtables/")
needed_B_table    = "B0000000000210000001.TXT"
needed_D_table    = "D0000000000210000001.TXT"
available_B_table = "B0000000000098013001.TXT"
available_D_table = "D0000000000098013001.TXT"

# NOTE: the naming scheme used by ECMWF is sucht, that the table name can
#       be derived from elements from sections 0 and 1, which can be
#       decoded without loading bufr tables.
# TODO: implement this

source      = os.path.join(ecmwf_BUFR_TABLES_dir,  available_B_table)
destination = os.path.join(private_BUFR_TABLES_dir,needed_B_table)
if (not os.path.exists(destination)):
      os.symlink(source,destination)

source      = os.path.join(ecmwf_BUFR_TABLES_dir,  available_D_table)
destination = os.path.join(private_BUFR_TABLES_dir,needed_D_table)
if (not os.path.exists(destination)):
      os.symlink(source,destination)

# make sure the BUFR tables can be found
# also, force a slash at the end, otherwise the library fails to find the tables
e = os.environ
e["BUFR_TABLES"] = private_BUFR_TABLES_dir+os.path.sep

#  #]
#  #[ call BUS012
ksup   = np.zeros(         9,dtype=np.int)
ksec0  = np.zeros(         3,dtype=np.int)
ksec1  = np.zeros(        40,dtype=np.int)
ksec2  = np.zeros(      4096,dtype=np.int)
kerr   = 0

print "calling: ecmwfbufr.bus012():"
ecmwfbufr.bus012(words,ksup,ksec0,ksec1,ksec2,kerr)
# optional parameters: kbufl)
print "returned from: ecmwfbufr.bus012()"
print "kerr = ",kerr

print "ksup : ",ksup
print "sec0 : ",ksec0
print "sec1 : ",ksec1
print "sec2 : ",ksec2

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
#ksup   = np.zeros(         9,dtype=np.int)
#ksec0  = np.zeros(         3,dtype=np.int)
#ksec1  = np.zeros(        40,dtype=np.int)
#ksec2  = np.zeros(      4096,dtype=np.int)

ksec3  = np.zeros(         4,dtype=np.int)
ksec4  = np.zeros(         2,dtype=np.int)
cnames = np.zeros((kelem,64),dtype=np.character)
cunits = np.zeros((kelem,24),dtype=np.character)
values = np.zeros(     kvals,dtype=np.float64) # this is the default
cvals  = np.zeros((kvals,80),dtype=np.character)
kerr   = 0

print "calling: ecmwfbufr.bufrex():"
ecmwfbufr.bufrex(words,ksup,ksec0,ksec1,ksec2,ksec3,ksec4,
                 cnames,cunits,values,cvals,kerr)
# optional parameters: sizewords,kelem,kvals)
print "returned from: ecmwfbufr.bufrex()"
print "kerr = ",kerr

#  #]
#  #[ print a selection of the decoded numbers
print "Decoded BUFR message:"
print "ksup : ",ksup
print "sec0 : ",ksec0
print "sec1 : ",ksec1
print "sec2 : ",ksec2
print "sec3 : ",ksec3
print "sec4 : ",ksec4
print "cnames : ",cnames
print "cunits : ",cunits
print "values : ",values

nsubsets  = 361 # number of subsets in this BUFR message
nelements =  44 # size of one expanded subset
lat = np.zeros(nsubsets)
lon = np.zeros(nsubsets)
for s in range(nsubsets):
      #index_lat = nelements*(s-1)+24
      #index_lon = nelements*(s-1)+25
      index_lat = MAXNREXPDESCR*(s-1)+24
      index_lon = MAXNREXPDESCR*(s-1)+25
      lat[s] = values[index_lat]
      lon[s] = values[index_lon]
      if (30*(s/30)==s):
          print "s=",s, "lat = ",lat[s]," lon = ",lon[s]

print "min/max lat",min(lat),max(lat)
print "min/max lon",min(lon),max(lon)
#  #]
