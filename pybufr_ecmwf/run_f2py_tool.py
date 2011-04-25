#!/usr/bin/env python

"""
this is a stripped down version of the f2py tool that is present on
my own machine, and is included here since it seems the f2py tool
itself is not available in the standard path on some machines,
even if numpy and numpy.f2py are available as python module.
"""

from numpy.f2py import main
main()
