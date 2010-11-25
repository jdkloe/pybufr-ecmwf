#!/usr/bin/env python

"""
a small tool to take the BUFR table definitions used by NCEP,
as published on their website, see
http://www.emc.ncep.noaa.gov/mmb/data_processing/...
      NCEP_BUFR_File_Structure.htm#ASCII_Table
and convert it to BUFR Tables formatted such that the ECMWF library
can use them.
"""

import os, urllib

ascii_source_table_url = 'http://www.emc.ncep.noaa.gov/mmb/data_processing/'+\
                         'NCEP_BUFR_File_Structure.htm'
local_copy = './local_copy_NCEP_ASCII_BUFR_TABLE.txt'
ncep_table_b = 'NCEP_table_B.txt'

def remove_tags(txt):
    # assume tags are not broken into multiple lines
    clean_txt = []
    inside_tag = False
    for c in txt:
        if c=='<':
            inside_tag = True
        elif c=='>':
            inside_tag = False
        else:
            if not inside_tag:
                clean_txt.append(c)

    return ''.join(c for c in clean_txt)

if not os.path.exists(local_copy):
    try:
        html_fd = urllib.urlopen(ascii_source_table_url)
        html_data = html_fd.read()
        html_fd.close()
    except IOError:
        print 'Sorry, download of NCEP ASCII BUFR tables html page failed'
        print 'Please try again later.'
        sys.exit(1)

    # at this point we have one chunck of text in a string,
    # not splitted into lines
    print 'html_data contains ',len(html_data),' bytes'
    fd = open(local_copy,'w')
    fd.write(html_data)
    fd.close()

# read (again) into a list of lines
html_data = open(local_copy).readlines()

print 'html_data contains ',len(html_data),' bytes'
print 'type(html_data) = ',type(html_data)
print 'type(html_data[0]) = ',type(html_data[0])
print 'html_data[0:5] = ',html_data[0:5]

table_start_found = False
table_lines = []
for l in html_data:
    if 'Lines containing Table D' in l:
        table_start_found = True
    if table_start_found:
        table_lines.append(l)

print 'html BUFR table contains ',len(table_lines),' lines'

all_lines_as_text = ''.join(l.strip() for l in table_lines)
new_lines = all_lines_as_text.split('</p>')
cleaned_table_lines = []
for l in new_lines:
    cleaned_table_line = remove_tags(l)
    cl_line = cleaned_table_line.replace('&nbsp;',' ')
    cl_line = cl_line.replace('&lt;','<')
    cl_line = cl_line.replace('&gt;','>')
    cleaned_table_lines.append(cl_line)

# now extract the actual data

mnemonic_defs   = {} # definition of symbols (mnemonics)
sequence_defs   = {} # this corresponds to Table D
descriptor_defs = {} # this corresponds to Table B

in_mnemonic_defs   = False
in_sequence_defs   = False
in_descriptor_defs = False
for l in cleaned_table_lines:
    if ('MNEMONIC' in l) and ('NUMBER' in l) and ('DESCRIPTION' in l):
        in_mnemonic_defs   = True
        in_sequence_defs   = False
        in_descriptor_defs = False
    if ('MNEMONIC' in l) and ('SEQUENCE' in l):
        in_mnemonic_defs   = False
        in_sequence_defs   = True
        in_descriptor_defs = False
    if ('MNEMONIC' in l) and ('SCAL' in l) and ('REFERENCE' in l):
        in_mnemonic_defs   = False
        in_sequence_defs   = False
        in_descriptor_defs = True

    parts = l.split('|')
    if in_mnemonic_defs:
        if len(parts)>4:
            mnemonic    = parts[1].strip()
            number      = parts[2].strip()
            description = parts[3].strip()
            if ( (mnemonic != '') and
                 (mnemonic != 'MNEMONIC') and
                 (mnemonic != '----------') ):
                mnemonic_defs[mnemonic] =(number,description)
    if in_sequence_defs:
        if len(parts)>3:
            mnemonic = parts[1].strip()
            sequence = ' '.join(w for w in parts[2].split())
            defs = sequence_defs.get(mnemonic,'')+' '+sequence
            if ( (mnemonic != '') and
                 (mnemonic != 'MNEMONIC') and
                 (mnemonic != '----------') ):
                sequence_defs[mnemonic] = defs.strip()
    if in_descriptor_defs:
        if len(parts)>7:
            # MNEMONIC | SCAL | REFERENCE   | BIT | UNITS
            mnemonic    = parts[1].strip()
            scale       = parts[2].strip()
            reference   = parts[3].strip()
            numbits     = parts[4].strip()
            unit        = parts[5].strip()
            if ( (mnemonic != '') and
                 (mnemonic != 'MNEMONIC') and
                 (mnemonic != '----------') ):
                descriptor_defs[mnemonic] = (scale, reference, numbits, unit)

#print 'mnemonic_defs:'
#for (key,data) in mnemonic_defs.items():
#    print key+'[%s][%s]' % data

#print 'sequence_defs:'
#for (key,data) in sequence_defs.items():
#    print key+'[%s]' % data

print 'descriptor_defs:'
for (mnemonic,data) in descriptor_defs.items():
    print mnemonic+'[%s][%s][%s][%s]' % data,
    print mnemonic_defs[mnemonic]

# now construct table B
table_b_lines = []
for (mnemonic,data) in descriptor_defs.items():
    (scale, reference, numbits, unit) = data
    (descriptor, name) = mnemonic_defs[mnemonic]

    # for string formatting see:
    # http://docs.python.org/library/string.html#formatstrings
    line = '{:>7} {:<64}{:<24}{:>4}{:>14}{:>4}'.format(\
           descriptor,name,unit,scale,reference,numbits)
    table_b_lines.append(line)

table_b_lines.sort()
# print '\n'.join(l for l in table_b_lines)

fd = open(ncep_table_b,'w')
for l in table_b_lines:
    fd.write(l+'\n')
fd.close()

    
