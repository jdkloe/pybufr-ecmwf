#!/bin/bash

# a script that handles installation of the different requirements
# for the different cases in the travis test sequence,
# both for linux and for osx.

# based on the example in:
# https://docs.travis-ci.com/user/multi-os/

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then

    # Ensure brew is up-to-date
    # Then install gcc (which should include gfortran)
    # but first unlink the system version of gcc, and then reinstall it.
    # This ensures it is the same version that was used for building
    # python, which in turn is required to build fortran and c-based
    # python extensions.
    # Also install Homebrew that provides python 2.7 and 3.5
    brew update
    brew unlink gcc
    brew install gcc
    brew tap Homebrew/python
    
    # install custom requirements on OS X using brew
    case "${TOXENV}" in
        py27)
            # install Python 2.7 and numpy on OS X
	    #brew unlink python
            #brew install python
            #brew install homebrew/python/numpy
	    echo "it seems python + numpy is available by default now for OSX"
            ;;
        py35)
            # install Python 3.5 and numpy on OS X
	    # brew unlink python3
            brew install python3
            #brew unlink numpy
            #brew unlink numpy --with-python3
            brew install homebrew/python/numpy --with-python3
            brew link --overwrite homebrew/python/numpy --with-python3
            ;;
    esac
else
    # Install the gfortran requirement on Linux
    sudo apt-get update -qq
    sudo apt-get install -y gfortran
    # install numpy
    pip install numpy
fi
