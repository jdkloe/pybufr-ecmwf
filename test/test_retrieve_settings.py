#!/usr/bin/env python

# Copyright J. de Kloe
# This software is licensed under the terms of the LGPLv3 Licence
# which can be obtained from https://www.gnu.org/licenses/lgpl.html

import pybufr_ecmwf.ecmwfbufr
import numpy
data = pybufr_ecmwf.ecmwfbufr.retrieve_settings()
print data
