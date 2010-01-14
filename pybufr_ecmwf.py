#!/usr/bin/env python

#  #[ documentation
# This module implements a python interface around the BUFR library provided by
# ECMWF to allow reading and writing the WMO BUFR file standard.
# For now, this is only a reference implementatio intended to demonstrate how
# this could be done.
#
# For more on information ECMWF see: http://www.ecmwf.int/
# For more information on the BUFR library software provided
# by ECMWF see: http://www.ecmwf.int/products/data/software/download/bufr.html
#
# Note about the use of the "#  #[" and "#  #]" comments:
#   these are folding marks for my favorite editor, emacs, combined with its
#   folding mode
#   (see http://www.emacswiki.org/emacs/FoldingMode for more details)
# Please do not remove them.
#
# This module was written by: Jos de Kloe, KNMI, and may be redistributed
# for now under the terms of the GPL v.2.
#
# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI, Initial version 12-Nov-2009    
# 
#  #]
#  #[ imported modules
import os         # operating system functions
import sys        # system functions
import re         # regular expression handling
import glob       # allow for filename expansion
#import gzip # handle gzipped files [currently not used]
import tarfile    # handle tar archives
import subprocess # support running additional executables
import shutil     # portable file copying functions
import time       # handling of date and time
#  #]
#  #[ exception definitions
# see: http://docs.python.org/library/exceptions.html
# for a list of already available exceptions.
# are:     IOError, EOFError
class NotYetImplementedError(NotImplementedError): pass
class ProgrammingError(Exception): pass
class NetworkError(Exception): pass
class LibraryBuildError(Exception): pass
class InterfaceBuildError(Exception): pass
#  #]

class BUFRInterface:
    #  #[
    # could contain common code for bufr_interface_ecmwf
    # and the bufr module written by Guilherme Castelao
    def __init__(self,verbose=False):
        self.verbose = verbose
    #  #]
