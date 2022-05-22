import os
import sys
import glob
import shutil
import pytest

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

@pytest.fixture
def setup():  #autouse=True, scope="module"):
    #  #[ setup/teardown code
    print('DEBUG: inside my test setup function: setup')
    DUMMY_SYS_PATH = sys.path[:] # provide a copy
    (DUMMY_SYS_PATH, MY_MODULE_PATH) = \
                     get_and_set_the_module_path(DUMMY_SYS_PATH)
    # in case the build is done by setup.py,
    # the created ecmwfbufr.so module will be in a path like
    #    SWROOT/build/lib.linux-x86_64-2.7/pybufr_ecmwf/
    # To ensure the unittests find it, temporarily rename SWROOT/pybufr_ecmwf/
    # and create a symlink to SWROOT/build/lib.linux-x86_64-2.7/pybufr_ecmwf/
    PYBUFR_ECMWF_MODULE_WAS_RENAMED = False
    if 'build/lib' in MY_MODULE_PATH:
        print('renaming pybufr_ecmwf to pybufr_ecmwf.renamed')
        shutil.move('pybufr_ecmwf', 'pybufr_ecmwf.renamed')
        print('creating symlink pybufr_ecmwf')
        os.symlink(os.path.join(MY_MODULE_PATH, 'pybufr_ecmwf'), # source
                   'pybufr_ecmwf') # destination
        PYBUFR_ECMWF_MODULE_WAS_RENAMED = True
    # else:
    #    print('MY_MODULE_PATH = ', MY_MODULE_PATH)

    yield 0

    # teardown code
    print('DEBUG: inside my test setup function: teardown')
    
    # restore the original directory structure when all testing is done
    if PYBUFR_ECMWF_MODULE_WAS_RENAMED:
        # safety check
        if os.path.islink('pybufr_ecmwf'):
            print('removing symlink pybufr_ecmwf')
            os.remove('pybufr_ecmwf')
            print('renaming pybufr_ecmwf.renamed to pybufr_ecmwf')
            shutil.move('pybufr_ecmwf.renamed', 'pybufr_ecmwf')
    #  #]
