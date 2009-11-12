#!/usr/bin/env python

signature_file = "f2py_build/signatures.pyf"

# these values are defined in parameter.F 
#PARAMETER(JSUP =   9,
#          JSEC0=   3,
#          JSEC1=  40,
#          JSEC2=4096,
#          JSEC3=   4
#          JSEC4=   2,
#          JELEM=320000,
#          JSUBS=400,
#          JCVAL=150 ,
#          JBUFL=512000,
#          JBPW =  32,
#          JTAB =3000,
#          JCTAB=3000,
#          JCTST=9000,
#          JCTEXT=9000,
#          JWORK=4096000,
#          JKEY=46,
#          JTMAX=10,
#          JTCLAS=64,
#          JTEL=255)

edits = {}
edits['JSUP']  = 9
edits['JSEC0'] = 3
edits['JSEC1'] = 40
edits['JSEC2'] = 4096
edits['JSEC3'] = 4
edits['JSEC4'] = 2
edits['JELEM'] = 320000
edits['JSUBS'] = 400
edits['JCVAL'] = 150
edits['JBUFL'] = 512000
edits['JBPW'] = 32
edits['JTAB'] = 3000
edits['JCTAB'] = 3000
edits['JCTST'] = 9000
edits['JCTEXT'] = 9000
edits['JWORK'] = 4096000
edits['JKEY'] = 46
edits['JTMAX'] = 10
edits['JTCLAS'] = 64
edits['JTEL'] = 255
#edits[''] = 

lines = open(signature_file).readlines()
fd = open(signature_file,"wt")
for l in lines:
    if 'dimension' in l:
        for e in edits.keys():
            txt = '('+e.lower()+')'
            value = edits[e]
            if txt in l:
                l=l.replace(txt,str(value))
    fd.write(l)
fd.close()
