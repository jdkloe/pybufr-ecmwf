      SUBROUTINE DO_MEM_DUMP(FILENAME)
      CHARACTER*(*) FILENAME

#      include "parameter.F"

#     include "bcmctc.F"
#     include "bcmct.F"
#     include "bcmdefc.F"
#     include "bcmel.F"
#     include "bcmoff.F"
#     include "bcmroot.F"
#     include "bcmrq.F"
#     include "bcmtabc.F"
#     include "bcmtab.F"
#     include "bcmtabloadc.F"
#     include "bcmtabload.F"
#     include "bcmwork.F"
#     include "bcmwtc.F"
#     include "bcmwt.F"
#     include "bcomatbc.F"
#     include "bcomatb.F"
#     include "bcombef.F"
#     include "bcomcom.F"
#     include "bcomp.F"
#     include "bcomunit.F"
#     include "bcprq.F"

C     these contain double definitions and cannot be used at the
C     same time as the above includes

C#     include "bcmatbc.F"
C#     include "bcmatb.F"
C#     include "bcmbef.F"
C#     include "bcomctc.F"
C#     include "bcomct.F"
C#     include "bcomdefc.F"
C#     include "bcomel.F"
C#     include "bcomoff.F"
C#     include "bcomreq.F"
C#     include "bcomroot.F"
C#     include "bcomrq.F"
C#     include "bcomtabc.F"
C#     include "bcomtab.F"
C#     include "bcomtabloadc.F"
C#     include "bcomtabload.F"
C#     include "bcomwork.F"
C#     include "bcomwtc.F"
C#     include "bcomwt.F"

      OPEN(21, FILE=FILENAME,STATUS="REPLACE",ACTION="WRITE")

      WRITE(21,*) "variables in: parameter.F"
      WRITE(21,*) "JSUP=", JSUP
      WRITE(21,*) "JSEC0=",JSEC0
      WRITE(21,*) "JSEC1=",JSEC1
      WRITE(21,*) "JSEC2= ",JSEC2
      WRITE(21,*) "JSEC3=",JSEC3
      WRITE(21,*) "JSEC4=",JSEC4
      WRITE(21,*) "JELEM=",JELEM
      WRITE(21,*) "JSUBS=",JSUBS
      WRITE(21,*) "JCVAL=",JCVAL
      WRITE(21,*) "JBUFL=",JBUFL
      WRITE(21,*) "JBPW=",JBPW
      WRITE(21,*) "JTAB=",JTAB
      WRITE(21,*) "JCTAB=",JCTAB
      WRITE(21,*) "JCTST=",JCTST
      WRITE(21,*) "JCTEXT=",JCTEXT
      WRITE(21,*) "JWORK=",JWORK
      WRITE(21,*) "JKEY=",JKEY
      WRITE(21,*) "JTMAX=",JTMAX
      WRITE(21,*) "JTCLAS=",JTCLAS
      WRITE(21,*) "JTEL=",JTEL

C     WRITE(21,*) "variables in: bcmctc.F"
C     WRITE(21,*) "CTEXT=",CTEXT ! size: JCTEXT=9000
      
C      WRITE(21,*) "variables in: bcmct.F"
C      WRITE(21,*) "NREF=",NREF ! size: JCTAB=3000
C      WRITE(21,*) "NSTART=",NSTART ! size: JCTAB=3000
C      WRITE(21,*) "NLEN=",NLEN ! size: JCTAB=3000
C      WRITE(21,*) "NCODNUM=",NCODNUM ! size: JCTST=9000
C      WRITE(21,*) "NSTARTC=",NSTARTC ! size: JCTST=9000
C      WRITE(21,*) "NLENC=",NLENC ! size: JCTST=9000
      
      WRITE(21,*) "variables in: bcmdefc.F"
      WRITE(21,*) "CECMWF=",CECMWF ! character string
      WRITE(21,*) "CUSER=",CUSER !  character string

      WRITE(21,*) "variables in: bcmel.F"
      WRITE(21,*) "NTDLEN=",NTDLEN ! size: 1
C      WRITE(21,*) "NTDLST=",NTDLST ! size: JELEM=320000
      WRITE(21,*) "NTDEXL=",NTDEXL ! size: 1
