#!/usr/bin/env python

"""
a module containing helpers to handle sys.path juggling
and python3 string handling cases
"""

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
    # print 'possible_so_files_1 = ',possible_so_files_1
    # print 'possible_so_files_2 = ',possible_so_files_2
    # sys.exit(1)
    
    if len(possible_so_files_1)>0:
        module_path = './'
    elif len(possible_so_files_2)>0:
        module_path = glob.glob(os.path.join('.', 'build', 'lib*'))[0]
    else:
        errtxt = 'could not find ecmwfbufr*.so; '+\
                 'the interface seems not yet build!'
        raise InterfaceBuildError(errtxt)

    abs_module_path = os.path.abspath(module_path)
    # print 'appending path: ', abs_module_path
    syspath.append(abs_module_path)

    if module_path != './':
        # remove the current dir from the path
        syspath_copy = syspath
        for spth in syspath_copy:
            abs_spth = os.path.abspath(spth)
            if abs_spth == os.path.abspath('./'):
                if spth in syspath:
                    # print 'removing path: ', spth
                    syspath.remove(spth)
                if abs_spth in syspath:
                    # print 'removing abs_path: ', abs_spth
                    syspath.remove(abs_spth)

    return (syspath, abs_module_path)
    #  #]


python3=False
try:
    if sys.version_info.major == 3:
        python3=True
except AttributeError:
    # python 2.6 and before has no major attibute in sys.version_info
    # so these will fall back to the default python3
    pass