class BUFRInterfaceECMWF(BUFRInterface):
    #  #[
    def __init__(self,verbose=False,
                 preferred_fortran_compiler=None,
                 preferred_c_compiler=None,
                 fortran_compiler=None,
                 fortran_ld_library_path=None,
                 fortran_flags=None,
                 c_compiler=None,
                 c_ld_library_path=None,
                 c_flags=None,
                 debug_f2py_c_api=False):
        #  #[

        self.preferred_fortran_compiler = preferred_fortran_compiler
        self.preferred_c_compiler       = preferred_c_compiler
        self.fortran_compiler           = fortran_compiler
        self.fortran_ld_library_path    = fortran_ld_library_path
        self.c_compiler                 = c_compiler
        self.c_ld_library_path          = c_ld_library_path
        self.fortran_flags              = fortran_flags
        self.c_flags                    = c_flags

        # call the init of the parent class
        BUFRInterface.__init__(self,verbose)
        # for now, this is equivalent to:
        #self.verbose = verbose

        self.ecmwf_bufr_lib_dir  = "./ecmwf_bufr_lib"

        # check for the presence of the library
        bufr_lib_file = "libbufr.a"
        if (os.path.exists(bufr_lib_file)):
            pass
            #print "library seems present"
        else:
            print "Entering installation sequence:"
            self.install()

        self.wrapper_name = "ecmwfbufr.so"
        if (os.path.exists(self.wrapper_name)):
            #print "python wrapper seems already present"
            return
        else:
            print "Entering wrapper generation sequence:"
            (source_dir,tarfile_to_install) = self.get_source_dir()
            self.generate_python_wrapper(source_dir,debug_f2py_c_api)

        #  #]
    def download_library(self):
        #  #[
        url_bufr_page     = "http://www.ecmwf.int/products/data/"+\
                            "software/download/bufr.html"
        url_ecmwf_website = "http://www.ecmwf.int/"

        os.makedirs(self.ecmwf_bufr_lib_dir)

        import urllib

        if (self.verbose):
            print "setting up connection to ECMWF website"
        try:
            # Get a file-like object for this website
            f = urllib.urlopen(url_bufr_page)
        except:
            print "connection failed......"
            print "could not open url: ",url_bufr_page
            raise NetworkError

        # Read from the object, storing the page's contents in a list of lines
        lines = f.readlines()
        f.close()
        if (self.verbose):
            print "ECMWF download page retrieved successfully"
        
        # a test print of the html of this webpage
        #print "data:",s

        # do a simple parsing to retrieve the currently available
        # BUFR library versions and their URLs for download:

        # a little test to see how this regular expression grouping works:
        # (to be executed manually on the python prompt)
        # >import re
        # >x="abc 123 def 456 ghi"
        # >print re.match('.*(123).*(456).*',x).groups()
        # The output you get is:
        # ('123', '456')
        
        # the lines we are interested in have this format:
        # <TD WIDTH="37%"><A HREF="SOMEPATH/bufr_VERSION.tar.gz" class="sowtware">bufr_VERSION.tar.gz</A>DATE</TD>
        # so use this regular expression to parse these lines:
        line_pattern = r'<TD .*><A HREF="(.*)" .*>(.*)</A>(.*)</TD>'

        bufr_lib_versions = []
        for l in lines:
            if (".tar.gz" in l):
                #print l
                match_object = re.match(line_pattern,l)
                if (match_object):
                    data = match_object.groups()
                    #print data
                    bufr_lib_versions.append(data)

        # find most recent library version, for now just sort on name
        # that should do the trick
        most_recent_bufr_lib_url       = ""
        most_recent_bufr_tarfile_name  = ""
        most_recent_bufr_lib_date      = ""
        for data in bufr_lib_versions:
            bufr_lib_url      = data[0] # example: '/products/data/software/download/software_files/bufr_000380.tar.gz'
            bufr_tarfile_name = data[1] # example: 'bufr_000380.tar.gz'
            bufr_lib_date     = data[2] # example: ' 28.07.2009'
            if (bufr_tarfile_name > most_recent_bufr_tarfile_name):
                # store
                most_recent_bufr_lib_url      = bufr_lib_url
                most_recent_bufr_tarfile_name = bufr_tarfile_name
                most_recent_bufr_lib_date     = bufr_lib_date

        # report the result
        if (self.verbose):
            print "Most recent library version seems to be: ",
            most_recent_bufr_tarfile_name
        download_url = url_ecmwf_website+most_recent_bufr_lib_url

        if (self.verbose):
            print "trying to dowdload: ",most_recent_bufr_tarfile_name
        try:
            # Get a file-like object for this website
            f = urllib.urlopen(download_url)
        except:
            print "connection failed......"
            print "could not open url: ",download_url
            raise NetworkError
        
        tarfiledata = f.read()
        f.close()
        if (self.verbose):
            print "ECMWF download page retrieved successfully"
        
        local_fullname = os.path.join(self.ecmwf_bufr_lib_dir,
                                      most_recent_bufr_tarfile_name)
        fd = open(local_fullname,'wb')
        fd.write(tarfiledata)
        fd.close()

        if (self.verbose):
            print "created local copy of: ",most_recent_bufr_tarfile_name
        #  #]
    def get_source_dir(self):
        #  #[
        list_of_bufr_tarfiles = glob.glob(os.path.join(self.ecmwf_bufr_lib_dir,
                                                       "*.tar.gz"))

        # safety catch
        if (len(list_of_bufr_tarfiles)==0):
            return (None,None)

        # sort in reverse alphabetical order to get the newest one on top
        list_of_bufr_tarfiles.sort(reverse=True)
        if (self.verbose):
            print "available library tarfiles: ",list_of_bufr_tarfiles
            print "most recent library tarfile: ",list_of_bufr_tarfiles[0]

        (path,tarfile_to_install) = os.path.split(list_of_bufr_tarfiles[0])
        
        # find out the actual name of the library source directory
        # after unpacking. Use the tarfile module and look inside:
        tarfile_obj = tarfile.open(list_of_bufr_tarfiles[0],'r:gz')
        names = tarfile_obj.getnames()
        #print "names[0:5] = ",names[0:5]
        # this library holds everything in a single subdirectory named something
        # like bufr_000380, so I guess it is safe to assume that the first name
        # in the archive will be the name of this directory.
        bufr_dir = names[0]
        tarfile_obj.close()

        source_dir = os.path.join(self.ecmwf_bufr_lib_dir,bufr_dir)

        return (source_dir,tarfile_to_install)
        #  #]
    def install(self):
        #  #[

        #  #[ download and unpack the ECMWF BUFR library tar file
        (source_dir,tarfile_to_install) = self.get_source_dir()
        if (source_dir == None):
            self.download_library()
            # retry (hopefully we have a copy of the tarfile now)
            (source_dir,tarfile_to_install) = self.get_source_dir()
            
        if (not os.path.exists(source_dir)):

            # safety catch
            if (tarfile_to_install == None):
                print "ERROR: no tarfile available for BUFR library."
                print "Maybe the automatic download failed?"
                print "If you try to install without internet connection you"
                print "have to manually create a directory named ecmwf_bufr_lib"
                print "and place a copy of a recent ECMWF BUFR library tarfile"
                print "in it before running the pybufr_ecmwf.py command."
                raise NetworkError

            cmd = "cd "+self.ecmwf_bufr_lib_dir+";tar zxvf "+tarfile_to_install
            print "Executing command: ",cmd
            os.system(cmd)
        else:
            print "path exists: ",source_dir
            print "assuming the package is already unpacked..."
        #  #]

        #  #[ find a suitable fortran and c compiler to use
        # the first one found will be used, unless a preferred one is specified.
        self.custom_fc_present = self.check_presence(self.fortran_compiler)
        self.g95_present       = self.check_presence("g95")
        self.gfortran_present  = self.check_presence("gfortran")
        self.g77_present       = self.check_presence("g77")
        self.f90_present       = self.check_presence("f90")
        self.f77_present       = self.check_presence("f77")

        self.use_custom_fc = False
        self.use_g95       = False
        self.use_gfortran  = False
        self.use_g77       = False
        self.use_f90       = False
        self.use_f77       = False

        fortran_compiler_selected = False
        if (self.preferred_fortran_compiler != None):
            implementedfortran_compilers = ["custom","g95","gfortran",
                                            "g77","f90","f77"]
            if not (self.preferred_fortran_compiler in
                    implementedfortran_compilers):
                print "ERROR: unknown preferred fortran compiler specified."
                print "valid options are: ",\
                      ", ".join(s for s in implementedfortran_compilers)
                raise NotYetImplementedError
                
            if (self.preferred_fortran_compiler == "custom"):
                if (self.custom_fc_present):
                    self.use_custom_fc = True
                    fortran_compiler_selected = True
            elif (self.preferred_fortran_compiler == "g95"):
                if (self.g95_present):
                    self.use_g95 = True
                    fortran_compiler_selected = True
            elif (self.preferred_fortran_compiler == "gfortran"):
                if (self.gfortran_present):
                    self.use_gfortran = True
                    fortran_compiler_selected = True
            elif (self.preferred_fortran_compiler == "g77"):
                if (self.g77_present):
                    self.use_g77 = True
                    fortran_compiler_selected = True
            elif (self.preferred_fortran_compiler == "f90"):
                if (self.f90_present):
                    self.use_f90 = True
                    fortran_compiler_selected = True
            elif (self.preferred_fortran_compiler == "f77"):
                if (self.f77_present):
                    self.use_f77 = True
                    fortran_compiler_selected = True
            else:
                print "Warning: this line should never be reached."
                print "check the list of available fortran compilers,"
                print "it seems not consistent."
                print "Please report this bug if you encounter it"
                print "ERROR in BUFRInterfaceECMWF.install()"
                raise ProgrammingError
                
            if (not fortran_compiler_selected):
                print "preferred fortran compiler ["+\
                      self.preferred_fortran_compiler+"] seems not available..."
                print "falling back to default fortran compiler"
                raise UserWarning
            
        if (not fortran_compiler_selected):
            if (self.custom_fc_present):
                self.use_custom_fc = True
                fortran_compiler_selected = True
            elif (self.g95_present):
                self.use_g95 = True
                fortran_compiler_selected = True
            elif (self.gfortran_present):
                self.use_gfortran = True
                fortran_compiler_selected = True
            elif (self.g77_present):
                self.use_g77 = True
                fortran_compiler_selected = True
            elif (self.f90_present):
                self.use_f90 = True
                fortran_compiler_selected = True
            elif (self.f77_present):
                self.use_f77 = True
                fortran_compiler_selected = True


        if (not fortran_compiler_selected):
            print "ERROR: no valid fortran compiler found,"
            print "installation is not possible"
            print "Please install a fortran compiler first."
            print "Good options are the free GNU compilers"
            print "gfortran and g95 which may be downloaded free of charge."
            print "(see: http://gcc.gnu.org/fortran/  "
            print " and: http://www.g95.org/         )"
            raise EnvironmentError

        self.custom_cc_present = self.check_presence(self.c_compiler)
        self.gcc_present       = self.check_presence("gcc")
        self.cc_present        = self.check_presence("cc")

        self.use_custom_cc = False
        self.use_gcc       = False
        self.use_cc        = False
        
        c_compiler_selected = False
        if (self.preferred_c_compiler !=None):
            implementedc_compilers = ["custom","gcc","cc"]
            if not (self.preferred_c_compiler in implementedc_compilers):
                print "ERROR: unknown preferred c compiler specified."
                print "valid options are: ",\
                      ", ".join(s for s in implementedc_compilers)
                raise NotYetImplementedError

            if (self.preferred_c_compiler == "custom"):
                if (self.custom_cc_present):
                    self.use_custom_cc = True
                    c_compiler_selected = True
            elif (self.preferred_c_compiler == "gcc"):
                if (self.gcc_present):
                    self.use_gcc = True
                    c_compiler_selected = True
            elif (self.preferred_c_compiler == "cc"):
                if (self.cc_present):
                    self.use_cc = True
                    c_compiler_selected = True
            else:
                print "Warning: this line should never be reached."
                print "check the list of available c compilers,"
                print "it seems not consistent."
                print "Please report this bug if you encounter it"
                print "ERROR in BUFRInterfaceECMWF.install()"
                raise ProgrammingError
                
            if (not c_compiler_selected):
                print "preferred c compiler ["+\
                      self.preferred_c_compiler+"] seems not available..."
                print "falling back to default c compiler"

        if (not c_compiler_selected):
            if (self.custom_cc_present):
                self.use_custom_cc = True
                c_compiler_selected = True
            elif (self.gcc_present):
                self.use_gcc = True
                c_compiler_selected = True
            elif (self.cc_present):
                self.use_cc = True
                c_compiler_selected = True

        if (not c_compiler_selected):
            print "ERROR: no valid c compiler found, installation is"
            print "not possible. Please install a c compiler first."
            print "A good options is the free GNU compiler gcc"
            print "which may be downloaded free of charge."
            print "(see: http://gcc.gnu.org/ )"
            raise EnvironmentError

        if (self.verbose):
            print "custom_fc_present = ",self.custom_fc_present,\
                  " use_custom_fc = ",self.use_custom_fc
            print "g95_present       = ",self.g95_present,\
                  " use_g95       = ",self.use_g95
            print "gfortran_present  = ",self.gfortran_present,\
                  " use_gfortran  = ",self.use_gfortran
            print "g77_present       = ",self.g77_present,\
                  " use_g77       = ",self.use_g77
            print "f90_present       = ",self.f90_present,\
                  " use_f90       = ",self.use_f90
            print "f77_present       = ",self.f77_present,\
                  " use_f77       = ",self.use_f77

            print "custom_cc_present = ",self.custom_cc_present,\
                  " use_custom_cc = ",self.use_custom_cc
            print "gcc_present       = ",self.gcc_present,\
                  " use_gcc       = ",self.use_gcc
            print "cc_present        = ",self.cc_present,\
                  " use_cc        = ",self.use_cc
            
        #  #]
        
        #  #[ add the custom LD_LIBRARY_PATH settings
        libpath = ""
        if (self.fortran_ld_library_path != None):
            libpath = ";".join(s for s in
                               [libpath,self.fortran_ld_library_path]
                               if (s != ""))
        if (self.c_ld_library_path != None):
            libpath = ";".join(s for s in
                               [libpath,self.c_ld_library_path]
                               if (s != ""))

        if (libpath != ""):
            print "Using LD_LIBRARY_PATH setting: ",libpath
        #  #]

        #  #[ generate a config file for compilation of the BUFR library
        
        #----------------------------------------------------------------------#
        # Possible commands to the make command for the BUFR library, in case  #
        # you wish to use the config files from the ECMWF software package     #
        # are: (see the README file within source_dir)                         #
        # - architecture: ARCH=sgimips (or: decalpha,hppa,linux,rs6000,sun4)   #
        # - 64 bit machine: R64=R64                                            #
        # - compiler name (only for linux or sun machines): CNAME=_gnu         #
        #                                                                      #
        #----------------------------------------------------------------------#

        # NOTE that for the linux case the library has some hardcoded switches
        # to use 32-bit variables in its interfacing (at least last time I
        # looked), so DO NOT try to use the 64 bit option on linux, even if
        # you have a 64-bit processor and compiler available !
        # Even if the code runs, it will fail miserably and cause segmentation
        # faults if you are lucky, or just plain nonsense if you are out of
        # luck ....

        # these 4 settings determine the name of the config file used by the
        # Make command; look in ecmwf_bufr_lib/bufr_000380/config/ to see all
        # available versions.
        #ARCH="linux"
        #CNAME="_compiler"
        #R64="" 
        #A64=""
        
        # note: usefull free compilers for linux that you can use are:
        # (at least for these config files are provided in the ECMWF BUFR
        #  package)
        # g77      : CNAME="_gnu"
        # g95      : CNAME="_g95"
        # gfortran : CNAME="_gfortran"

        # Notes on compiler switches:

        # for most compilers you should force the BUFR library to use 4 byte
        # integers as default integer. Do this by adding the "-i4" option.
        # This works for most compilers, with gfortran as known exception 
        # (that one has this setting as default and does not have a commandline
        #  option to set it)

        # is seems the c compiler step needs the "-DFOPEN64" switch to be set
        # (at least it is present in most config files in the package) but it is
        # never used in the source code itself, so I guess it is obsolete.

        if (self.use_custom_fc):
            fc = self.fortran_compiler
            # Default compiler switches
            fflags = "-O -Dlinux"
            # add any custom flags given by the user
            if (self.fortran_flags != None):
                fflags = fflags + ' ' + self.fortran_flags
        elif (self.use_g95):
            fc = "g95"
            # Default compiler switches
            fflags = "-O -Dlinux"
            # additional g95 specific switches
            fflags = fflags+" -i4"
            fflags = fflags+" -fno-second-underscore"
            fflags = fflags+" -r8"
            fflags = fflags+" -fPIC"
            #cname="_g95"
        elif (self.use_gfortran):
            fc = "gfortran"
            # Default compiler switches
            fflags = "-O -Dlinux"
            # additional gfortran specific switches
            fflags = fflags+" -fno-second-underscore"
            fflags = fflags+" -fPIC"
            #fflags=fflags" -fdefault-integer-4"
            # an explicit 4-byte default integer options seems not to exists
            # for gfortran, so lets just hope that is the default ...
            #cname="_gfortran"
        elif (self.use_g77):
            fc = "g77"
            # Default compiler switches
            fflags = "-O -Dlinux"
            fflags = fflags+" -i4"
            #cname="_gnu"
        elif (self.use_f90):
            # this catches installations that have some commercial fortran
            # installed, which usually are symlinked to the name
            # f90 for convenience
            fc = "f90"
            # Default compiler switches
            fflags = "-O -Dlinux"
            fflags = fflags+" -i4"
            #cname="_???"
        elif (self.use_f77):
            # this catches installations that have some commercial fortran
            # installed, which usually are symlinked to the name
            # f77 for convenience
            fc = "f77"
            # Default compiler switches
            fflags = "-O -Dlinux"
            fflags = fflags+" -i4"
            #cname="_???"
        else:
            print "ERROR in bufr_interface_ecmwf.install:"
            print "No suitable fortran compiler found"
            raise EnvironmentError

        if (self.use_custom_cc):
            cc=self.c_compiler
            cflags = "-fPIC"
            # add any custom flags given by the user
            if (self.c_flags != None):
                cflags = cflags+' '+self.c_flags
        elif (self.use_gcc):
            cc="gcc"
            # Default compiler switches
            cflags = "-fPIC"
        elif (self.use_cc):
            # this catches installations that have some commercial c-compiler
            # installed, which usually are symlinked to the name
            # cc for convenience
            cc="cc"
            # Default compiler switches
            cflags = "-fPIC"
        else:
            print "ERROR in bufr_interface_ecmwf.install:"
            print "No suitable c compiler found"
            raise EnvironmentError

        # no check implemented on the "ar" and "ranlib" commands yet
        # (easy to add if we woould need it)

        # a command to generate an archive (*.a) file
        ar="ar"
        # a command to generate an index of an archive file
        rl = "/usr/bin/ranlib"

        # Unfortunately, the config files supplied with this library seem
        # somewhat outdated and sometimes incorrect, or incompatible with
        # the current compiler version (since they seem based on some
        # older compiler version, used some time ago at ECMWF, and never
        # got updated). This especially is true for the g95 compiler.
        # Therefore we have decided (at KNMI) to create our own
        # custom config file in stead.
        # We just call it: config.linux_compiler
        # which seems safe for now, since ECMWF doesn't use that name.
        
        arch  = "linux"
        cname = "_compiler"
        r64   = "" 
        a64   = ""

        # construct the name of the config file to be used
        config_file = "config."+arch+cname+r64+a64
        fullname_config_file = os.path.join(source_dir,"config",config_file)

        # this check is only usefull if you use one of the existing config files
        #if not os.path.exists(fullname_config_file):
        #    # see if a version with ".in" extension is present
        #    # and if so, symlink to it.
        #    if not os.path.exists(fullname_config_file+".in"):
        #        print "ERROR: config file not found: ",fullname_config_file
        #        raise IOError
        #    else:
        #        os.symlink(config_file+".in",fullname_config_file)

        # create our custom config file:
        print "Using: "+fc+" as fortran compiler"
        print "Using: "+cc+" as c compiler"

        print "Creating ECMWF-BUFR config file: ",fullname_config_file
        fd = open(fullname_config_file,'wt')
        fd.write("#   Generic configuration file for linux.\n")
        fd.write("AR         = "+ar+"\n")
        fd.write("ARFLAGS    = rv\n")
        fd.write("CC         = "+cc+"\n")
        fd.write("CFLAGS     = -O "+cflags+"\n")
        fd.write("FASTCFLAGS = "+cflags+"\n")
        fd.write("FC         = "+fc+"\n")
        fd.write("FFLAGS     = "+fflags+"\n")
        fd.write("VECTFFLAGS = "+fflags+"\n")
        fd.write("RANLIB     = "+rl+"\n")
        fd.close()
        
        # create a backup copy in the ecmwf_bufr_lib_dir
        source      = fullname_config_file
        destination = os.path.join(self.ecmwf_bufr_lib_dir,"config_file")
        shutil.copyfile(source,destination)
        #  #]
        
        #  #[ compile little pieces of Fortran and c to test the compilers
        self.fortran_compile_test(fc,fflags,libpath)
        self.c_compile_test(cc,cflags,libpath)
        #  #]
        
        #  #[ now use the make command to build the library

        # construct the compilation command:
        cmd = "cd "+source_dir+";make ARCH="+arch+" CNAME="+\
              cname+" R64="+r64+" A64="+a64

        # now issue the Make command
        if (libpath == ""):
            print "Executing command: ",cmd
            os.system(cmd)
            #(lines_stdout,lines_stderr) = self.__RunShellCommand__(cmd)
            #self.__RunShellCommand__(cmd,catch_output=False)
        else:
            #(lines_stdout,lines_stderr) = \
            #         self.__RunShellCommand__(cmd,libpath=libpath)
            self.__RunShellCommand__(cmd,libpath=libpath,catch_output=False)
        #  #]

        #  #[ check the result
        bufr_lib_file = "libbufr.a"
        fullname_bufr_lib_file = os.path.join(source_dir,bufr_lib_file)
        if (os.path.exists(fullname_bufr_lib_file)):
            print "Build seems successfull"
            # remove any old symlink that might be present
            if (os.path.exists(bufr_lib_file)):
                os.remove(bufr_lib_file)
            # make a symlink in a more convenient location
            os.symlink(fullname_bufr_lib_file,bufr_lib_file)
        else:
            print "ERROR in bufr_interface_ecmwf.install:"
            print "No libbufr.a file seems generated."
            raise LibraryBuildError
        #  #]

        #  #[ some old notes
        
        # save the settings for later use
        #self.make_settings = (arch,cname,r64,a64)
        #self.compilers     = (fc,fflags,cc,cflags)
        #self.tools         = (ar,rl)

        # actually, this saving of settings is not the way I would
        # prefer doing this. I think it is better to keep the 2 stages
        # (installation of the BUFR library, and generation of the
        #  python interface shared object) as separate as possible.
        # This allows rerunning generation of the python interface
        # without rerunning the installation of the BUFR library
        # (which will at least save a lot of time during development)
        #
        # So the generate_python_wrapper routine should just
        # read the config file generated above, and not use these
        # settings in self, that might not always be defined.
        #  #]
        
        #  #]
    def run_shell_command(self,cmd,libpath=None,catch_output=True):
        #  #[
        # get the list of already defined env settings
        e = os.environ
        if (libpath):
            # add the additional env setting
            envname = "LD_LIBRARY_PATH"
            if (e.has_key(envname)):
                e[envname] = e[envname] + ";" + libpath
            else:
                e[envname] = libpath
                
                
        print "Executing command: ",cmd
        if (catch_output):
            subpr = subprocess.Popen(cmd,
                                     shell=True,
                                     env=e,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            
            # wait until the child process is done
            #subpr.wait() # seems not necessary when catching stdout and stderr
            
            lines_stdout = subpr.stdout.readlines()
            lines_stderr = subpr.stderr.readlines()
            
            #print "lines_stdout: ",lines_stdout
            #print "lines_stderr: ",lines_stderr
            
            return (lines_stdout,lines_stderr)

        else:
            subpr = subprocess.Popen(cmd, shell=True, env=e)

            # wait until the child process is done
            subpr.wait()
            return
        #  #]
    def check_presence(self,command):
        #  #[
        if (self.verbose):
            print "checking for presence of command: "+str(command)
        
        result = []

        if (command == None):
            return False
        
        # get the real command, in case it was an alias
        cmd = "which "+command
        (lines_stdout,lines_stderr) = \
                    self.run_shell_command(cmd,catch_output=True)

        if (len(lines_stdout)==0):
            # command is not present in default path
            return False
        else:
            # command is present in default path
            return True
        #  #]
    def fortran_compile_test(self,fc,fflags,libpath):
        #  #[
        # Note: for now the flags are not used in these test because these
        # are specific for generating a shared-object file, and will fail to
        # generate a simple executable for testing

        fortran_test_code = \
"""
program pybufr_test_program

  print *,'Hello pybufr module:'
  print *,'Fortran compilation seems to work fine ...'

end program pybufr_test_program
"""

        # generate a testfile with a few lines of Fortran90 code
        fortran_test_executable = "pybufr_fortran_test_program"
        fortran_test_file       = fortran_test_executable+".F90"
        fd = open(fortran_test_file,'wt')
        fd.write(fortran_test_code)
        fd.close()

        # contruct the compile command
        #cmd = fc+' '+fflags+' -o '+fortran_test_executable+' '+\
        #      fortran_test_file
        cmd = fc+' -o '+fortran_test_executable+' '+fortran_test_file
        
         # now issue the compile command
        if (libpath == ""):
            print "Executing command: ",cmd
            os.system(cmd)
        else:
            self.run_shell_command(cmd,libpath=libpath,catch_output=False)

        # now execute the just generated test program to verify if we succeeded
        cmd = fortran_test_executable
        if (libpath == ""):
            (lines_stdout,lines_stderr) = self.run_shell_command(cmd)
        else:
            (lines_stdout,lines_stderr) = \
                          self.run_shell_command(cmd,libpath=libpath)

        expected_output = [' Hello pybufr module:\n',
                           ' Fortran compilation seems to work fine ...\n']
        if ( (expected_output[0] not in lines_stdout) or
             (expected_output[1] not in lines_stdout)   ):
            print "ERROR: Fortran compilation test failed; "+\
                  "something seems very wrong"
            print "Expected output: ",expected_output
            print 'actual output stdout = ',lines_stdout
            print 'actual output stderr = ',lines_stderr
            raise EnvironmentError

        print "Fortran compilation test successfull..."

        # clean up
        os.remove(fortran_test_executable)
        os.remove(fortran_test_file)
        
        #  #]
    def c_compile_test(self,cc,cflags,libpath):
        #  #[
        # Note: for now the flags are not used in these test because these
        # are specific for generating a shared-object file, and will fail to
        # generate a simple executable for testing

        c_test_code = \
r"""
#include <stdio.h>
int main()
{
  printf("Hello pybufr module:\n");
  printf("c compilation seems to work fine ...\n");
  return 0;
}
"""

        # generate a testfile with a few lines of Fortran90 code
        c_test_executable = "pybufr_c_test_program"
        c_test_file       = c_test_executable+".c"
        fd = open(c_test_file,'wt')
        fd.write(c_test_code)
        fd.close()

        # contruct the compile command
        #cmd = cc+' '+cflags+' -o '+c_test_executable+' '+c_test_file
        cmd = cc+' -o '+c_test_executable+' '+c_test_file
        
         # now issue the compile command
        if (libpath == ""):
            print "Executing command: ",cmd
            os.system(cmd)
        else:
            self.run_shell_command(cmd,libpath=libpath,catch_output=False)

        # now execute the just generated test program to verify if we succeeded
        cmd = c_test_executable
        if (libpath == ""):
            (lines_stdout,lines_stderr) = self.run_shell_command(cmd)
        else:
            (lines_stdout,lines_stderr) = \
                          self.run_shell_command(cmd,libpath=libpath)

        expected_output = ['Hello pybufr module:\n',
                           'c compilation seems to work fine ...\n']
        if ( (expected_output[0] not in lines_stdout) or
             (expected_output[1] not in lines_stdout)   ):
            print "ERROR: c compilation test failed; something seems very wrong"
            print "Expected output: ",expected_output
            print 'actual output stdout = ',lines_stdout
            print 'actual output stderr = ',lines_stderr
            raise EnvironmentError

        print "c compilation test successfull..."

        # clean up
        os.remove(c_test_executable)
        os.remove(c_test_file)
        #  #]
    def generate_python_wrapper(self,source_dir,debug_f2py_c_api=False):
        #  #[
        wrapper_build_dir   = "f2py_build"
        wrapper_module_name = "ecmwfbufr"
        signatures_filename = "signatures.pyf"

        #source_files = ["buxdes.F",
        #                "bufren.F",
        #                "bufrex.F",
        #                "btable.F",
        #                "get_name_unit.F",
        #                "bus012.F",
        #                "busel.F",
        #                "buprs0.F",
        #                "buprs1.F",
        #                "buprs2.F",
        #                "buprs3.F",
        #                "buukey.F",
        #                "bupkey.F",
        #                "buprq.F"]
        #source_file_list = ' '.join(os.path.join(source_dir,"bufrdc",f)
        #                            for f in source_files)
        # compilation of the wrapper seems to work when I use
        # this selected set of fortran files, but when I try to import the
        # module in python I get the following error (don't know yet why):
        #   >>> import ecmwfbufr
        #   Traceback (most recent call last):
        #     File "<stdin>", line 1, in <module>
        #   ImportError: ./ecmwfbufr.so:
        #   undefined symbol: _gfortran_concat_string
        #   >>> 

        # just take them all (this works for me)
        source_file_list = source_dir+"/bufrdc/*.F"

        # apply ld_library path settings
        libpath = ""
        if (self.fortran_ld_library_path != None):
            libpath = ";".join(s for s in
                               [libpath,self.fortran_ld_library_path]
                               if (s != ""))
        if (self.c_ld_library_path != None):
            libpath = ";".join(s for s in
                               [libpath,self.c_ld_library_path]
                               if (s != ""))

        if (libpath != ""):
            print "Using LD_LIBRARY_PATH setting: ",libpath

        # call f2py and create a signature file that defines the
        # interfacing to the fortran routines in this library
        cmd = "f2py --build-dir "+wrapper_build_dir+\
              " -m "+wrapper_module_name+\
              " -h "+signatures_filename+\
              " "+source_file_list

        if (libpath == ""):
            print "Executing command: ",cmd
            os.system(cmd)
            #(lines_stdout,lines_stderr) = \
            #       self.run_shell_command(cmd,catch_output=True)
        else:
            #(lines_stdout,lines_stderr) = \
            #       self.run_shell_command(cmd,libpath=libpath,
            #                              catch_output=True)
            self.run_shell_command(cmd,libpath=libpath,catch_output=False)
    
        # safety check: see if the signatures.pyf file really is created
        signatures_fullfilename = os.path.join(wrapper_build_dir,
                                               signatures_filename)
        if (not os.path.exists(signatures_fullfilename)):
            print "ERROR: build of python wrapper failed"
            print "the signatures file could not be found"
            raise InterfaceBuildError

        # open the config file used for building the ECMWF BUFR library
        config_file = os.path.join(self.ecmwf_bufr_lib_dir,"config_file")
        lines = open(config_file).readlines()

        # extract which fortran compiler is used
        fortran_compiler       = 'undefined'
        fortran_compiler_flags = 'undefined'
        for l in lines:
            parts=l.split('=')
            if (parts[0].strip()=="FC"):
                fortran_compiler = parts[1].strip()
            if (parts[0].strip()=="FFLAGS"):
                fortran_compiler_flags = parts[1].strip()

        # adapt the signature file
        # this is needed, since the wrapper generation fails to do a number
        # of file includes that are essential for the interface definition
        # To circumvent this, remove the not-properly defined constants
        # and replace them by their numerical values
        # (maybe there is a more clever way to do this in f2py, but I have
        #  not yet found another way ...)
        self.adapt_f2py_signature_file(signatures_fullfilename)

        # it might be usefull for debugging to include this option: --debug-capi
        debug_f2py_c_api_option = ""
        if (debug_f2py_c_api):
            debug_f2py_c_api_option = " --debug-capi "

        if (self.fortran_compiler != None):
            cmd = "f2py  --build-dir "+wrapper_build_dir+\
                  debug_f2py_c_api_option+\
                  " --f90exec="+fortran_compiler+\
                  " --f90flags='"+fortran_compiler_flags+"'"+\
                  " --f77flags='"+fortran_compiler_flags+"'"+\
                  " ./f2py_build/signatures.pyf -L./ -lbufr -c"
        else:
            # note: adding the fortran_compiler_flags manually like this
            # causes some of them to be included twice, but this doesn't hurt,
            # and is the only way I get the automatic compilation using the
            # g95 compiler going.
            # TODO: Maybe later I could sort out how to use the python f2py
            # module in stead of the executable, and clean-up the compiler
            # flags before starting the tool
            cmd = "f2py  --build-dir "+wrapper_build_dir+\
                  debug_f2py_c_api_option+\
                  " --f90flags='"+fortran_compiler_flags+"'"+\
                  " --f77flags='"+fortran_compiler_flags+"'"+\
                  " --fcompiler="+fortran_compiler+\
                  " ./f2py_build/signatures.pyf -L./ -lbufr -c"

        if (libpath == ""):
            print "Executing command: ",cmd
            os.system(cmd)
            #(lines_stdout,lines_stderr) = \
            #       self.run_shell_command(cmd,catch_output=False)
        else:
            #(lines_stdout,lines_stderr) = \
            #       self.run_shell_command(cmd,libpath=libpath,
            #                              catch_output=True)
            self.run_shell_command(cmd,libpath=libpath,catch_output=False)
            
        # finally, again check for the presence of the wrapper
        # to see if the build was successfull
        if (os.path.exists(self.wrapper_name)):
            print "a python wrapper to the ECMWF BUFR library has been generated"
            return
        else:
            print "ERROR: build of python wrapper failed"
            print "the compilation or linking stage failed"
            raise InterfaceBuildError

        #  #]
    def adapt_f2py_signature_file(self,signature_file):
        #  #[

        # NOTE: maybe this modification is not needed if I can get the file
        #       with the parameters included in an other way.
        #       Looking at the f2py manpage the option -include might do the
        #       trick but that one is depricated. In stead a usercode section
        #       should be used, but that again means modifying the signature
        #       file ...
        #       Also the --include_paths option might be related.
        # TODO: sort this out
        
        #signature_file = "f2py_build/signatures.pyf"

        # these values are defined in parameter.F 
        # PARAMETER(JSUP =   9,
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
        # edits[''] = 

        # read the file
        lines = open(signature_file).readlines()

        # create a backup copy, to allow manual inspection
        source      = signature_file
        destination = signature_file+".bak"
        shutil.copyfile(source,destination)
        
        print "Fixing array size definitions in signatures definition ..."
        fd = open(signature_file,"wt")
        inside_subroutine = False
        for l in lines:

            if ('end subroutine' in l):
                inside_subroutine = False
            elif ('subroutine' in l):
                inside_subroutine = True

            if (inside_subroutine):
                if (' ::' in l):
                    # Add the intent(inplace) switch to all subroutine
                    # parameters.
                    # This might not be very pretty, but otherwise all
                    # parameters are assigned the default, which is intent(in).
                    # Maybe the proper way would be to sort out for each routine
                    # in this library which parameters are intent(in) and
                    # which are intent(out), but this is a huge task (and
                    # should be done by ECMWF rather then by us I think...)
                    (part1,part2) = l.split(' ::')
                    l = part1+',intent(inplace) ::'+part2
                
            if 'dimension' in l:
                #print "adapting line: ",l
                for e in edits.keys():
                    txt = '('+e.lower()+')'
                    value = edits[e]
                    if txt in l:
                        l=l.replace(txt,str(value))
                #print "to           : ",l

            if (l.strip() == "end interface"):
                # NOTE: the pb interface routines are written in c, so f2py
                # will not automatically generate their signature. This next
                # subroutine call explicitely adds these signatures.
                self.insert_pb_interface_definition(fd)

            fd.write(l)
        fd.close()
        #  #]
    def insert_pb_interface_definition(self,fd):
        #  #[
        # note:
        # it seems I am doing something wrong here, since this interface
        # is not yet functional. When trying to execute ecmwfbufr.pbopen()
        # I get the not very helpfull error message:
        #   "SystemError: NULL result without error in PyObject_Call"
        # Anybody out there who has an idea how this can be solved?
        indentation = 8*' '
        lines_to_add = \
          ["subroutine pbopen(cFileUnit,BufrFileName,mode,bufr_error_flag)",
           #"   intent(c) pbopen"
           #"   intent(c)"
           "   integer*4,        intent(out) :: cFileUnit",
           "   character(len=*), intent(in)  :: BufrFileName",
           "   character(len=1), intent(in)  :: mode",
           "   integer*4,        intent(out) :: bufr_error_flag",
           "end subroutine pbopen",
           "subroutine pbclose(cFileUnit,bufr_error_flag)",
           "   integer*4,        intent(inplace) :: cFileUnit",
           "   integer*4,        intent(inplace) :: bufr_error_flag ",
           "end subroutine pbclose",
           "subroutine pbbufr(cFileUnit,Buffer,BufferSizeBytes,MsgSizeBytes,&",
           "                  bufr_error_flag)",
           "   integer*4,              intent(inplace) :: cFileUnit",
           "   integer*4,dimension(*), intent(inplace) :: Buffer",
           "   integer*4,              intent(inplace) :: BufferSizeBytes",
           "   integer*4,              intent(inplace) :: MsgSizeBytes",
           "   integer*4,              intent(inplace) :: bufr_error_flag ",
           "end subroutine pbbufr",
           "subroutine pbwrite(cFileUnit,Buffer,MsgSizeBytes,bufr_return_value)",
           "   integer*4,              intent(inplace) :: cFileUnit",
           "   integer*4,dimension(*), intent(inplace) :: Buffer",
           "   integer*4,              intent(inplace) :: MsgSizeBytes",
           "   integer*4,              intent(inplace) :: bufr_return_value",
           "end subroutine pbwrite"]

        print "Inserting hardcoded interface to pbbufr routines in "+\
              "signatures file ..."
        for l in lines_to_add:
            fd.write(indentation+l+'\n')
            
        #  #]
    def get_expected_ecmwf_bufr_table_names(self,center,subcenter,
                                            LocalVersion,MasterTableVersion,
                                            EditionNumber,MasterTableNumber):
        #  #[
        # some local parameters used for detection of the
        # BUFR tables naming convention (short, medium or long)
        testfile_short  = "B0000980000.TXT"
        # this format was introduced with bufr_000260
        testfile_medium = "B000000000980000.TXT"
        # this format was introduced with bufr_000270
        testfile_long   = "B0000000000098000000.TXT"

        # somne codes to define the conventions
        conv_undefined = -1
        conv_short     =  1
        conv_medium    =  2
        conv_long      =  3

        (source_dir,tarfile_to_install) = self.get_source_dir()
        ecmwf_bufr_tables_dir = os.path.join(source_dir,"bufrtables/")

        #-------------------------------------------------------------
        # see which BUFR tables naming convention is used (short/long)
        #-------------------------------------------------------------
        bufrtable_naming_convention = conv_undefined

        testfile = os.path.join(ecmwf_bufr_tables_dir,testfile_short)
        if (os.path.exists(testfile)):
            print "Using short BUFRtables naming convention ..."
            bufrtable_naming_convention = conv_short

        testfile = os.path.join(ecmwf_bufr_tables_dir,testfile_medium)
        if (os.path.exists(testfile)):
            print "Using medium length BUFRtables naming convention ..."
            bufrtable_naming_convention = conv_medium

        testfile = os.path.join(ecmwf_bufr_tables_dir,testfile_long)
        if (os.path.exists(testfile)):
            print "Using long BUFRtables naming convention ..."
            bufrtable_naming_convention = conv_long

        if (bufrtable_naming_convention == conv_undefined):
            print "Sorry, unable to detect which BufrTable naming convention"
            print "should be used. Assuming the short convention ....."
            bufrtable_naming_convention = conv_short

        copy_center            = center
        copy_subcenter         = subcenter
        copy_mastertablenumber = MasterTableNumber
    
        # exception: if version of local table is set to zero then
        # it is assumed in BUGBTS that a standard ECMWF table is used !
        if (LocalVersion == 0):
            copy_center    = 98 # ECMWF
            copy_subcenter = 0

        # initialise
        name_table_b = ''
        name_table_d = ''

        if   (bufrtable_naming_convention == conv_short):
            if (EditionNumber <= 2):
                table_format = "%2.2i%3.3i%2.2i%2.2i"
                copy_subcenter = 0
            else:
                # starting from edition 3 the originating center
                # has one digit more
                table_format = "%3.3i%3.3i%2.2i%2.2i"
            numeric_part = table_format % (copy_subcenter,copy_center,
                                           MasterTableVersion,LocalVersion)
            
        elif (bufrtable_naming_convention == conv_medium):
            table_format = "%3.3i%4.4i%4.4i%2.2i%2.2i"
            if (EditionNumber <= 2):
                copy_subcenter         = 0
                copy_mastertablenumber = 0
            numeric_part = table_format % (copy_mastertablenumber,
                                           copy_subcenter,copy_center,
                                           MasterTableVersion,LocalVersion)

        elif (bufrtable_naming_convention == conv_long):
            table_format = "%3.3i%5.5i%5.5i%3.3i%3.3i"
            if (EditionNumber <= 2):
                copy_subcenter         = 0
                copy_mastertablenumber = 0
            numeric_part = table_format % (copy_mastertablenumber,
                                           copy_subcenter,copy_center,
                                           MasterTableVersion,LocalVersion)

        name_table_b = 'B'+numeric_part
        name_table_d = 'D'+numeric_part

        # xx=KSEC1(3)  = kcenter
        # yy=KSEC1(15) = kMasterTableVersion
        # zz=KSEC1(08) = kLocalVersion
        # for bufr editions 1 and 2
        # ww=0
        # ss=0
        # for bufr editions 3 and 4
        # ww=KSEC1(16) = ksubcenter
        # ss=KSEC1(14) = kMasterTableNumber
        #
        # naming convention for BUFR tables:
        # [B/C/D]xxxxxyyzz
        # with   xxxxx = originating centre          (tbd%kcenter)
        #        yy    = version of mastertable used (tbd%kMasterTableVersion)
        #        zz    = version of local table used (tbd%kLocalVersion)
        #
        # for more details see also file: buetab.f
        # (which actually reads the BUFR tables)
        #
        # see also: bufrdc.f in SUBROUTINE BUGBTS()
        #
        #             BUFR EDITION 2 NAMING CONVENTION
        #
        #             BXXXXXYYZZ , CXXXXXYYZZ , DXXXXXYYZZ
        #
        #             B/C/D  - BUFR TABLE B/C/D
        #             XXXXX  - ORIGINATING CENTRE
        #             YY     - VERSION NUMBER OF MASTER TABLE
        #                      USED( CURRENTLY 2 )
        #             ZZ     - VERSION NUMBER OF LOCAL TABLE USED
        #
        #             BUFR EDITION 3 NAMING CONVENTION
        #
        #             BWWWXXXYYZZ , CWWWXXXYYZZ , DWWWXXXYYZZ
        #
        #             B/C/D  - BUFR TABLE B/C/D
        #             WWW    - ORIGINATING SUB-CENTRE
        #             XXX    - ORIGINATING CENTRE
        #             YY     - VERSION NUMBER OF MASTER TABLE
        #                      USED( CURRENTLY 2 )
        #             ZZ     - VERSION NUMBER OF LOCAL TABLE USED
        #
        #
        #             BUFR EDITION 4 NAMING CONVENTION
        #
        #             BSSSWWWWXXXXYYZZ , CSSSWWWWXXXXYYZZ , DSSSWWWWXXXXYYZZ
        #
        #             B      - BUFR TABLE 'B'
        #             C      - BUFR TABLE 'C'
        #             D      - BUFR TABLE 'D'
        #             SSS    - MASTER TABLE
        #             WWWW(W)   - ORIGINATING SUB-CENTRE
        #             XXXX(X)   - ORIGINATING CENTRE
        #             YY(Y)     - VERSION NUMBER OF MASTER
        #                         TABLE USED( CURRENTLY 12 )
        #             ZZ(Y)     - VERSION NUMBER OF LOCAL TABLE USED
        
        return (name_table_b,name_table_d)
        #  #]
    #  #]
class BUFRMessage:
    #  #[
    pass
    # possible methods:
    # -add_descriptor
    # -expand_descriptorList
    # -encode
    # -decode
    # -print_sections_012
    # -get_descriptor_properties
    # -fill_one_real_value
    # -fill_one_string_value
    # -get_one_real_value
    # -get_one_string_value
    # -...
    #  #]
class BUFRFile:
    #  #[
    def __init__(self):
        #  #[
        self.bufr_fd  = None
        self.filename = None
        self.filemode = None
        self.filesize = None
        self.data = None
        self.use_native_byte_order = True
        self.list_of_bufr_pointers = []
        self.nr_of_bufr_messages = 0
        #  #]
    def print_properties(self,prefix="BUFRFile"):
        #  #[
        print prefix+": bufr_fd  = ",self.bufr_fd
        print prefix+": filename = ",self.filename
        print prefix+": filemode = ",self.filemode
        print prefix+": filesize = ",self.filesize
        if (self.data!=None):
            print prefix+": len(data) = ",len(self.data)
        else:
            print prefix+": data = ",self.data
        print prefix+": use_native_byte_order = ",self.use_native_byte_order
        print prefix+": list_of_bufr_pointers = ",\
              self.list_of_bufr_pointers
        print prefix+": nr_of_bufr_messages = ",self.nr_of_bufr_messages
        #print prefix+":  = ",self.
        #  #]
    def open(self,filename,mode):
        #  #[
        self.filename = filename
        self.filemode = mode
        
        # filename should include the path specification as well
        assert(mode in ['r','w','a'])

        if (mode=='r'):
            if (os.path.exists(filename)):
                self.filesize = os.path.getsize(filename)
            else:
                print "ERROR in BUFRFile.open():"
                print "Opening file: ",self.filename," with mode: ",\
                      self.filemode," failed"
                print "This file was not found or is not accessible."
                raise IOError
        try:
            self.bufr_fd = open(filename,mode)
        except:
            print "ERROR in BUFRFile.open():"
            print "Opening file: ",self.filename," with mode: ",\
                  self.filemode," failed"
            raise IOError

        if (mode=='r'):
            try:
                self.data = self.bufr_fd.read()
            except:
                print "ERROR in BUFRFile.open():"
                print "Reading data from file: ",self.filename," with mode: ",\
                      self.filemode," failed"
                raise IOError

            # split in separate BUFR messages
            self.split()

        #  #]
    def close(self):
        #  #[
        # close the file
        self.bufr_fd.close()
        # then erase all settings
        self.__init__()
        #  #]
    def split(self):
        #  #[
        # Purpose: scans the file for the string "BUFR"
        # which indicate the start of a new BUFR message,
        # counts the nr of BUFR messages, and stores file
        # pointers to the start of each BUFR message.

        # safety catch
        if (self.filesize == 0):
            self.nr_of_bufr_messages = 0
            return

        # note: this very simpple search algorithm might accidently
        # find the string "7777" in the middle of the data of a BUFR message.
        # To check on this, make sure the distance between the end of a
        # message and the start of a message if either 0 or 2 bytes
        # (this may happen if the file is padded with zeros to contain
        #  a multiple of 4 bytes)
        # Do the same check on the end of the file.

        inside_message   = False
        file_end_reached = False
        search_pos = 0
        start_pos  = -1
        end_pos    = -1
        txt_start  = "BUFR"
        txt_end    = "7777"
        while not file_end_reached:

            if (not inside_message):
                # try to find a txt_start string
                start_pos = self.data.find(txt_start,search_pos)
                print "search_pos = ",search_pos," start_pos = ",start_pos,\
                      " txt = ",txt_start

                if (start_pos!=-1):
                    inside_message = True

                    # sanity check, see if distance to the previous BUFR
                    # message is no more than 4 bytes
                    if (end_pos != -1):
                        distance = (start_pos-end_pos)
                        print "distance = ",distance," bytes"
                        if (distance > 3):
                            # this means we have found a false "7777"
                            # end marker, so ignore the last added msg
                            # and start looking again
                            (prev_start_pos,prev_end_pos) = \
                                           self.list_of_bufr_pointers.pop()
                            # restore the previous msg start pos
                            # to allow trying to search again for a correct
                            # end marker
                            start_pos = prev_start_pos
                            print "restored start_pos = ",start_pos

                            # step over the "7777" string to prepare for
                            #  searching the real end of the message
                            search_pos = end_pos
                        else:
                            # step over the "BUFR" string to prepare for
                            #  searching the end of the message
                            search_pos = start_pos+4


                else:
                    # check the distance to the fileend
                    # This should be no more than 4 bytes.
                    # If it is larger we have found a false "7777"
                    # end marker (or the file is corrupted and truncated)
                    distance = (self.filesize-end_pos)
                    print "distance to fileend = ",distance," bytes"
                    if (distance > 3):
                        # this means we have found a false "7777"
                        # end marker, so ignore the last added msg
                        # and start looking again
                        (prev_start_pos,prev_end_pos) = \
                                       self.list_of_bufr_pointers.pop()
                        # restore the previous msg start pos
                        # to allow trying to search again for a correct
                        # end marker
                        start_pos = prev_start_pos
                        print "restored start_pos = ",start_pos
                        
                        # step over the "7777" string to prepare for
                        #  searching the real end of the message
                        search_pos = end_pos

                        # file end was not yet reached, keep on looking
                        file_end_reached=False
                        inside_message = True
                    else:
                        # file end was not really reached
                        file_end_reached=True

                    
            if (inside_message and not file_end_reached):
                # try to find a txt_end string
                end_pos = self.data.find(txt_end,search_pos)
                print "search_pos = ",search_pos," end_pos = ",end_pos,\
                      " txt = ",txt_end

                if (end_pos!=-1):
                    inside_message = False

                    # point to the end of the four sevens
                    # (in slice notation, so the bufr msg data
                    # can be adressed as data[start_pos:end_pos])
                    end_pos = end_pos+4
                    
                    # step over the "7777" string to prepare for searching the
                    # end of the message
                    search_pos = end_pos

                    # store the found message
                    self.list_of_bufr_pointers.append((start_pos,end_pos))
                else:
                    file_end_reached=True

        # count howmany we found
        self.nr_of_bufr_messages = len(self.list_of_bufr_pointers)
        #  #]
    def get_num_bufr_msgs(self):
        #  #[
        if (self.bufr_fd== None):
            print "ERROR: a bufr file first needs to be opened"
            print "using BUFRFile.open() before you can request the"
            print "number of BUFR messages in a file .."
            raise IOError

        return self.nr_of_bufr_messages
        #  #]

    # possible additional methods:
    # -read_next_msg
    # -write_msg
    # -...
    #  #]


# some temporary testcode for the BUFRFile class

# NOTE: this testfile: Testfile3CorruptedMsgs.BUFR
# hold 3 copies of Testfile.BUFR catted together, and
# was especially modified using hexedit to have
# false end markers (7777) halfway the 2nd and 3rd
# message. These messages are therefore corrupted and
# decoding them will probably result in garbage, but they
# are very usefull to test the BUFRFile.split() method.

input_test_bufr_file = 'Testfile3CorruptedMsgs.BUFR'
BF = BUFRFile()
BF.print_properties(prefix="BUFRFile (before)")
BF.open(input_test_bufr_file,'r')
BF.print_properties(prefix="BUFRFile (after)")

print "This file contains: ",BF.get_num_bufr_msgs()," BUFR messages."
BF.close()
sys.exit(0)

if __name__ == "__main__":
        #  #[ test program
        print "Starting test program:"
        #  #[ instantiate the class, and build library if needed
        # (4 different tests defined for this step, with 4 different compilers)
        
        testcase = 1 # test default g95
        #testcase = 2 # test default gfortran
        #testcase = 3 # test custom gfortran
        #testcase = 4 # test custom g95-32 bit
        #testcase = 5 # test custom g95-64 bit

        if (testcase == 1):
            # tested at my laptop at home with a g95 v.0.92 (32-bit)
            # in my search PATH
            # successfully tested 18-Dec-2009
            #BI = BUFRInterfaceECMWF(verbose=True)
            BI = BUFRInterfaceECMWF(verbose=True,debug_f2py_c_api=True)
        elif (testcase == 2):
            # tested at my laptop at home with a systemwide
            # gfortran v4.3.2 installed
            # successfully tested 18-Dec-2009
            BI = BUFRInterfaceECMWF(verbose=True,
                                    preferred_fortran_compiler='gfortran')
        elif (testcase==3):
            # note that the "-O" flag is allways set for each fortran compiler
            # so no need to specify it to the fortran_flags parameter.
            
            # tested at my laptop at home with a gfortran v4.4.0 installed
            # in a user account
            # successfully tested 18-Dec-2009
            BI = BUFRInterfaceECMWF(verbose=True,
                     fortran_compiler="/home/jos/bin/gfortran_personal",
                     fortran_ld_library_path="/home/jos/bin/gcc-trunk/lib64",
                     fortran_flags="-fno-second-underscore -fPIC")
        elif (testcase==4):
            # tested at my laptop at home with a g95 v0.92 (32-bit) installed
            # in a user account
            # successfully tested 18-Dec-2009
            BI = BUFRInterfaceECMWF(verbose=True,
                     fortran_compiler="/home/jos/bin/g95_32",
                     fortran_flags="-fno-second-underscore -fPIC -i4 -r8")
        elif (testcase==5):
            # tested at my laptop at home with a g95 v0.92 (64-bit) installed in a user account
            # successfully tested 18-Dec-2009
            BI = BUFRInterfaceECMWF(verbose=True,
                     fortran_compiler="/home/jos/bin/g95_64",
                     fortran_flags="-fno-second-underscore -fPIC -i4 -r8")
        #  #]
        #  #[ import additional modules needed for testing
        import struct      # allow converting c datatypes and structs
        import ecmwfbufr   # import the just created wrapper module
        import numpy as np # import numerical capabilities
        #  #]
        #  #[ test of bufr file handling
        center               = 210 # = ksec1( 3)
        subcenter            =   0 # = ksec1(16)
        local_version        =   1 # = ksec1( 8)
        master_table_version =   0 # = ksec1(15)
        edition_number       =   3 # =  ksec0( 3)
        master_table_number  =   0 # = ksec1(14)
        (b,d) = BI.get_expected_ecmwf_bufr_table_names(center,subcenter,
                                      local_version,master_table_version,
                                      edition_number,master_table_number)
        print "tabel name B: ",b
        print "tabel name D: ",d
        assert(b == 'B0000000000210000001')
        assert(d == 'D0000000000210000001')
        #  #]
        #  #[ read the binary data
        input_test_bufr_file = 'Testfile.BUFR'
        fd=open(input_test_bufr_file,'rb')
        data=fd.read()
        len(data)
        
        sizewords=len(data)/4
        words = np.array(struct.unpack("<"+str(sizewords)+"i",data))
        #print 'data[:4] = ',data[:4]
        #print 'data[:4] = ',';'.join(str(data[i])
        #                             for i in range(4) if data[i].isalnum())
        #print 'words[:4] = ',words[:4]
        assert(data[:4] == 'BUFR')
        #  #]
        #  #[ pbopen/bpbufr/pbclose tests [not yet functional]
        do_pb_test = True # False
        if (do_pb_test):
            c_file_unit       = 0
            bufr_error_flag = 0
            print "input_test_bufr_file = ["+input_test_bufr_file+"]"
            (c_file_unit,bufr_error_flag) = \
                           ecmwfbufr.pbopen(input_test_bufr_file,'R')
            # ecmwfbufr.pbopen(c_file_unit,input_test_bufr_file,
            #                  'R',bufr_error_flag)
            print "c_file_unit = ",c_file_unit
            print "bufr_error_flag = ",bufr_error_flag
            
            buffer_size_words = 12000
            buffer_size_bytes = buffer_size_words/4
            buffer = np.zeros(buffer_size_words,dtype=np.int)
            msg_size_bytes = 0
            bufr_error_flag = 0
            ecmwfbufr.pbbufr(c_file_unit,buffer,buffer_size_bytes,
                             msg_size_bytes,bufr_error_flag)
            print "msg_size_bytes = ",msg_size_bytes
            print "buffer[0:4] = ",buffer[0:4]
            print "bufr_error_flag = ",bufr_error_flag
            
            bufr_error_flag = 0        
            ecmwfbufr.pbclose(c_file_unit,bufr_error_flag)
            print "bufr_error_flag = ",bufr_error_flag
            
            sys.exit(1)
        #  #]
        #  #[ define the needed constants

        # note: this block of constant parameters defining all array sizes
        #       in the interfaces to this ecmwf library seems not available
        #       through the f2py interface
        #       It is defined in file:
        #           ecmwf_bufr_lib/bufr_000380/bufrdc/parameter.F
        #
        #      PARAMETER(JSUP =   9,JSEC0=   3,JSEC1= 40,JSEC2=4096,JSEC3=   4,
        #     1          JSEC4=2,JELEM=320000,JSUBS=400,JCVAL=150 ,JBUFL=512000,
        #     2          JBPW = 32,JTAB =3000,JCTAB=3000,JCTST=9000,JCTEXT=9000,
        #     3          JWORK=4096000,JKEY=46, JTMAX=10,JTCLAS=64,JTEL=255)
        
        # TODO: read this file from python, in stead of hardcoding the
        #       numbers below and provide them as module parameters for
        #       pybufr_ecmwf.py
        max_nr_descriptors          =     20 # 300
        max_nr_expanded_descriptors =    140 # 160000
        max_nr_subsets              =    361 # 25
        
        ktdlen = max_nr_descriptors
        # krdlen = max_nr_delayed_replication_factors
        kelem  = max_nr_expanded_descriptors
        kvals  = max_nr_expanded_descriptors*max_nr_subsets
        # jbufl  = max_bufr_msg_size
        # jsup   = length_ksup

        #  #]
        #  #[ handle BUFR tables
        print '------------------------------'

        # define our own location for storing (symlinks to) the BUFR tables
        private_bufr_tables_dir = os.path.abspath("./tmp_BUFR_TABLES")
        if (not os.path.exists(private_bufr_tables_dir)):
            os.mkdir(private_bufr_tables_dir)
            
        # make the needed symlinks
        (source_dir,tarfile_to_install) = BI.get_source_dir()
        ecmwf_bufr_tables_dir = os.path.join(source_dir,"bufrtables/")
        ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
        needed_B_table    = "B0000000000210000001.TXT"
        needed_D_table    = "D0000000000210000001.TXT"
        available_B_table = "B0000000000098013001.TXT"
        available_D_table = "D0000000000098013001.TXT"
        
        # NOTE: the naming scheme used by ECMWF is such, that the table name can
        #       be derived from elements from sections 0 and 1, which can be
        #       decoded without loading bufr tables.
        # TODO: implement this
        
        source      = os.path.join(ecmwf_bufr_tables_dir,  available_B_table)
        destination = os.path.join(private_bufr_tables_dir,needed_B_table)
        if (not os.path.exists(destination)):
            os.symlink(source,destination)

        source      = os.path.join(ecmwf_bufr_tables_dir,  available_D_table)
        destination = os.path.join(private_bufr_tables_dir,needed_D_table)
        if (not os.path.exists(destination)):
            os.symlink(source,destination)
            
        # make sure the BUFR tables can be found
        # also, force a slash at the end, otherwise the library fails
        # to find the tables
        e = os.environ
        e["BUFR_TABLES"] = private_bufr_tables_dir+os.path.sep

        #  #]
        #  #[ call BUS012
        print '------------------------------'
        ksup   = np.zeros(         9,dtype=np.int)
        ksec0  = np.zeros(         3,dtype=np.int)
        ksec1  = np.zeros(        40,dtype=np.int)
        ksec2  = np.zeros(      4096,dtype=np.int)
        kerr   = 0
        
        print "calling: ecmwfbufr.bus012():"
        ecmwfbufr.bus012(words,ksup,ksec0,ksec1,ksec2,kerr)
        # optional parameters: kbufl)
        print "returned from: ecmwfbufr.bus012()"
        if (kerr != 0):
            print "kerr = ",kerr
            sys.exit(1)
        print 'ksup = ',ksup
        #  #]
        #  #[ call BUPRS0
        print '------------------------------'
        print "printing content of section 0:"
        print "sec0 : ",ksec0
        ecmwfbufr.buprs0(ksec0)
        #  #]
        #  #[ call BUPRS1
        print '------------------------------'
        print "printing content of section 1:"
        print "sec1 : ",ksec1
        ecmwfbufr.buprs1(ksec1)
        #  #]
        #  #[ call BUUKEY
        key = np.zeros(52, dtype=np.int)
        sec2_len = ksec2[0]
        if (sec2_len > 0):
            # buukey expands local ECMWF information from section 2
            # to the key array
            print '------------------------------'
            print "calling buukey"
            ecmwfbufr.buukey(ksec1,ksec2,key,ksup,kerr)
        #  #]
        #  #[ call BUPRS2
        print '------------------------------'
        print "length of sec2: ",sec2_len
        if (sec2_len > 0):
            print "sec2 : ",ksec2
            print "printing content of section 2:"
            ecmwfbufr.buprs2(ksup,key)
        else:
            print 'skipping section 2 [since it seems unused]'
        #  #]
        #  #[ call BUFREX
        
        # WARNING: getting this to work is rather tricky
        # any wrong datatype in these definitions may lead to
        # the code entering an infinite loop ...
        # Note that the f2py interface only checks the lengths
        # of these arrays, not the datatype. It will accept
        # any type, as long as it is numeric for the non-string items
        # If you are lucky you will get a MemoryError when you make a mistake
        # but often this will not be the case, and the code just fails or
        # produces faulty results without apparant reason.
        
        # these 4 are filled by the BUS012 call above
        # ksup   = np.zeros(         9,dtype=np.int)
        # ksec0  = np.zeros(         3,dtype=np.int)
        # ksec1  = np.zeros(        40,dtype=np.int)
        # ksec2  = np.zeros(      4096,dtype=np.int)
        
        print '------------------------------'
        ksec3  = np.zeros(         4,dtype=np.int)
        ksec4  = np.zeros(         2,dtype=np.int)
        cnames = np.zeros((kelem,64),dtype=np.character)
        cunits = np.zeros((kelem,24),dtype=np.character)
        values = np.zeros(     kvals,dtype=np.float64) # this is the default
        cvals  = np.zeros((kvals,80),dtype=np.character)
        kerr   = 0
        
        print "calling: ecmwfbufr.bufrex():"
        ecmwfbufr.bufrex(words,ksup,ksec0,ksec1,ksec2,ksec3,ksec4,
                         cnames,cunits,values,cvals,kerr)
        # optional parameters: sizewords,kelem,kvals)
        print "returned from: ecmwfbufr.bufrex()"
        if (kerr != 0):
            print "kerr = ",kerr
            sys.exit(1)
        #  #]
        #  #[ print a selection of the decoded numbers
        print '------------------------------'
        print "Decoded BUFR message:"
        print "ksup : ",ksup
        print "sec0 : ",ksec0
        print "sec1 : ",ksec1
        print "sec2 : ",ksec2
        print "sec3 : ",ksec3
        print "sec4 : ",ksec4
        print "cnames [cunits] : "
        for (i,cn) in enumerate(cnames):
            cu = cunits[i]
            txtn = ''.join(c for c in cn)
            txtu = ''.join(c for c in cu)
            if (txtn.strip() != ''):
                print '[%3.3i]:%s [%s]' % (i,txtn,txtu)

        print "values : ",values
        txt = ''.join(str(v)+';' for v in values[:20] if v>0.)
        print "values[:20] : ",txt
        
        nsubsets  = ksec3[2] # 361 # number of subsets in this BUFR message
        nelements = ksup[4] # 44 # size of one expanded subset
        lat = np.zeros(nsubsets)
        lon = np.zeros(nsubsets)
        for s in range(nsubsets):
            # index_lat = nelements*(s-1)+24
            # index_lon = nelements*(s-1)+25
            index_lat = max_nr_expanded_descriptors*(s-1)+24
            index_lon = max_nr_expanded_descriptors*(s-1)+25
            lat[s] = values[index_lat]
            lon[s] = values[index_lon]
            if (30*(s/30)==s):
                print "s=",s, "lat = ",lat[s]," lon = ",lon[s]

        print "min/max lat",min(lat),max(lat)
        print "min/max lon",min(lon),max(lon)
        #  #]
        #  #[ call BUSEL
        print '------------------------------'
        # busel: fill the descriptor list arrays (only needed for printing)   
        
        # warning: this routine has no inputs, and acts on data stored
        #          during previous library calls
        # Therefore it only produces correct results when either bus0123
        # or bufrex have been called previously on the same bufr message.....
        # However, it is not clear to me why it seems to correctly produce
        # the descriptor lists (both bare and expanded), but yet it does
        # not seem to fill the ktdlen and ktdexl values.
        
        ktdlen = 0
        ktdlst = np.zeros(max_nr_descriptors,dtype=np.int)
        ktdexl = 0
        ktdexp = np.zeros(max_nr_expanded_descriptors,dtype=np.int)
        kerr   = 0
        
        print "calling: ecmwfbufr.busel():"
        ecmwfbufr.busel(ktdlen, # actual number of data descriptors
                        ktdlst, # list of data descriptors
                        ktdexl, # actual number of expanded data descriptors
                        ktdexp, # list of expanded data descriptors
                        kerr)   # error  message
        print "returned from: ecmwfbufr.busel()"
        if (kerr != 0):
            print "kerr = ",kerr
            sys.exit(1)

        print 'busel result:'
        print "ktdlen = ",ktdlen
        print "ktdexl = ",ktdexl

        selection1 = np.where(ktdlst > 0)
        #print 'selection1 = ',selection1[0]
        ktdlen = len(selection1[0])
        selection2 = np.where(ktdexp > 0)
        #print 'selection2 = ',selection2[0]
        ktdexl = len(selection2[0])

        print 'fixed lengths:'
        print "ktdlen = ",ktdlen
        print "ktdexl = ",ktdexl

        print 'descriptor lists:'
        print "ktdlst = ",ktdlst[:ktdlen]
        print "ktdexp = ",ktdexp[:ktdexl]
        
        #  #]
        #  #[ call BUPRS3
        print '------------------------------'
        print "printing content of section 3:"
        print "sec3 : ",ksec3
        ecmwfbufr.buprs3(ksec3,
                         ktdlst, # list of data descriptors
                         ktdexp, # list of expanded data descriptors
                         cnames) # descriptor names
        #  #]
        #  #[ reinitialise all arrays
        print '------------------------------'
        print 'reinitialising all arrays...'
        print '------------------------------'
        ksup   = np.zeros(         9,dtype=np.int)
        ksec0  = np.zeros(         3,dtype=np.int)
        ksec1  = np.zeros(        40,dtype=np.int)
        ksec2  = np.zeros(      4096,dtype=np.int)
        key = np.zeros(52, dtype=np.int)
        ksec3  = np.zeros(         4,dtype=np.int)
        ksec4  = np.zeros(         2,dtype=np.int)
        cnames = np.zeros((kelem,64),dtype=np.character)
        cunits = np.zeros((kelem,24),dtype=np.character)
        values = np.zeros(     kvals,dtype=np.float64) # this is the default
        cvals  = np.zeros((kvals,80),dtype=np.character)
        ktdlen = 0
        ktdlst = np.zeros(max_nr_descriptors,   dtype=np.int)
        ktdexl = 0
        ktdexp = np.zeros(max_nr_expanded_descriptors,dtype=np.int)
        kerr   = 0
        #  #]
        #  #[ handle BUFR tables
        print '------------------------------'

        # define our own location for storing (symlinks to) the BUFR tables
        private_bufr_tables_dir = os.path.abspath("./tmp_BUFR_TABLES")
        if (not os.path.exists(private_bufr_tables_dir)):
            os.mkdir(private_bufr_tables_dir)
            
        # make the needed symlinks
        (source_dir,tarfile_to_install) = BI.get_source_dir()
        ecmwf_bufr_tables_dir = os.path.join(source_dir,"bufrtables/")
        ecmwf_bufr_tables_dir = os.path.abspath(ecmwf_bufr_tables_dir)
        needed_B_table    = "B0000000000098015001.TXT"
        needed_D_table    = "D0000000000098015001.TXT"
        available_B_table = "B0000000000098013001.TXT"
        available_D_table = "D0000000000098013001.TXT"
        
        # NOTE: the naming scheme used by ECMWF is such, that the table name can
        #       be derived from elements from sections 0 and 1, which can be
        #       decoded without loading bufr tables.
        # TODO: implement this
        
        source      = os.path.join(ecmwf_bufr_tables_dir,  available_B_table)
        destination = os.path.join(private_bufr_tables_dir,needed_B_table)
        if (not os.path.exists(destination)):
            os.symlink(source,destination)

        source      = os.path.join(ecmwf_bufr_tables_dir,  available_D_table)
        destination = os.path.join(private_bufr_tables_dir,needed_D_table)
        if (not os.path.exists(destination)):
            os.symlink(source,destination)
            
        # make sure the BUFR tables can be found
        # also, force a slash at the end, otherwise the library fails to find the tables
        e = os.environ
        e["BUFR_TABLES"] = private_bufr_tables_dir+os.path.sep

        #  #]
        #  #[ fill sections 0,1,2 and 3

        bufr_edition              =   4
        bufr_code_centre          =  98 # ECMWF
        bufr_obstype              =   3 # sounding
        bufr_subtype_L1B          = 251 # L1B
        bufr_table_local_version  =   1
        bufr_table_master         =   0
        bufr_table_master_version =  15
        bufr_code_subcentre       =   0 # L2B processing facility
        bufr_compression_flag     =   0 #  64=compression/0=no compression
        
        (year,month,day,hour,minute,second,
         weekday,julianday,isdaylightsavingstime) = time.localtime()

        num_subsets = 4
        
        # fill section 0
        ksec0[1-1]= 0
        ksec0[2-1]= 0
        ksec0[3-1]= bufr_edition

        # fill section 1
        ksec1[ 1-1]=  22                       # length sec1 bytes
        #                                        [filled by the encoder]
        # however,a minimum of 22 is obliged here
        ksec1[ 2-1]= bufr_edition              # bufr edition
        ksec1[ 3-1]= bufr_code_centre          # originating centre
        ksec1[ 4-1]=   1                       # update sequence
        ksec1[ 5-1]=   0                       # (PRESENCE SECT 2)
        #                                        (0/128 = no/yes)
        ksec1[ 6-1]= bufr_obstype              # message type 
        ksec1[ 7-1]= bufr_subtype_L1B          # subtype
        ksec1[ 8-1]= bufr_table_local_version  # version of local table
        ksec1[ 9-1]= (year-2000)               # Without offset year - 2000
        ksec1[10-1]= month                     # month
        ksec1[11-1]= day                       # day
        ksec1[12-1]= hour                      # hour
        ksec1[13-1]= minute                    # minute
        ksec1[14-1]= bufr_table_master         # master table
        ksec1[15-1]= bufr_table_master_version # version of master table
        ksec1[16-1]= bufr_code_subcentre       # originating subcentre
        ksec1[17-1]=   0
        ksec1[18-1]=   0

        # a test for ksec2 is not yet defined

        # fill section 3
        ksec3[1-1]= 0
        ksec3[2-1]= 0
        ksec3[3-1]= num_subsets                # no of data subsets
        ksec3[4-1]= bufr_compression_flag      # compression flag
        
        #  #]
        #  #[ define a descriptor list
        
        ktdlen = 6 # length of unexpanded descriptor list
        ktdlst = np.zeros(ktdlen,dtype=np.int)

        # add descriptor 1
        dd_d_date_YYYYMMDD = 301011 # date
        # this defines the sequence:
        # 004001 ! year
        # 004002 ! month
        # 004003 ! day

        
        
        # add descriptor 2
        dd_d_time_HHMM = 301012 # time 
        # this defines the sequence:
        # 004004 ! hour 
        # 004005 ! minute 
        
        # add descriptor 3
        dd_pressure = int('007004',10) # pressure [pa]  

        # WARNING: filling the descriptor variable with 007004 will fail
        # because python will interpret this as an octal value, and thus
        # automatically convert 007004 to the decimal value 3588

        # add descriptor 4
        dd_temperature = int('012001',10) # [dry-bulb] temperature [K]  
        
        # add descriptor 5
        dd_latitude_high_accuracy = int('005001',10)
        # latitude (high accuracy) [degree] 

        # add descriptor 6
        dd_longitude_high_accuracy = int('006001',10)
        # longitude (high accuracy) [degree] 

        ktdlst[0] = dd_d_date_YYYYMMDD
        ktdlst[1] = dd_d_time_HHMM
        ktdlst[2] = dd_pressure
        ktdlst[3] = dd_temperature
        ktdlst[4] = dd_latitude_high_accuracy
        ktdlst[5] = dd_longitude_high_accuracy

        #  #]
        #  #[ call BUXDES
        # buxdes: expand the descriptor list
        #         and fill the array ktdexp and the variable ktdexp
        #         [only usefull when creating a bufr msg with table D entries

        #iprint=0 # default is to be silent
        iprint=1
        if (iprint == 1):
            print "------------------------"
            print " printing BUFR template "
            print "------------------------"

        kdata = np.zeros(1,dtype=np.int) # list of replication factors 
        ecmwfbufr.buxdes(iprint,ksec1,ktdlst,kdata,
                         ktdexl,ktdexp,cnames,cunits,kerr)
        print "ktdlst = ",ktdlst
        print "ktdexp = ",ktdexp
        print "ktdexl = ",ktdexl # this one seems not to be filled ...?
        if (kerr != 0):
            print "kerr = ",kerr
            sys.exit(1)

        #print "cnames = ",cnames
        #print "cunits = ",cunits

        # retrieve the length of the expanded descriptor list
        exp_descr_list_length = len(np.where(ktdexp>0)[0])
        print "exp_descr_list_length = ",exp_descr_list_length
        #  #]
        #  #[ fill the values array with some dummy varying data
        num_values = exp_descr_list_length*num_subsets
        values = np.zeros(num_values,dtype=np.float64) # this is the default

        for subset in range(num_subsets):
            # note that python starts counting with 0, unlike fortran,
            # so there is no need to take (subset-1)
            i=subset*exp_descr_list_length

            values[i]        = 1999 # year
            i=i+1; values[i] =   12 # month
            i=i+1; values[i] =   31 # day
            i=i+1; values[i] =   23 # hour
            i=i+1; values[i] =   59    -        subset # minute
            i=i+1; values[i] = 1013.e2 - 100.e2*subset # pressure [pa]
            i=i+1; values[i] = 273.15  -    10.*subset # temperature [K]
            i=i+1; values[i] = 51.82   +   0.05*subset # latitude
            i=i+1; values[i] =  5.25   +    0.1*subset # longitude
        
        #  #]
        #  #[ call BUFREN
        #   bufren: encode a bufr message

        sizewords = 200
        kbuff = np.zeros(num_values,dtype=np.int)
        cvals = np.zeros((num_values,80),dtype=np.character)
        
        print "kvals = ",kvals
        print "cvals = ",cvals
        ecmwfbufr.bufren(ksec0,ksec1,ksec2,ksec3,ksec4,
                         ktdlst,kdata,exp_descr_list_length,
                         values,cvals,words,kerr)
        print "bufren call finished"
        if (kerr != 0):
            print "kerr = ",kerr
            sys.exit(1)
        #  #]
        
        # add test calls to:
        #   bupkey: pack ecmwf specific key into section 2
        # and possibly to:
        #   btable: tries to load a bufr-B table
        #    [usefull for testing the presence of a needed table]
        #   get_name_unit: get a name and unit string for a given descriptor
        #   buprq: sets some switches that control the bufr library
        #
        #  #]