C      WRITE(21,*) "NTDEXP=",NTDEXP ! size: JELEM=320000

      WRITE(21,*) "variables in: bcmoff.F"
      WRITE(21,*) "NWP=",NWP ! size: 1
      WRITE(21,*) "NBP=",NBP ! size: 1
      WRITE(21,*) "NSUBSET=",NSUBSET ! size: 1
      WRITE(21,*) "OMULTI=",OMULTI ! size: 1

      WRITE(21,*) "variables in: bcmroot.F"
      WRITE(21,*) "CROOT=",CROOT ! size: 1
      WRITE(21,*) "OPRINT=",OPRINT ! size: 1
      
      WRITE(21,*) "variables in: bcmrq.F"
C      WRITE(21,*) "NWORDP=",NWORDP ! size: JWORK=4096000
C      WRITE(21,*) "NBITP=",NBITP ! size: JWORK=4096000

      WRITE(21,*) "variables in: bcmtabc.F"
C      WRITE(21,*) "CTABBEN=",CTABBEN ! size: JTAB=3000
C      WRITE(21,*) "CTABBU=",CTABBU ! size: JTAB=3000

      WRITE(21,*) "variables in: bcmtab.F"
C      WRITE(21,*) "NTABBTR=",NTABBTR ! size: JTAB=3000
C      WRITE(21,*) "NTABBS=",NTABBS ! size: JTAB=3000
C      WRITE(21,*) "NTABBRV=",NTABBRV ! size: JTAB=3000
C      WRITE(21,*) "NTABBDW=",NTABBDW ! size: JTAB=3000
C      WRITE(21,*) "NTABBDW=",NTABBDW ! size: JTAB=3000
C      WRITE(21,*) "NTABDTR=",NTABDTR ! size: JTAB=3000
C      WRITE(21,*) "NTABDST=",NTABDST ! size: JTAB=3000
C      WRITE(21,*) "NTABDL=",NTABDL ! size: JTAB=3000
C      WRITE(21,*) "NTABDSQ=",NTABDSQ ! size: JTAB*20=3000*20=60000
C      WRITE(21,*) "NTABP(64,256)=",NTABP ! size: 64,256=16384


      WRITE(21,*) "variables in: bcmtabloadc.F"
C      WRITE(21,*) "CCTABBEN=",CCTABBEN ! size: JTAB*JTMAX=3000*10=30000
C      WRITE(21,*) "CCTABBU=",CCTABBU ! size: JTAB*JTMAX=3000*10=30000
      WRITE(21,*) "CTABLE_LIST=",CTABLE_LIST ! size: JTMAX=10

      WRITE(21,*) "variables in: bcmtabload.F"
