#!/usr/bin/env python

"""
this module collects a number of general helper routines
and classes used on several places in the code.
"""

#  #[ documentation:
#
# this file defines some helper subroutines used in several places
# and a collection of custom exceptions
#
#
# Written by: J. de Kloe, KNMI (www.knmi.nl), Initial version 19-Mar-2010
#
# License: GPL v2.
#
#  #]
#  #[ imported modules 
import os          # operating system functions
#  #]


def get_tables_dir():
    #  #[
    """ inspect the location of the helpers.py file, and derive
    from this the location of the BUFR tables that are delivered
    with the ECMWF BUFR library software
    """ 
    
    helpers_path = os.path.split(__file__)[0]
    path1 = os.path.join(helpers_path, "ecmwf_bufrtables")
    path2 = os.path.join(helpers_path, '..', "ecmwf_bufrtables")

    if os.path.exists(path1):
        ecmwf_bufr_tables_dir = path1
    elif os.path.exists(path2):
        ecmwf_bufr_tables_dir = path2
    else:
        print "Error: could not find BUFR tables directory"
        raise IOError

    # make sure the path is absolute, otherwise the ECMWF library
    # might fail when it attempts to use it ...
    ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
    return ecmwf_bufr_tables_dir
    #  #]

