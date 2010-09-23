#################################################
# ideas on how the module should/could be used: #
#################################################

#################################################
# reading a BUFR file
#################################################
#
# bf = BUFRFile(filename,'r')
# print bf.get_num_bufr_msgs()
# ==> 3
# print len(bf)
# ==> 3
#
# for msg in bf:
#    print msg
#    ==> BUFR msg holding 361 subsets of 44 descriptors
#    print len(msg)
#    ==>361
#    for subset in msg:
#      print subset
#      ==>BUFR MSG SUBSET holding 44 descriptors
#      print len(subset)
#      ==>44
#      for item in subset:
#         if item['name'] == 'LATITUDE (COARSE ACCURACY)':
#            print item.value
#            ==>-2.91
#    
#    x = msg.get_values('LATITUDE (COARSE ACCURACY)')  
#    print x
#    array([1.21,1.43,1.66,...])
#
#      
################################################

################################################
# creating a BUFR table from scratch
################################################
# 
# bt = BUFRtable()
# bt.add_B(key="011012", # also called "table reference"
#          name="WIND SPEED AT 10 M",
#          unit="M/S",
#          scale=1,      # also named "unit scale"
#          offset=0,     # also called "reference value"
#          numbits=12,   # also called "data width"
#          remark="some comment")
#
# ERROR: InvalidKeyError: only BUFR table B keys with FXXYYY reference
# numbers with above XX in the range 48-63 or YYY in the range 192-255
# are allowed to be redefined for local use. The other ranges are reserved
# for the official reference numbers as issued by WMO.
#
# (NOTE: for use of this format outside meteorology it might be usefull
#  to add a switch to allow this anyway)
#
# bt.add_B(key="063012", # also called "table reference"
#          name="MODIFIED WIND SPEED AT 10 M",
#          unit="CM/S",
#          scale=3,      # also named "unit scale"
#          offset=0,     # also called "reference value"
#          numbits=9,   # also called "data width"
#          remark="my own private wind speed definition")
#
# (should end succesfull)
#
# tm = BufrTemplate()
# tm.add_descriptors(dd_d_date_YYYYMMDD,
#                    dd_d_time_HHMM)
#
# bt.add_D(key="363255"
#          tmpl=tm,
#          remark="my remark")
#
# bt.copy_B(from="B0000000000210000001.TXT",
#           key="005001",
#           newkey="063001")
#
# bt.copy_B(from="B0000000000210000001.TXT",
#           newkey="006001") # newkey=key="006001" in this case
#
# bt.copy_D(from="D0000000000210000001.TXT",
#           key="300003"
#           newkey="363003")
#
# bt.copy_D(from="D0000000000210000001.TXT",
#           key="300004") # newkey=key="300004" in this case
#
# bt.save(filename_B,filename_D) # saves B and D tables
#
################################################

################################################
# see also:
# http://www.wmo.int/pages/prog/www/WMOCodes.html
# http://www.wmo.int/pages/prog/www/WMOCodes/BUFRTableB_112007.doc
# http://www.wmo.int/pages/prog/www/WMOCodes/Guides/BUFRCREXPreface_en.html
# for the official WMO documentation
#
# and
#
# http://www.ecmwf.int/products/data/software/bufr.html
# http://www.ecmwf.int/products/data/software/bufr_user_guide.pdf
# http://www.ecmwf.int/products/data/software/bufr_reference_manual.pdf
# for the ECMWF documentation
#