C      WRITE(21,*) "MTABBTR=",MTABBTR ! size: JTAB*JTMAX=3000*10=30000
C      WRITE(21,*) "MTABBS=",MTABBS ! size: JTAB*JTMAX=3000*10=30000
C      WRITE(21,*) "MTABBRV=",MTABBRV ! size: JTAB*JTMAX=3000*10=30000
C      WRITE(21,*) "MTABBDW=",MTABBDW ! size: JTAB*JTMAX=3000*10=30000
C      WRITE(21,*) "MTABDTR=",MTABDTR ! size: JTAB*JTMAX=3000*10=30000
C      WRITE(21,*) "MTABDST=",MTABDST ! size: JTAB*JTMAX=3000*10=30000
C      WRITE(21,*) "MTABDL=",MTABDL ! size:  (JTAB*JTMAX=3000*10=30000
C      WRITE(21,*) "MTABDSQ=",MTABDSQ ! size: JTAB*20*JTMAX=3000*20*10=600000
C      WRITE(21,*) "MTABP=",MTABP ! size: JTCLAS*JTEL*JTMAX=64*255*10=163200
      WRITE(21,*) "NTC=",NTC ! size: 1
      WRITE(21,*) "NTT=",NTT ! size: 1

      WRITE(21,*) "variables in: bcmwork.F"
      WRITE(21,*) "RVIND=",RVIND
      WRITE(21,*) "EPS=",EPS
      WRITE(21,*) "NBPW=",NBPW
      WRITE(21,*) "NWPT=",NWPT
      WRITE(21,*) "NBPT=",NBPT
      WRITE(21,*) "NWPTB=",NWPTB
      WRITE(21,*) "NBPTB=",NBPTB
      WRITE(21,*) "NMASK=",NMASK ! size: JBPW=32
      WRITE(21,*) "NVIND=",NVIND
      WRITE(21,*) "NBENP=",NBENP
      WRITE(21,*) "NLTVNP=",NLTVNP
      WRITE(21,*) "NWWP=",NWWP
      WRITE(21,*) "NXXP=",NXXP
      WRITE(21,*) "NYYP=",NYYP
      WRITE(21,*) "NZZP=",NZZP
      WRITE(21,*) "NSSP=",NSSP
      WRITE(21,*) "NEDN=",NEDN

      WRITE(21,*) "variables in: bcmwtc.F"
C      WRITE(21,*) "CWTEN=",CWTEN ! size: JELEM=320000
C      WRITE(21,*) "CWTU=",CWTU ! size: JELEM=320000

      WRITE(21,*) "variables in: bcmwt.F"
      WRITE(21,*) "NDWINC=",NDWINC
      WRITE(21,*) "NSCAM=",NSCAM
      WRITE(21,*) "NAFDW=",NAFDW
      WRITE(21,*) "NWT=",NWT
      WRITE(21,*) "ODREPF=",ODREPF
      WRITE(21,*) "N40=",N40
      WRITE(21,*) "N07=",N07
      WRITE(21,*) "N08=",N08
      WRITE(21,*) "NDWINC07=",NDWINC07
      WRITE(21,*) "NSCAM07=",NSCAM07
      WRITE(21,*) "NAFDWA=",NAFDWA ! size: 100
      WRITE(21,*) "NFD=",NFD
      WRITE(21,*) "NREP=",NREP
      WRITE(21,*) "OREP=",OREP
      WRITE(21,*) "N221=",N221
      WRITE(21,*) "MREL=",MREL
      WRITE(21,*) "NFCM=",NFCM
      WRITE(21,*) "NFUCM=",NFUCM
      WRITE(21,*) "MBMP=",MBMP
      WRITE(21,*) "OMARKER=",OMARKER
      WRITE(21,*) "MBMPL=",MBMPL
C      WRITE(21,*) "NSTACK=",NSTACK ! size: JELEM=320000
C      WRITE(21,*) "NWTEN=",NWTEN ! size: JELEM=320000
C      WRITE(21,*) "NWTR=",NWTR ! size: JELEM=320000
C      WRITE(21,*) "NWTS=",NWTS ! size: JELEM=320000
C      WRITE(21,*) "NWTRV=",NWTRV ! size: JELEM=320000
C      WRITE(21,*) "NWTDW=",NWTDW ! size: JELEM=320000
C      WRITE(21,*) "NWTIW=",NWTIW ! size: JELEM=320000
C      WRITE(21,*) "NWTIWS=",NWTIWS ! size: JELEM=320000

      WRITE(21,*) "variables in: bcomatbc.F"
C      WRITE(21,*) "CATBEN=",CATBEN ! size: JTAB=3000
C      WRITE(21,*) "CATBU=",CATBU ! size: JTAB=3000
      
      WRITE(21,*) "variables in: bcomatb.F"
      WRITE(21,*) "NJA=",NJA
C      WRITE(21,*) "NATBTR=",NATBTR ! size: JTAB=3000
C      WRITE(21,*) "NATBS=",NATBS ! size: JTAB=3000
C      WRITE(21,*) "NATBRV=",NATBRV ! size: JTAB=3000
C      WRITE(21,*) "NATBDW=",NATBDW ! size: JTAB=3000

      WRITE(21,*) "variables in: bcombef.F"
      WRITE(21,*) "M=",M
      WRITE(21,*) "MM=",MM
      WRITE(21,*) "N=",N
      WRITE(21,*) "JCV=",JCV

      WRITE(21,*) "variables in: bcomcom.F"
      WRITE(21,*) "ICOMP=",ICOMP
      
      WRITE(21,*) "variables in: bcomp.F"
C      WRITE(21,*) "INWTEN=",INWTEN ! size: JELEM=320000
C      WRITE(21,*) "INWTR=",INWTR ! size: JELEM=320000
C      WRITE(21,*) "INWTS=",INWTS ! size: JELEM=320000
C      WRITE(21,*) "INWTRV=",INWTRV ! size: JELEM=320000
C      WRITE(21,*) "INWTDW=",INWTDW ! size: JELEM=320000
C      WRITE(21,*) "INWORDP=",INWORDP ! size: JWORK=4096000
C      WRITE(21,*) "INBITP=",INBITP ! size: JWORK=4096000

      WRITE(21,*) "variables in: bcomunit.F"
      WRITE(21,*) "KNTN=",KNTN
      
      WRITE(21,*) "variables in: bcprq.F"
      WRITE(21,*) "NPMISS=",NPMISS
      WRITE(21,*) "NPRUS=",NPRUS
      WRITE(21,*) "NOKEY=",NOKEY
      WRITE(21,*) "NOFL=",NOFL
      
      
C     this one solved the bug!!!!
C      NJA=0

      CLOSE(21)

      RETURN
      END
