#!/bin/bash

# based on the example in:
# https://docs.travis-ci.com/user/multi-os/

echo "Inside: .travis/install.sh"
echo "TRAVIS_OS_NAME = $TRAVIS_OS_NAME"
echo "TOXENV = $TOXENV"

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then

    # ensure brew is up-to-date
    # install gcc (which should include gfortran)
    # install Homebrew that provides python 2.7 and 3.5
    brew update
    brew install gcc
    brew brew tap Homebrew/python
    
    # install custom requirements on OS X using brew
    case "${TOXENV}" in
        py27)
            # install Python 2.7 and numpy on OS X
            brew install python
            brew install numpy
            ;;
        py35)
            # install Python 3.5 and numpy on OS X
            brew install python3
            brew install numpy --with-python3
            ;;
    esac
else
    # Install the gfortran requirement on Linux
    sudo apt-get update -qq
    sudo apt-get install -y gfortran
    pip install numpy
fi
