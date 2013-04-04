C
C     This file allows requesting values of some hard coded constants
C     that are used in this BUFR software, in the include file
C     parameter.F.
C     This allows allocating arrays to the proper sizes BEFORE calling 
C     code from the BUFR library.
C
C     This also includes the JBPW value (which actually is defined as JBPW_DEF
C     in the fortint.h include file), which allows to construct interfaces to
C     c and python that actually work (i.e. use the correct integer types...)
C
C     Written by: J. de Kloe, 2013
C

      SUBROUTINE RETRIEVE_SETTINGS(
     1     VAL_JSUP, VAL_JSEC0, VAL_JSEC1, VAL_JSEC2, VAL_JSEC3,
     2     VAL_JSEC4, VAL_JELEM, VAL_JSUBS, VAL_JCVAL, VAL_JBUFL,
     3     VAL_JBPW, VAL_JTAB, VAL_JCTAB, VAL_JCTST, VAL_JCTEXT,
     4     VAL_JWORK, VAL_JKEY, VAL_JTMAX, VAL_JTCLAS, VAL_JTEL)

C     all these variables are outputs:
      INTEGER, INTENT(OUT) :: VAL_JSUP, VAL_JSEC0, VAL_JSEC1
      INTEGER, INTENT(OUT) :: VAL_JSEC2, VAL_JSEC3, VAL_JSEC4
      INTEGER, INTENT(OUT) :: VAL_JELEM, VAL_JSUBS, VAL_JCVAL
      INTEGER, INTENT(OUT) :: VAL_JBUFL, VAL_JBPW, VAL_JTAB
      INTEGER, INTENT(OUT) :: VAL_JCTAB, VAL_JCTST, VAL_JCTEXT
      INTEGER, INTENT(OUT) :: VAL_JWORK, VAL_JKEY, VAL_JTMAX
      INTEGER, INTENT(OUT) :: VAL_JTCLAS, VAL_JTEL

#     include "parameter.F"

      VAL_JSUP = JSUP
      VAL_JSEC0 = JSEC0
      VAL_JSEC1 = JSEC1
      VAL_JSEC2 = JSEC2
      VAL_JSEC3 = JSEC3
      VAL_JSEC4 = JSEC4
      VAL_JELEM = JELEM
      VAL_JSUBS = JSUBS
      VAL_JCVAL = JCVAL
      VAL_JBUFL = JBUFL
      VAL_JBPW = JBPW
      VAL_JTAB = JTAB
      VAL_JCTAB = JCTAB
      VAL_JCTST = JCTST
      VAL_JCTEXT = JCTEXT
      VAL_JWORK = JWORK
      VAL_JKEY = JKEY
      VAL_JTMAX = JTMAX
      VAL_JTCLAS = JTCLAS
      VAL_JTEL = JTEL

      RETURN
      END

C     in addition this kind of routines could be added to allow
C     requesting single items

      SUBROUTINE RETRIEVE_JBPW(VAL_JBPW)

C     output:
      INTEGER VAL_JBPW
      
#     include "parameter.F"

      VAL_JBPW = JBPW

      RETURN
      END
