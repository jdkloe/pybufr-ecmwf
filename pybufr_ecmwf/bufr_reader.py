from pybufr_ecmwf import raw_bufr_file
from pybufr_ecmwf import ecmwfbufr
from pybufr_ecmwf import ecmwfbufr_parameters

import os
import numpy as np


class BUFRReader(object):
    """
    High Level BUFR reader based on iteration over the BUFR messages.

    Parameters
    ----------
    filename : string
        filename of the bufr file
    kelem_guess : int, optional
        if the elements per variable in as message are known
        please specify here.
        Otherwise the elements will be found out via trial and error
        This works most of the time but is not 100 percent failsafe
        Default: 500
    max_tries : int, optional
        the Reader will try max_tries times to unpack a bufr message.
        Some messages can not be read even if the array sizes are ok.
        Most of the time these files are corrupt.

    """

    def __init__(self, filename, kelem_guess=500, max_tries=10):
        self.bufr = raw_bufr_file.RawBUFRFile()
        self.bufr.open(filename, 'rb')
        self.nr_messages = self.bufr.get_num_bufr_msgs()
        self.max_tries = max_tries

        if 'BUFR_TABLES' not in os.environ:
            path = os.path.split(ecmwfbufr.__file__)[0]
            os.environ["BUFR_TABLES"] = os.path.join(
                path, 'ecmwf_bufrtables' + os.sep)

        self.size_ksup = ecmwfbufr_parameters.JSUP
        self.size_ksec0 = ecmwfbufr_parameters.JSEC0
        self.size_ksec1 = ecmwfbufr_parameters.JSEC1
        self.size_ksec2 = ecmwfbufr_parameters.JSEC2
        self.size_key = ecmwfbufr_parameters.JKEY
        self.size_ksec3 = ecmwfbufr_parameters.JSEC3
        self.size_ksec4 = ecmwfbufr_parameters.JSEC4

        self.kelem_guess = kelem_guess

    def messages(self):
        """
        Raises
        ------
        IOError:
            if a message cannot be unpacked after max_tries tries

        Yields
        ------
        data : dict
            Dictionary of the data in the BUFR message.
            Keys are the names of the variables.
        units: dict
            The units of each data field in the data dictionary.
            Keys are the same as in the data dictionary.
        """

        for i in np.arange(self.nr_messages) + 1:
            tries = 0

            ksup = np.zeros(self.size_ksup, dtype=np.int)
            ksec0 = np.zeros(self.size_ksec0, dtype=np.int)
            ksec1 = np.zeros(self.size_ksec1, dtype=np.int)
            ksec2 = np.zeros(self.size_ksec2, dtype=np.int)
            ksec3 = np.zeros(self.size_ksec3, dtype=np.int)
            ksec4 = np.zeros(self.size_ksec4, dtype=np.int)

            kerr = 0
            data = self.bufr.get_raw_bufr_msg(i)

            ecmwfbufr.bus012(data[0],  # input
                             ksup,  # output
                             ksec0,  # output
                             ksec1,  # output
                             ksec2,  # output
                             kerr)  # output

            kelem = self.kelem_guess
            ksup_first = ksup[5]
            kvals = ksup_first * kelem
            max_kelem = 500000
            self.init_values = np.zeros(kvals, dtype=np.float64)
            self.cvals = np.zeros((kvals, 80), dtype=np.character)
            # try to expand bufr message with the first guess for
            # kelem
            increment_arraysize = True
            while increment_arraysize:
                cnames = np.zeros((kelem, 64), dtype='|S1')
                cunits = np.zeros((kelem, 24), dtype='|S1')
                ecmwfbufr.bufrex(data[0],  # input
                                 ksup,  # output
                                 ksec0,  # output
                                 ksec1,  # output
                                 ksec2,  # output
                                 ksec3,  # output
                                 ksec4,  # output
                                 cnames,  # output
                                 cunits,  # output
                                 self.init_values,  # output
                                 self.cvals,  # output
                                 kerr)  # output
                # no error - stop loop
                if kerr == 0 and ksec4[0] != 0:
                    increment_arraysize = False
                # error increase array size and try to unpack again
                else:
                    tries += 1
                    if tries >= self.max_tries:
                        raise IOError('This file seems corrupt')
                    kelem = kelem * 5
                    kvals = ksup_first * kelem

                    if kelem > max_kelem:
                        kelem = kvals / 2
                        max_kelem = kvals

                    self.init_values = np.zeros(kvals, dtype=np.float64)
                    self.cvals = np.zeros((kvals, 80), dtype=np.character)

            decoded_values = ksup[4]
            # set kelem_guess to decoded values of last message
            # only increases reading speed if all messages are the same
            # not sure if this is the best option
            self.kelem_guess = decoded_values
            decoded_msg = ksup[5]
            # calculate first dimension of 2D array
            factor = kvals / kelem

            # reshape and trim the array to the actual size of the data
            values = self.init_values.reshape((factor, kelem))
            values = values[:decoded_msg, :decoded_values]

            # reshape and format the cnames and cunits string attributes.
            cnames = [''.join(x).rstrip() for x in cnames[:decoded_values, :]]
            cunits = [''.join(x).rstrip() for x in cunits[:decoded_values, :]]

            data = {}
            units = {}
            for i, name in enumerate(cnames):
                data[name] = values[:, i]
                units[name] = cunits[i]

            yield data, units

    def __enter__(self):
        return self

    def __exit__(self, exc, val, trace):
        self.bufr.close()
