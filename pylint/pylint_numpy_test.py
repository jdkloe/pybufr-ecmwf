#!/usr/bin/env python
"""
a small piece of sample code to allow checking whether
pylint can properly check imports from numpy or not
"""

import numpy

X1 = numpy.zeros(5, dtype=int)
Y1 = numpy.linspace(0., 1., 5)
print 'X1 = numpy.zeros(5, dtype=int) = ', X1
print 'Y1 = numpy.linspace(0., 1., 5) = ', Y1
