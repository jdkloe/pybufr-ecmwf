#!/usr/bin/env python

"""
a module containing helpers to handle sys.path juggling
and python3 string handling cases
"""

# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

from __future__ import (absolute_import, division,
                        print_function) #, unicode_literals)

import os, sys    # operating system functions
import glob       # support wildcard expansion on filenames

def get_and_set_the_module_path(syspath):
    #  #[
    """
    a little helper function to see where to import the module from,
    either the local directory or the build/lib.linux* directory
    """
    possible_so_files_1 = glob.glob(os.path.join('.',
                                                 'pybufr_ecmwf',
                                                 'ecmwfbufr*.so'))
    possible_so_files_2 = glob.glob(os.path.join('.', 'build', 'lib*',
                                                 'pybufr_ecmwf',
                                                 'ecmwfbufr*.so'))
    # print('possible_so_files_1 = ',possible_so_files_1)
    # print('possible_so_files_2 = ',possible_so_files_2)
    # sys.exit(1)
    
    if len(possible_so_files_1)>0:
        module_path = './'
    elif len(possible_so_files_2)>0:
        module_path = glob.glob(os.path.join('.', 'build', 'lib*'))[0]
    else:
        errtxt = 'could not find ecmwfbufr*.so; '+\
                 'the interface seems not yet build!'
        raise RuntimeError(errtxt)

    abs_module_path = os.path.abspath(module_path)
    # print('appending path: ', abs_module_path)
    #syspath.append(abs_module_path)
    syspath.insert(0,abs_module_path)
    syspath.insert(0,os.path.join(abs_module_path, 'pybufr_ecmwf'))

    if module_path != './':
        # remove the current dir from the path
        syspath_copy = syspath
        for spth in syspath_copy:
            abs_spth = os.path.abspath(spth)
            if abs_spth == os.path.abspath('./'):
                if spth in syspath:
                    # print('removing path: ', spth)
                    syspath.remove(spth)
                if abs_spth in syspath:
                    # print('removing abs_path: ', abs_spth)
                    syspath.remove(abs_spth)

    return (syspath, abs_module_path)
    #  #]

def get_software_root():
    #  #[ find the software root 
    # i.e. find the parent dir that holds build_interface.py
    # (differs when doing "python setup.py build"
    #  or when calling directly build_interface.py)

    current_path = os.getcwd()
    build_dir = os.path.abspath(current_path)
    
    software_root = None
    tmp_dir = build_dir
    while software_root is None:
        files = os.listdir(tmp_dir)
        if 'build_interface.py' in files:
            software_root = tmp_dir
        else:
            tmp_dir, subdir = os.path.split(tmp_dir)
            if subdir == '':
                break
    return software_root
    #  #]
    
