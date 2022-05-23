import os
import sys
import glob
import shutil
import pytest

def provide_installed_so_files_and_tables():
    #  #[
    """
    a little helper function to symlink the compiled *.so files,
    and generated *.py files,
    and a symlink to the BUFR tables directory.
    """
    module_path = glob.glob(os.path.join('.', 'build', 'lib*'))[0]

    # files to copy
    file_patterns = ['ecmwfbufr*.so',
                     'ecmwfbufr_parameters.py',
                     'version.py']
    dirs_to_link = ['ecmwf_bufrtables', ]

    for fnp in file_patterns:
        pattern = os.path.join(module_path, 'pybufr_ecmwf', fnp)
        filenames = glob.glob(pattern)
        for fn in filenames:
            src = os.path.join('..', fn)
            dst = os.path.join('pybufr_ecmwf', os.path.split(fn)[1])
            if not os.path.islink(dst):
                print('creating symlink: {} => {}'.format(dst, src))
                os.symlink(src, dst)

    for dtl in dirs_to_link:
        rel_dirname = os.path.join(module_path, 'pybufr_ecmwf', dtl)
        src = os.path.join('..', rel_dirname)
        dst = os.path.join('pybufr_ecmwf', dtl)
        if not os.path.islink(dst):
            print('creating symlink: {} => {}'.format(dst, src))
            os.symlink(src, dst)
    #  #]

@pytest.fixture
def setup():  #autouse=True, scope="module"):
    #  #[ setup/teardown code
    print('DEBUG: inside my test setup function: setup')
    provide_installed_so_files_and_tables()

    yield 0

    # teardown code
    print('DEBUG: inside my test setup function: teardown')
    #  #]
