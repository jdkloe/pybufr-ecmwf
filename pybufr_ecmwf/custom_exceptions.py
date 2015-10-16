#!/usr/bin/env python

"""
this file defines custom exceptions to be used by this module.
All these exceptions are derived from the PybufrEcmwfBaseError class
to enable users to easily catch them all.
"""

# Written by: J. de Kloe, KNMI (www.knmi.nl)
#
# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

# see: http://docs.python.org/library/exceptions.html
# for a list of already available exceptions.
# are:     IOError, EOFError

class PybufrEcmwfBaseError(Exception):
    """ a generic base exception for this module """
    pass

class EcmwfBufrLibError(PybufrEcmwfBaseError):
    """ an exception to indicate that one of the subroutines or functions
    in the ECMWF bufr library returned with an error """
    pass

class EcmwfBufrTableError(PybufrEcmwfBaseError):
    """ an exception to indicate that no set of suitable BUFR tables
    needed for bufr decoding/encoding can be found """
    pass

class IncorrectUsageError(PybufrEcmwfBaseError):
    """ an exception to indicate that the user tried to use
    a method incorrectly. """
    pass
# todo:
# add a check here to ensure a (hopefully) helpfull error text
# is provided explaining to the user what to do.

class NoMsgLoadedError(PybufrEcmwfBaseError):
    """ an exception to indicate that no message has yet been
    loaded from the currently open BUFR file. """
    pass

class CannotExpandFlagsError(PybufrEcmwfBaseError):
    """ an exception to indicate that the user tried to expand
    flags,  but used this in a wrong way. """
    pass

class ProgrammingError(PybufrEcmwfBaseError):
    """ an exception to indicate that a programming error seems
    present in the code (this should be reported to the author) """
    pass

# build exceptions, used by the build_interface.py script
# and the build_test.py script
class BuildException(PybufrEcmwfBaseError):
    """ a generic base exception for this build script """
    pass

class NetworkError(BuildException):
    """ an exception to indicate that a network problem occurred """
    pass

class LibraryBuildError(BuildException):
    """ an exception to indicate that building the ECMWF BUFR
    library has failed """
    pass

class InterfaceBuildError(BuildException):
    """ an exception to indicate that building the fortran-to-python
    interface has failed """
    pass

