#!/usr/bin/env python

# start with the idea: everything is an object ...

descriptor-object
  ==>descriptor-code (table reference)
  ==>descriptive text (element name)
  ==>unit text (element unit)
  ==>offset (reference value)
  ==>num bits (data width)
  ==>etc.

replication-object(descriptor-object):
  ==>replication-count
  ==>list-of-descriptor-objects = []

delayed-replication-object(descriptor-object):
  ==>maximum-replication-count = 4
  ==>actual-replication-count-list ] [1,2,3,4]
  ==>list-of-descriptor-objects = []

composite-descriptor-object(descriptor-object): [table D entry]
  ==>descriptor code
  ==>list-of-descriptor-objects = []

bufr-table
  ==>table-B = [list of desciptor-objects]
  ==>table-D = [list of composite-descriptor-objects]
  methods:
  ==>read-tables
  ==>write-tables

data-object
  ==>value or string-value
  ==>already filled or not?
  ==>pointer to the associated descriptor object

bufr-msg
  ==>properties-list = [sec0,sec1,sec2,sec3 data]
  ==>list-of-descriptor-objects = []
  ==>finish (set num subsets, num delayed replications)
  ==>2D-data-array of data objects (num subsets x expanded num descriptors)
  
