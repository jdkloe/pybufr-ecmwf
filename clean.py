#!/usr/bin/env python

import os,glob

dir_to_delete   = ["ecmwf_bufr_lib/bufr_000380",
                   "ecmwf_bufr_lib/bufr_000371",
                   "ecmwf_bufr_lib/bufr_000381",
                   "f2py_build",
                   "tmp_BUFR_TABLES"]
files_to_delete = glob.glob("*~")
files_to_delete.extend(["libbufr.a",
                        "ecmwfbufr.so",
                        "ecmwf_bufr_lib/ConfigFile"])

for d in dir_to_delete:
    if (os.path.exists(d)):
        print "deleting dir: ",d
        os.system(r"\rm -rf "+d)
    # this only works if the dirs are empty!
    #os.removedirs(d)

for f in files_to_delete:
    if (os.path.exists(f)):
        print "deleting file: ",f
        os.remove(f)
        #os.system(r"\rm -f "+f)
    if (os.path.islink(f)):
        print "deleting symlink: ",f
        os.remove(f)

    
#os.remove(
    
