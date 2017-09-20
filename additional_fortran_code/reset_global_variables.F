      SUBROUTINE RESET_GLOBAL_VARS

#     include "parameter.F"
#     include "bcomatb.F"
      
C     bufrdc version 000409 contains this bug:
C     one of the global variables (NJA in the common block defined
C     by bcomatb.F is not always reset for a next decode call from
C     the same program (because it is behind an if statement)
C     This causes the NJA variable to increment with each augmented
C     descriptor found in the template. If many messages are read
C     in sequence, eventually the NJA index exceeds the size of the arrays
C     (currently this is 3000) that use it, and the converter crashes,
C     Forcing it to zero before each decode call solves this problem.
      
      NJA=0

      END
