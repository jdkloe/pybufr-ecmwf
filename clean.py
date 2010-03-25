#!/usr/bin/env python

import os,glob,sys

# delete these dirs
dirs_glob_patterns = ["pybufr_ecmwf/ecmwf_bufr_lib/bufr_000*",
                      "ecmwf_bufr_lib/bufr_000*"]
dirs_to_delete = ["pybufr_ecmwf/example_programs/tmp_BUFR_TABLES",
                  "pybufr_ecmwf/tmp_BUFR_TABLES", "tmp_BUFR_TABLES",
                  "pybufr_ecmwf/f2py_build","build","dist"]

# delete these files
file_glob_patterns = ["*~","*/*~","*/*/*~","*.pyc","*/*.pyc",
                      "*/Testfile3Msgs.BUFR", "*/*/Testfile3Msgs.BUFR",
                      "pybufr_ecmwf/expected_test_outputs/*.actual_std*"]
files_to_delete = ["pybufr_ecmwf/libbufr.a", "libbufr.a","MANIFEST",
                   "pybufr_ecmwf/ecmwf_bufrtables","ecmwfbufr.so",
                   "ecmwf_bufrtables", "pybufr_ecmwf/ecmwfbufr.so",
                   "ecmwfbufr.so", "pybufr_ecmwf/ecmwf_bufr_lib/config_file",
                   "ecmwf_bufr_lib/config_file", "pybufr_ecmwf/ecmwfbufr.so"]

for pattern in dirs_glob_patterns:
    dirs_to_delete.extend(glob.glob(pattern))

for pattern in file_glob_patterns:
    files_to_delete.extend(glob.glob(pattern))

for d in dirs_to_delete:
    if (os.path.exists(d)):
        if (os.path.isdir(d)):
            print "deleting dir: ",d
            os.system(r"\rm -rf "+d)
    # this only works if the dirs are empty!
    #os.removedirs(d)

for f in files_to_delete:
    if (os.path.exists(f)):
        print "deleting file: ",f
        os.remove(f)
    if (os.path.islink(f)):
        print "deleting symlink: ",f
        os.remove(f)

print "done"
