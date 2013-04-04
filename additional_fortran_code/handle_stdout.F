C
C     This file is intended to open a fileunit used for
C     all textoutputs (KNTN) which usually is stdout,
C     but may be changed to an external file called
C     fort.N by setting the environment setting STD_OUT
C     to the integer number N (5 and 6 are normally
C     used for stderr and stdout, so this number should
C     be choosen above 6).
C     The pybufr_ecmwf module uses this functionality
C     to redirect the fortran stdout because otherwise
C     the stdout channels of fortran and c are mixed in
C     inpredictable ways, and running unittests on this
C     code becomes impossible ...
C
C     Written by: J. de Kloe, 2013
C

      SUBROUTINE OPEN_FORTRAN_STDOUT(FILENAME)
      CHARACTER*(*) FILENAME

#     include "bcomunit.F"

      OPEN(KNTN,FILE=FILENAME,STATUS="REPLACE",ACTION="WRITE")

      RETURN
      END

      SUBROUTINE CLOSE_FORTRAN_STDOUT()

#     include "bcomunit.F"

      CLOSE(KNTN)

      RETURN
      END
