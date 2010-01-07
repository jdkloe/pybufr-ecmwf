#!/usr/bin/env python

#  #[ documentation
# This module implements a python interface around the BUFR library provided by ECMWF
# to allow reading and writing the WMO BUFR file standard.
# For now, this is only a reference implementatio intended to demonstrate how
# this could be done.
#
# For more on information ECMWF see: http://www.ecmwf.int/
# For more information on the BUFR library software provided
# by ECMWF see: http://www.ecmwf.int/products/data/software/download/bufr.html
#
# Note about the use of the "#  #[" and "#  #]" comments:
#   these are folding marks for my favorite editor, emacs, combined with its folding mode
#   (see http://www.emacswiki.org/emacs/FoldingMode for more details)
# Please do not remove them.
#
# This module was written by: Jos de Kloe, KNMI, and may be redistributed for now
# under the terms of the GPL v.2.
#
# Modifications:
# J. de Kloe   12-Nov-2009    Initial version
# J. de Kloe   19-Nov-2009    First working version. Builds the ecmwfbufr.so file
#                             at my home machine, and succesfully tested using it.
# J. de Kloe   03-Dec-2009    implement some code to retrieve the source dir from
#                             the tarfile, in stead of assuming it is identical
#                             to the tarfile name with stripped extension.
# J. de Kloe   03-Dec-2009    moved BUSEL testcode from test_using_ecmwfbufr.py to here
# J. de Kloe   03-Dec-2009    added tests for BUPRS0, BUPRS1, BUUKEY, and BUPRS2
#  #]
#  #[ imported modules
import os   # operating system functions
import sys  # system functions
import re   # regular expression handling
import glob # allow for filename expansion
#import gzip # handle gzipped files
import tarfile     # handle tar archives
import subprocess  # support running additional executables
import shutil      # portable file copying functions
import time        # handling of date and time
#  #]

class bufr_interface:
    #  #[
    # could contain common code for bufr_interface_ecmwf
    # and the bufr module written by Guilherme Castelao
    def __init__(self,verbose=False):
        self.verbose = verbose
    #  #]
class bufr_interface_ecmwf(bufr_interface):
    #  #[
    def __init__(self,verbose=False,
                 PreferredFortranCompiler=None,
                 PreferredCCompiler=None,
                 FortranCompiler=None,FortranLdLibraryPath=None,FFlags=None,
                 CCompiler=None,CLdLibraryPath=None,CFlags=None,
                 Debug_f2py_c_api=False):
        #  #[

        self.PreferredFortranCompiler = PreferredFortranCompiler
        self.PreferredCCompiler       = PreferredCCompiler
        self.FortranCompiler          = FortranCompiler
        self.FortranLdLibraryPath     = FortranLdLibraryPath
        self.CCompiler                = CCompiler
        self.CLdLibraryPath           = CLdLibraryPath
        self.FFlags                   = FFlags
        self.CFlags                   = CFlags

        # call the init of the parent class
        bufr_interface.__init__(self,verbose)
        # for now, this is equivalent to:
        #self.verbose = verbose

        self.ecmwf_bufr_lib_dir  = "./ecmwf_bufr_lib"

        # check for the presence of the library
        BufrLibFile = "libbufr.a"
        if (os.path.exists(BufrLibFile)):
            pass
            #print "library seems present"
        else:
            print "Entering installation sequence:"
            self.__install__()

        self.wrapper_name = "ecmwfbufr.so"
        if (os.path.exists(self.wrapper_name)):
            #print "python wrapper seems already present"
            return
        else:
            print "Entering wrapper generation sequence:"
            (Source_Dir,TarFile_to_Install) = self.__get_source_dir__()
            self.__generate_python_wrapper__(Source_Dir,Debug_f2py_c_api)

        #  #]
    def __download_library__(self):
        #  #[
        
        # this is the latest available version when I wrote this, dated 28-jul-2009
        #bufrlib_source_dir  = "http://www.ecmwf.int/products/data/software/download/software_files/"
        #bufrlib_source_file = "bufr_000380.tar.gz"
        url_bufr_page     = "http://www.ecmwf.int/products/data/software/download/bufr.html"
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
            sys.exit(1)

        # Read from the object, storing the page's contents in a list of lines
        lines = f.readlines()
        f.close()
        if (self.verbose):
            print "ECMWF download page retrieved successfully"
        
        # a test print of the html of this webpage
        #print "data:",s

        # do a simple parsing to retrieve the currently available BUFR library versions
        # and their URLs for download:

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
        LinePattern = r'<TD .*><A HREF="(.*)" .*>(.*)</A>(.*)</TD>'

        BufrLibVersions = []
        for l in lines:
            if (".tar.gz" in l):
                #print l
                MatchObject = re.match(LinePattern,l)
                if (MatchObject):
                    data = MatchObject.groups()
                    #print data
                    BufrLibVersions.append(data)

        # find most recent library version, for now just sort on name
        # that should do the trick
        MostRecentBufrLibURL       = ""
        MostRecentBufrTarFileName  = ""
        MostRecentBufrLibDate      = ""
        for data in BufrLibVersions:
            BufrLibURL      = data[0] # example: ('/products/data/software/download/software_files/bufr_000380.tar.gz'
            BufrTarFileName = data[1] # example: 'bufr_000380.tar.gz'
            BufrLibDate     = data[2] # example: ' 28.07.2009'
            if (BufrTarFileName > MostRecentBufrTarFileName):
                # store
                MostRecentBufrLibURL       = BufrLibURL
                MostRecentBufrTarFileName  = BufrTarFileName
                MostRecentBufrLibDate      = BufrLibDate

        # report the result
        if (self.verbose):
            print "Most recent library version seems to be: ",MostRecentBufrTarFileName
        download_url = url_ecmwf_website+MostRecentBufrLibURL

        if (self.verbose):
            print "trying to dowdload: ",MostRecentBufrTarFileName
        try:
            # Get a file-like object for this website
            f = urllib.urlopen(download_url)
        except:
            print "connection failed......"
            print "could not open url: ",download_url
            sys.exit(1)
        
        tarfiledata = f.read()
        f.close()
        if (self.verbose):
            print "ECMWF download page retrieved successfully"
        
        LocalFullName = os.path.join(self.ecmwf_bufr_lib_dir,MostRecentBufrTarFileName)
        fd = open(LocalFullName,'wb')
        fd.write(tarfiledata)
        fd.close()

        if (self.verbose):
            print "created local copy of: ",MostRecentBufrTarFileName
        #  #]
    def __get_source_dir__(self):
        #  #[
        list_of_bufrtarfiles = glob.glob(os.path.join(self.ecmwf_bufr_lib_dir,"*.tar.gz"))

        # safety catch
        if (len(list_of_bufrtarfiles)==0):
            return (None,None)

        # sort in reverse alphabetical order to get the newest one on top
        list_of_bufrtarfiles.sort(reverse=True)
        if (self.verbose):
            print "available library tarfiles: ",list_of_bufrtarfiles
            print "most recent library tarfile: ",list_of_bufrtarfiles[0]

        (path,TarFile_to_Install) = os.path.split(list_of_bufrtarfiles[0])
        
        # # extract the BUFR_Dir name in which the source code is to be found
        # (BUFR_Tar,ext1) = os.path.splitext(TarFile_to_Install)
        # (BUFR_Dir,ext2) = os.path.splitext(BUFR_Tar)
        #
        # # exception:
        # # it seems ECMWF has made a stupid mistake while packaging its bufr_000381
        # # version (released 20-Nov-2009). When unpacked, the software actually
        # # seems to be placed in a folder named bufr_000371 in stead of bufr_000381 !!
        # # So this hardcoded exception compensates for that:
        # # ==>seems fixed now, so this workaround is no longer needed
        # #if (BUFR_Dir == "bufr_000381"):
        # #    BUFR_Dir = "bufr_000371"
        #
        # # a similar mistake was made form version 000351:
        # if (BUFR_Dir == "bufr_000351"):
        #     BUFR_Dir = "bufr_000350"        

        # a safer wat to find out the actual name of the library source directory
        # after unpacking, is to use the gzip module and look inside:

        TarFileObj = tarfile.open(list_of_bufrtarfiles[0],'r:gz')
        names = TarFileObj.getnames()
        #print "names[0:5] = ",names[0:5]
        # this library holds everything in a single subdirectory named something
        # like bufr_000380, so I guess it is safe to assume that the first name
        # in the archive will be the name of this directory.
        BUFR_Dir = names[0]
        TarFileObj.close()

        Source_Dir = os.path.join(self.ecmwf_bufr_lib_dir,BUFR_Dir)

        return (Source_Dir,TarFile_to_Install)
        #  #]
    def __install__(self):
        #  #[

        #  #[ download and unpack the ECMWF BUFR library tar file
        (Source_Dir,TarFile_to_Install) = self.__get_source_dir__()
        if (Source_Dir == None):
            self.__download_library__()
            # retry (hopefully we have a copy of the tarfile now)
            (Source_Dir,TarFile_to_Install) = self.__get_source_dir__()
            
        if (not os.path.exists(Source_Dir)):

            # safety catch
            if (TarFile_to_Install == None):
                print "ERROR: no tarfile available for BUFR library."
                print "Maybe the automatic download failed?"
                print "If you try to install without internet connection you have"
                print "to manually create a directory named ecmwf_bufr_lib and place"
                print "a copy of a recent ECMWF BUFR library tarfile in it before"
                print "running the pybufr_ecmwf.py command."
                sys.exit(1)

            Cmd = "cd "+self.ecmwf_bufr_lib_dir+";tar zxvf "+TarFile_to_Install
            print "Executing command: ",Cmd
            os.system(Cmd)
        else:
            print "path exists: ",Source_Dir
            print "assuming the package is already unpacked..."
        #  #]

        #  #[ find a suitable fortran and c compiler to use
        # the first one found will be used, unless a preferred one is specified.
        self.custom_fc_present = self.__CheckPresence__(self.FortranCompiler)
        self.g95_present       = self.__CheckPresence__("g95")
        self.gfortran_present  = self.__CheckPresence__("gfortran")
        self.g77_present       = self.__CheckPresence__("g77")
        self.f90_present       = self.__CheckPresence__("f90")
        self.f77_present       = self.__CheckPresence__("f77")

        self.use_custom_fc = False
        self.use_g95       = False
        self.use_gfortran  = False
        self.use_g77       = False
        self.use_f90       = False
        self.use_f77       = False

        fortran_compiler_selected = False
        if (self.PreferredFortranCompiler != None):
            implementedFortranCompilers = ["custom","g95","gfortran","g77","f90","f77"]
            if not (self.PreferredFortranCompiler in implementedFortranCompilers):
                print "Warning: unknown preferred fortran compiler specified."
                print "valid options are: custom, g95, gfortran, g77, f90, f77"
                
            if (self.PreferredFortranCompiler == "custom"):
                if (self.custom_fc_present):
                    self.use_custom_fc = True
                    fortran_compiler_selected = True
            elif (self.PreferredFortranCompiler == "g95"):
                if (self.g95_present):
                    self.use_g95 = True
                    fortran_compiler_selected = True
            elif (self.PreferredFortranCompiler == "gfortran"):
                if (self.gfortran_present):
                    self.use_gfortran = True
                    fortran_compiler_selected = True
            elif (self.PreferredFortranCompiler == "g77"):
                if (self.g77_present):
                    self.use_g77 = True
                    fortran_compiler_selected = True
            elif (self.PreferredFortranCompiler == "f90"):
                if (self.f90_present):
                    self.use_f90 = True
                    fortran_compiler_selected = True
            elif (self.PreferredFortranCompiler == "f77"):
                if (self.f77_present):
                    self.use_f77 = True
                    fortran_compiler_selected = True
            else:
                print "Warning: this line should never be reached."
                print "check the list of available fortran compilers, it seems not consistent"
                print "please report this bug if you encounter it"
                sys.exit(1)
                
            if (not fortran_compiler_selected):
                print "preferred fortran compiler ["+\
                      self.PreferredFortranCompiler+"] seems not available..."
                print "falling back to default fortran compiler"

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
            print "ERROR: no valid fortran compiler found, installation is not possible"
            print "Please install a fortran compiler first. Good options are the free GNU compilers"
            print "gfortran and g95 which may be downloaded free of charge."
            sys.exit(1)

        self.custom_cc_present = self.__CheckPresence__(self.CCompiler)
        self.gcc_present       = self.__CheckPresence__("gcc")
        self.cc_present        = self.__CheckPresence__("cc")

        self.use_custom_cc = False
        self.use_gcc       = False
        self.use_cc        = False
        
        c_compiler_selected = False
        if (self.PreferredCCompiler !=None):
            implementedCCompilers = ["custom","gcc","cc"]
            if not (self.PreferredCCompiler in implementedCCompilers):
                print "Warning: unknown preferred c compiler specified."
                print "valid options are: custom, gcc, cc"

            if (self.PreferredCCompiler == "custom"):
                if (self.custom_cc_present):
                    self.use_custom_cc = True
                    c_compiler_selected = True
            elif (self.PreferredCCompiler == "gcc"):
                if (self.gcc_present):
                    self.use_gcc = True
                    c_compiler_selected = True
            elif (self.PreferredCCompiler == "cc"):
                if (self.cc_present):
                    self.use_cc = True
                    c_compiler_selected = True
            else:
                print "Warning: this line should never be reached."
                print "check the list of available c compilers, it seems not consistent"
                print "please report this bug if you encounter it"
                sys.exit(1)
                
            if (not c_compiler_selected):
                print "preferred c compiler ["+\
                      self.PreferredCCompiler+"] seems not available..."
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
            print "ERROR: no valid c compiler found, installation is not possible"
            print "Please install a c compiler first. A good options is the free GNU compiler gcc"
            print "which may be downloaded free of charge."
            sys.exit(1)

        if (self.verbose):
            print "custom_fc_present = ",self.custom_fc_present," use_custom_fc = ",self.use_custom_fc
            print "g95_present       = ",self.g95_present,      " use_g95       = ",self.use_g95
            print "gfortran_present  = ",self.gfortran_present, " use_gfortran  = ",self.use_gfortran
            print "g77_present       = ",self.g77_present,      " use_g77       = ",self.use_g77
            print "f90_present       = ",self.f90_present,      " use_f90       = ",self.use_f90
            print "f77_present       = ",self.f77_present,      " use_f77       = ",self.use_f77

            print "custom_cc_present = ",self.custom_cc_present," use_custom_cc = ",self.use_custom_cc
            print "gcc_present       = ",self.gcc_present,      " use_gcc       = ",self.use_gcc
            print "cc_present        = ",self.cc_present,       " use_cc        = ",self.use_cc
            
        #  #]
        
        #  #[ add the custom LD_LIBRARY_PATH settings
        
        # check for the presence of needed libraries
        # in case the fortran compiler is installed in a user account (like I have myself)
        # NOTE: this one depends on the BUFR config file to determine the compiler command
        # so it will not run when run before creation of this config file
        # However, this solution is probably not very portable anyway, so maybe
        # it is better to remove it entirely (and replace maybe by a warning in case
        # the executable fails in the above fortran compilation test)
        #libpath = self.__check_needed_fc_libraries__()

        libpath = ""
        if (self.FortranLdLibraryPath != None):
            libpath = ";".join(s for s in [libpath,self.FortranLdLibraryPath] if (s != ""))
        if (self.CLdLibraryPath != None):
            libpath = ";".join(s for s in [libpath,self.CLdLibraryPath] if (s != ""))

        if (libpath != ""):
            print "Using LD_LIBRARY_PATH setting: ",libpath
        #  #]

        #  #[ generate a config file for compilation of the BUFR library
        
        #-----------------------------------------------------------------------------#
        # Possible commands to the make command for the BUFR library, in case you     #
        # wish to use the config files from the ECMWF software package are:           #
        # (see the README file within Source_Dir)                                     #
        # - architecture: ARCH=sgimips (or: decalpha,hppa,linux,rs6000,sun4)          #
        # - 64 bit machine: R64=R64                                                   #
        # - compiler name (only for linux or sun machines): CNAME=_gnu                #
        #                                                                             #
        #-----------------------------------------------------------------------------#

        # NOTE that for the linux case the library has some hardcoded switches to use
        # 32-bit variables in its interfacing, so DO NOT try to use the 64 bit option
        # on linux, even if you have a 64-bit processor and compiler available !
        # Even if the code runs, it will fail miserably and cause segmentation faults
        # if you are lucky, or just plain nonsense if you are out of luck ....

        # these 4 settings determine the name of the config file used by the Make command
        # look in ecmwf_bufr_lib/bufr_000380/config/ to see all available versions
        #ARCH="linux"
        #CNAME="_compiler"
        #R64="" 
        #A64=""
        
        # note: usefull free compilers for linux that you can use are:
        # (at least for these config files are provided in the ECMWF BUFR package)
        # g77      : CNAME="_gnu"
        # g95      : CNAME="_g95"
        # gfortran : CNAME="_gfortran"

        # Notes on compiler switches:

        # for most compilers you should force the BUFR library to use 4 byte integers
        # as default integer. Do this by adding the "-i4" option.
        # This works for most compilers, with gfortran as known exception (that one has
        # this setting as default and does not have a commandline option to set it)

        # the c compiler step seems to need the "-DFOPEN64" switch to be set
        # (at least it is present in most config files in the package) but it is
        # never used in the source code itself, so I guess it is obsolete.

        if (self.use_custom_fc):
            FC = self.FortranCompiler
            # Default compiler switches
            FFLAGS = "-O -Dlinux"
            # add any custom flags given by the user
            if (self.FFlags != None):
                FFLAGS = FFLAGS + ' ' + self.FFlags
        elif (self.use_g95):
            FC = "g95"
            # Default compiler switches
            FFLAGS = "-O -Dlinux"
            # additional g95 specific switches
            FFLAGS = FFLAGS+" -i4"
            FFLAGS = FFLAGS+" -fno-second-underscore"
            FFLAGS = FFLAGS+" -r8"
            FFLAGS = FFLAGS+" -fPIC"
            #CNAME="_g95"
        elif (self.use_gfortran):
            FC = "gfortran"
            # Default compiler switches
            FFLAGS = "-O -Dlinux"
            # additional gfortran specific switches
            FFLAGS = FFLAGS+" -fno-second-underscore"
            FFLAGS = FFLAGS+" -fPIC"
            #FINTEGERDEFINITION=" -fdefault-integer-4"
            # an explicit 4-byte default integer options seems not to exists
            # for gfortran, so lets just hope that is the default ...
            FINTEGERDEFINITION=""
            #CNAME="_gfortran"
        elif (self.use_g77):
            FC = "g77"
            # Default compiler switches
            FFLAGS = "-O -Dlinux"
            FFLAGS = FFLAGS+" -i4"
            #CNAME="_gnu"
        elif (self.use_f90):
            # this catches installations that have some commercial fortran
            # installed, which usually are symlinked to the name
            # f90 for convenience
            FC = "f90"
            # Default compiler switches
            FFLAGS = "-O -Dlinux"
            FFLAGS = FFLAGS+" -i4"
            #CNAME="_???"
        elif (self.use_f77):
            # this catches installations that have some commercial fortran
            # installed, which usually are symlinked to the name
            # f77 for convenience
            FC = "f77"
            # Default compiler switches
            FFLAGS = "-O -Dlinux"
            FFLAGS = FFLAGS+" -i4"
            #CNAME="_???"
        else:
            print "ERROR in bufr_interface_ecmwf.__install__:"
            print "No suitable fortran compiler found"
            sys.exit(1)

        if (self.use_custom_cc):
            CC=self.CCompiler
            CFLAGS = "-fPIC"
            # add any custom flags given by the user
            if (self.CFlags != None):
                CFLAGS = CFLAGS+' '+self.CFlags
        elif (self.use_gcc):
            CC="gcc"
            # Default compiler switches
            CFLAGS = "-fPIC"
        elif (self.use_cc):
            # this catches installations that have some commercial c-compiler
            # installed, which usually are symlinked to the name
            # cc for convenience
            CC="cc"
            # Default compiler switches
            CFLAGS = "-fPIC"
        else:
            print "ERROR in bufr_interface_ecmwf.__install__:"
            print "No suitable c compiler found"
            sys.exit(1)

        # no check implemented on the "ar" and "ranlib" commands yet
        # (easy to add if we woould need it)

        # a command to generate an archive (*.a) file
        AR="ar"
        # a command to generate an index of an archive file
        RL = "/usr/bin/ranlib"

        # Unfortunately, the config files supplied with this library seem
        # somewhat outdated and sometimes incorrect, or incompatible with
        # the current compiler version (since they seem based on some
        # older compiler version, used some time ago at ECMWF, and never
        # got updated). This especially is true for the g95 compiler.
        # Therefore we have decided (at KNMI) to create our own
        # custom config file in stead.
        # We just call it: config.linux_compiler
        # which seems safe for now, since ECMWF doesn't use that name.
        
        ARCH="linux"
        CNAME="_compiler"
        R64="" 
        A64=""

        # construct the name of the config file to be used
        ConfigFile = "config."+ARCH+CNAME+R64+A64
        FullnameConfigFile = os.path.join(Source_Dir,"config",ConfigFile)

        # this check is only usefull if you use one of the existing config files
        #if not os.path.exists(FullnameConfigFile):
        #    # see if a version with ".in" extension is present
        #    # and if so, symlink to it.
        #    if not os.path.exists(FullnameConfigFile+".in"):
        #        print "ERROR: config file not found: ",FullnameConfigFile
        #        sys.exit(1)
        #    else:
        #        os.symlink(ConfigFile+".in",FullnameConfigFile)

        # create our custom config file:
        print "Using: "+FC+" as fortran compiler"
        print "Using: "+CC+" as c compiler"

        print "Creating ECMWF-BUFR config file: ",FullnameConfigFile
        fd = open(FullnameConfigFile,'wt')
        fd.write("#   Generic configuration file for linux.\n")
        fd.write("AR         = "+AR+"\n")
        fd.write("ARFLAGS    = rv\n")
        fd.write("CC         = "+CC+"\n")
        fd.write("CFLAGS     = -O "+CFLAGS+"\n")
        fd.write("FASTCFLAGS = "+CFLAGS+"\n")
        fd.write("FC         = "+FC+"\n")
        fd.write("FFLAGS     = "+FFLAGS+"\n")
        fd.write("VECTFFLAGS = "+FFLAGS+"\n")
        fd.write("RANLIB     = "+RL+"\n")
        fd.close()
        
        # create a backup copy in the 
        Source      = FullnameConfigFile
        Destination = os.path.join(self.ecmwf_bufr_lib_dir,"ConfigFile")
        shutil.copyfile(Source,Destination)
        #  #]
        
        #  #[ try to compile little pieces of Fortran and c to test the compilers
        self.__fortran_compile_test__(FC,FFLAGS,libpath)
        self.__c_compile_test__(CC,CFLAGS,libpath)
        #  #]
        
        #  #[ now use the Make command provided in this package to build the library

        # construct the compilation command:
        Cmd = "cd "+Source_Dir+";make ARCH="+ARCH+" CNAME="+CNAME+" R64="+R64+" A64="+A64

        # now issue the Make command
        if (libpath == ""):
            print "Executing command: ",Cmd
            os.system(Cmd)
            #(lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd)
            #self.__RunShellCommand__(Cmd,CatchOutput=False)
        else:
            #(lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,libpath=libpath)
            self.__RunShellCommand__(Cmd,libpath=libpath,CatchOutput=False)
        #  #]

        #  #[ check the result
        BufrLibFile = "libbufr.a"
        FullnameBufrLibFile = os.path.join(Source_Dir,BufrLibFile)
        if (os.path.exists(FullnameBufrLibFile)):
            print "Build seems successfull"
            # remove any old symlink that might be present
            if (os.path.exists(BufrLibFile)):
                os.remove(BufrLibFile)
            # make a symlink in a more convenient location
            os.symlink(FullnameBufrLibFile,BufrLibFile)
        else:
            print "ERROR in bufr_interface_ecmwf.__install__:"
            print "No libbufr.a file seems generated."
            sys.exit(1)
        #  #]

        #  #[ some old notes
        
        # save the settings for later use
        #self.make_settings = (ARCH,CNAME,R64,A64)
        #self.compilers     = (FC,FFLAGS,CC,CFLAGS)
        #self.tools         = (AR,RL)

        # actually, this saving of settings is not the way I would
        # prefer doing this. I think it is better to keep the 2 stages
        # (installation of the BUFR library, and generation of the
        #  python interface shared object) as separate as possible.
        # This allows rerunning generation of the python interface
        # without rerunning the installation of the BUFR library
        # (which will at least save a lot of time during development)
        #
        # So in the __check_needed_fc_libraries__ routine should just
        # read the config file generated above, and not use these
        # settings in self, that might not always be defined.
        #  #]
        
        #  #]
    def __RunShellCommand__(self,Cmd,libpath=None,CatchOutput=True):
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
                
                
        print "Executing command: ",Cmd
        if (CatchOutput):
            SubPr = subprocess.Popen(Cmd,
                                     shell=True,
                                     env=e,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            
            # wait until the child process is done
            #SubPr.wait() # seems not necessary when catching stdout and stderr
            
            lines_stdout = SubPr.stdout.readlines()
            lines_stderr = SubPr.stderr.readlines()
            
            #print "lines_stdout: ",lines_stdout
            #print "lines_stderr: ",lines_stderr
            
            return (lines_stdout,lines_stderr)

        else:
            SubPr = subprocess.Popen(Cmd, shell=True, env=e)

            # wait until the child process is done
            SubPr.wait()
            return
        #  #]
    def __CheckPresence__(self,command):
        #  #[
        if (self.verbose):
            print "checking for presence of command: "+str(command)
        
        result = []

        if (command == None):
            return False
        
        # get the real command, in case it was an alias
        Cmd = "which "+command
        (lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,CatchOutput=True)

        if (len(lines_stdout)==0):
            # command is not present in default path
            return False
        else:
            # command is present in default path
            return True
        #  #]
    def __fortran_compile_test__(self,FC,FFLAGS,libpath):
        #  #[
        # Note: for now the flags are not used in these test because these
        # are specific for generating a shared-object file, and will fail to
        # generate a simple executable for testing

        FortranTestCode = \
"""
program pybufr_test_program

  print *,'Hello pybufr module:'
  print *,'Fortran compilation seems to work fine ...'

end program pybufr_test_program
"""

        # generate a testfile with a few lines of Fortran90 code
        FortranTestExecutable = "pybufr_fortran_test_program"
        FortranTestFile       = FortranTestExecutable+".F90"
        fd = open(FortranTestFile,'wt')
        fd.write(FortranTestCode)
        fd.close()

        # contruct the compile command
        Cmd = FC+' -o '+FortranTestExecutable+' '+FortranTestFile
        
         # now issue the compile command
        if (libpath == ""):
            print "Executing command: ",Cmd
            os.system(Cmd)
        else:
            self.__RunShellCommand__(Cmd,libpath=libpath,CatchOutput=False)

        # now execute the just generated test program to verify if we succeeded
        Cmd = FortranTestExecutable
        if (libpath == ""):
            (lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd)
        else:
            (lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,libpath=libpath)

        expected_output = [' Hello pybufr module:\n',
                           ' Fortran compilation seems to work fine ...\n']
        if ( (expected_output[0] not in lines_stdout) or
             (expected_output[1] not in lines_stdout)   ):
            print "ERROR: Fortran compilation test failed; something seems very wrong"
            print "Expected output: ",expected_output
            print 'actual output stdout = ',lines_stdout
            print 'actual output stderr = ',lines_stderr
            sys.exit(1)

        print "Fortran compilation test successfull..."

        # clean up
        os.remove(FortranTestExecutable)
        os.remove(FortranTestFile)
        
        #  #]
    def __c_compile_test__(self,CC,CFLAGS,libpath):
        #  #[
        # Note: for now the flags are not used in these test because these
        # are specific for generating a shared-object file, and will fail to
        # generate a simple executable for testing

        CTestCode = \
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
        CTestExecutable = "pybufr_c_test_program"
        CTestFile       = CTestExecutable+".c"
        fd = open(CTestFile,'wt')
        fd.write(CTestCode)
        fd.close()

        # contruct the compile command
        Cmd = CC+' -o '+CTestExecutable+' '+CTestFile
        
         # now issue the compile command
        if (libpath == ""):
            print "Executing command: ",Cmd
            os.system(Cmd)
        else:
            self.__RunShellCommand__(Cmd,libpath=libpath,CatchOutput=False)

        # now execute the just generated test program to verify if we succeeded
        Cmd = CTestExecutable
        if (libpath == ""):
            (lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd)
        else:
            (lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,libpath=libpath)

        expected_output = ['Hello pybufr module:\n',
                           'c compilation seems to work fine ...\n']
        if ( (expected_output[0] not in lines_stdout) or
             (expected_output[1] not in lines_stdout)   ):
            print "ERROR: c compilation test failed; something seems very wrong"
            print "Expected output: ",expected_output
            print 'actual output stdout = ',lines_stdout
            print 'actual output stderr = ',lines_stderr
            sys.exit(1)

        print "c compilation test successfull..."

        # clean up
        os.remove(CTestExecutable)
        os.remove(CTestFile)
        #  #]
    def __check_needed_fc_libraries__(self):
        #  #[ obsolete
        ConfigFile = os.path.join(self.ecmwf_bufr_lib_dir,"ConfigFile")
        lines = open(ConfigFile).readlines()

        # extract which fortran compiler is used
        for l in lines:
            parts=l.split('=')
            if (parts[0].strip()=="FC"):
                FortranCompiler = parts[1].strip()

        if (FortranCompiler == "gfortran"):
            print "Checking library availability for FortranCompiler = ",FortranCompiler
            # get the real command, in case it was an alias
            Cmd = "which "+FortranCompiler
            (lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,CatchOutput=True)
            if (len(lines_stdout)==0):
                # command is not present in default path
                print "ERROR: gfortran seems not present in the default part"
                sys.exit(1)
            else:
                # Return the canonical path of the specified filename, eliminating any
                # symbolic links encountered in the path.
                compiler1 = os.path.realpath(lines_stdout[0].strip())
                # gives in my case at home: /home/jos/bin/gcc-trunk/bin/gfortran

                # at work, I have a little wrapper script, to give some default
                # commandline options like -Wall to the gfortran command
                # In this case the gfortran command found by which actually is just a
                # little shell script of a few hundred kb. The actual gfortran compiler
                # is several 100 kb, so just the size to differentiate:
                size = os.path.getsize(compiler1)
                
                # so in case the size indicates a script. try to extract the gfortran
                # executable name from it
                if (size<100000):                    
                    print 'wrapper script detected'
                    # read the script
                    lines = open(compiler1).readlines()
                    for l in lines:
                        # for now, just assume the 1st line that has the gfortran
                        # string, contains the call to the executable
                        if ('gfortran' in l):
                            compiler1 = l.split()[0]
                            break

                print "compiler1=",compiler1
                libpath = ''
                if (compiler1 == 'echo'):
                    print 'KNMI specific script found:'
                    print 'see: /usr/local/free/gfortran.csh'
                    print 'and: /usr/local/free/gfortran.sh'
                    print 'Please do a manual LD_LIBRARY_PATH setting if needed ...'
                    return
                
                # Now find the corresponding f951 executable.
                # Note that both g95 and gfortran use this name for their
                # actual compiler executable, since they are forks of each other.
                # For gfortran this executable resides inside the libexec folder
                # next to the bin folder in which the gfortran command is installed
                # (al least on my system, so I hope this is a more general rule)
                (comp_path,comp) = os.path.split(compiler1)
                (base,head)      = os.path.split(comp_path)
                if (head=="bin"):
                    Cmd = "find "+os.path.join(base,"libexec")+" | grep f951"
                    (lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,CatchOutput=True)
                    # ==> find /home/jos/bin/gcc-trunk/libexec/ | grep f951
                    # on my system this returns:
                    # /home/jos/bin/gcc-trunk/libexec/gcc/x86_64-unknown-linux-gnu/4.4.0/f951
                    f951_cmd = lines_stdout[0].strip()
                    Cmd = "ldd "+f951_cmd
                    (lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,CatchOutput=True)
                    #if self.verbose:
                    #    print "lines_stdout:"
                    #    print '[%s]\n'.join(l for l in lines_stdout)
                    #    print "lines_stderr:"
                    #    print '[%s]\n'.join(l for l in lines_stderr)

                    # ==> ldd ~/bin/gcc-trunk/libexec/gcc/x86_64-unknown-linux-gnu/4.4.0/f951 
                    # on my system this returns:
                    # linux-vdso.so.1 =>  (0x00007fff602bb000)
                    # libcloog.so.0 => not found
                    # libppl_c.so.2 => not found
                    # libppl.so.7 => not found
                    # libgmpxx.so.4 => /usr/lib64/libgmpxx.so.4 (0x00007f163231d000)
                    # libc.so.6 => /lib64/libc.so.6 (0x000000354d400000)
                    # libgmp.so.3 => /usr/lib64/libgmp.so.3 (0x000000354d000000)
                    # libstdc++.so.6 => /usr/lib64/libstdc++.so.6 (0x0000003553400000)
                    # libm.so.6 => /lib64/libm.so.6 (0x000000354d800000)
                    # libgcc_s.so.1 => /lib64/libgcc_s.so.1 (0x0000003552000000)
                    # /lib64/ld-linux-x86-64.so.2 (0x000000354c000000)

                    missing_libraries = []
                    libpath   = ""
                    for l in lines_stdout:
                        if ("not found" in l):
                            print "WARNING: system library not found: ",l,
                            missing_libraries.append(l.split()[0].strip())
                    if (len(missing_libraries)>0):
                        # try to find the library setting to be used for these missing ones
                        libpath32 = os.path.join(base,"lib")
                        libpath64 = os.path.join(base,"lib64")

                        # see if the missing ones are present in the 32 bit lib folder
                        # next to the bin folder holding gfortran
                        uselib32 = True
                        for ml in missing_libraries:
                            name = os.path.join(libpath32,ml)
                            if not os.path.exists(name):
                                uselib32 = False
                        if (uselib32):
                            print "essential 32-bit libraries seem present in: ",libpath32
                            print "adding this one to the LD_LIBRARY_PATH"
                            libpath = libpath32
                            
                        uselib64=True
                        for ml in missing_libraries:
                            name = os.path.join(libpath64,ml)
                            if not os.path.exists(name):
                                uselib64 = False
                        if (uselib64):
                            print "essential 64-bit libraries seem present in: ",libpath64
                            print "adding this one to the LD_LIBRARY_PATH"
                            libpath = libpath64


        #elif (FortranCompiler == "g95"):
        #    print "Checking library availability for FortranCompiler = ",g95
        #    pass            
        else:
            print "ERROR: checking not yet implemented for FortranCompiler: ",FortranCompiler
            sys.exit(1)


        # possible numpy check:
        #ldd /usr/lib64/python2.5/site-packages/numpy/lib/_compiled_base.so
        # gives:
        #linux-vdso.so.1 =>  (0x00007fff62fc1000)
        #libpython2.5.so.1.0 => /usr/lib64/libpython2.5.so.1.0 (0x00007fc77f72f000)
        #libpthread.so.0 => /lib64/libpthread.so.0 (0x00007fc77f513000)
        #libc.so.6 => /lib64/libc.so.6 (0x00007fc77f1a0000)
        #libdl.so.2 => /lib64/libdl.so.2 (0x00007fc77ef9c000)
        #libutil.so.1 => /lib64/libutil.so.1 (0x00007fc77ed99000)
        #libm.so.6 => /lib64/libm.so.6 (0x00007fc77eb13000)
        #/lib64/ld-linux-x86-64.so.2 (0x000000354c000000)

        return libpath
        #  #]
    def __generate_python_wrapper__(self,Source_Dir,Debug_f2py_c_api=False):
        #  #[
        wrapper_build_dir   = "f2py_build"
        wrapper_module_name = "ecmwfbufr"
        signatures_filename = "signatures.pyf"

        #SrcFiles = ["buxdes.F",
        #            "bufren.F",
        #            "bufrex.F",
        #            "btable.F",
        #            "get_name_unit.F",
        #            "bus012.F",
        #            "busel.F",
        #            "buprs0.F",
        #            "buprs1.F",
        #            "buprs2.F",
        #            "buprs3.F",
        #            "buukey.F",
        #            "bupkey.F",
        #            "buprq.F"]
        #SrcFileList = ' '.join(os.path.join(Source_Dir,"bufrdc",f) for f in SrcFiles)
        # compilation of the wrapper seems to work when I use
        # this selected set of fortran files, but when I try to import the module
        # in python I get the following error (don't know yet why):
        #   >>> import ecmwfbufr
        #   Traceback (most recent call last):
        #     File "<stdin>", line 1, in <module>
        #   ImportError: ./ecmwfbufr.so: undefined symbol: _gfortran_concat_string
        #   >>> 

        # just take them all
        SrcFileList = Source_Dir+"/bufrdc/*.F"

        # check for the presence of needed libraries
        # in case the fortran compiler is installed in a user account (like I have myself)
        #libpath = self.__check_needed_fc_libraries__()

        libpath = ""
        if (self.FortranLdLibraryPath != None):
            libpath = ";".join(s for s in [libpath,self.FortranLdLibraryPath] if (s != ""))
        if (self.CLdLibraryPath != None):
            libpath = ";".join(s for s in [libpath,self.CLdLibraryPath] if (s != ""))

        if (libpath != ""):
            print "Using LD_LIBRARY_PATH setting: ",libpath

        # call f2py and create a signature file that defines the
        # interfacing to the fortran routines in this library
        Cmd = "f2py --build-dir "+wrapper_build_dir+\
              " -m "+wrapper_module_name+\
              " -h "+signatures_filename+\
              " "+SrcFileList

        if (libpath == ""):
            print "Executing command: ",Cmd
            os.system(Cmd)
            #(lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,CatchOutput=True)
        else:
            #(lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,libpath=libpath,
            #                                                       CatchOutput=True)
            self.__RunShellCommand__(Cmd,libpath=libpath,CatchOutput=False)
    
        # safety check: see if the signatures.pyf file really is created
        signatures_fullfilename = os.path.join(wrapper_build_dir,signatures_filename)
        if (not os.path.exists(signatures_fullfilename)):
            print "ERROR: build of python wrapper failed"
            print "the signatures file could not be found"
            sys.exit(1)

        ConfigFile = os.path.join(self.ecmwf_bufr_lib_dir,"ConfigFile")
        lines = open(ConfigFile).readlines()

        # extract which fortran compiler is used
        FortranCompiler      = 'undefined'
        FortranCompilerFlags = 'undefined'
        for l in lines:
            parts=l.split('=')
            if (parts[0].strip()=="FC"):
                FortranCompiler = parts[1].strip()
            if (parts[0].strip()=="FFLAGS"):
                FortranCompilerFlags = parts[1].strip()

        # adapt the signature file
        # this is needed, since the wrapper generation fails to do a number
        # of file includes that are essential for the interface definition
        # To circumvent this, remove the not-properly defined constants
        # and replace them by their numerical values
        self.__adapt_f2py_signature_file__(signatures_fullfilename)

        # it might be usefull for debugging to include this option: --debug-capi
        debug_f2py_c_api_option = ""
        if (Debug_f2py_c_api):
            debug_f2py_c_api_option = " --debug-capi "

        if (self.FortranCompiler != None):
            Cmd = "f2py  --build-dir "+wrapper_build_dir+\
                  debug_f2py_c_api_option+\
                  " --f90exec="+FortranCompiler+\
                  " --f90flags='"+FortranCompilerFlags+"'"+\
                  " --f77flags='"+FortranCompilerFlags+"'"+\
                  " ./f2py_build/signatures.pyf -L./ -lbufr -c"
        else:
            # note: adding the FortranCompilerFlags manually like this causes some
            # of them to be included double, but this doesn't hurt, and is the only
            # way I get the automatic compilation using the g95 compiler going.
            # TODO: Maybe later I could sort out how to use the python f2py module
            # in stead of the executable, and clean-up the compiler flags before
            # starting the tool
            Cmd = "f2py  --build-dir "+wrapper_build_dir+\
                  debug_f2py_c_api_option+\
                  " --f90flags='"+FortranCompilerFlags+"'"+\
                  " --f77flags='"+FortranCompilerFlags+"'"+\
                  " --fcompiler="+FortranCompiler+\
                  " ./f2py_build/signatures.pyf -L./ -lbufr -c"

        if (libpath == ""):
            print "Executing command: ",Cmd
            os.system(Cmd)
            #(lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,CatchOutput=False)
        else:
            #(lines_stdout,lines_stderr) = self.__RunShellCommand__(Cmd,libpath=libpath,
            #                                                       CatchOutput=True)
            self.__RunShellCommand__(Cmd,libpath=libpath,CatchOutput=False)
            
        # finally, again check for the presence of the wrapper
        # to see if the build was successfull
        if (os.path.exists(self.wrapper_name)):
            print "a python wrapper to the ECMWF BUFR library has been generated"
            return
        else:
            print "ERROR: build of python wrapper failed"
            print "the compilation or linking stage failed"
            sys.exit(1)

        #  #]
    def __adapt_f2py_signature_file__(self,signature_file):
        #  #[

        # NOTE: maybe this modification is not needed if I can get the file with the
        #       parameters included in an other way.
        #       Looking at the f2py manpage the option -include might do the trick
        #       but that one is depricated. In stead a usercode section should be used
        #       but that again means modifying the signature file ...
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
        Source      = signature_file
        Destination = signature_file+".bak"
        shutil.copyfile(Source,Destination)
        
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
                    # Add the intent(inplace) switch to all subroutine parameters
                    # This might not be very pretty, but otherwise all parameters
                    # are assigned the default, which is intent(in).
                    # Maybe the proper way would be to sort out for each routine
                    # in this library which parameters are intent(in) and which are
                    # intent(out), but this is a huge task (and should be done
                    # by ECMWF rather then by us I think...)
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
                self.__insert_pb_interface_definition__(fd)

            fd.write(l)
        fd.close()
        #  #]
    def __insert_pb_interface_definition__(self,fd):
        #  #[
        # note:
        # it seems I am doing something wrong here, since this interface
        # is not yet functional. When trying to execute ecmwfbufr.pbopen()
        # I get the not very helpfull error message:
        #   "SystemError: NULL result without error in PyObject_Call"
        # Anybody out there who has an idea how this can be solved?
        indentation = 8*' '
        lines_to_add = ["subroutine pbopen(cFileUnit,BufrFileName,mode,bufr_error_flag)",
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

        print "Inserting hardcoded interface to pbbufr routines in signatures file ..."
        for l in lines_to_add:
            fd.write(indentation+l+'\n')
            
        #  #]
    def __get_expected_ecmwf_bufr_table_names__(self,center,subcenter,
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

        (Source_Dir,TarFile_to_Install) = self.__get_source_dir__()
        ecmwf_BUFR_TABLES_dir = os.path.join(Source_Dir,"bufrtables/")

        #-------------------------------------------------------------
        # see which BUFR tables naming convention is used (short/long)
        #-------------------------------------------------------------
        bufrtable_naming_convention = conv_undefined

        testfile = os.path.join(ecmwf_BUFR_TABLES_dir,testfile_short)
        if (os.path.exists(testfile)):
            print "Using short BUFRtables naming convention ..."
            bufrtable_naming_convention = conv_short

        testfile = os.path.join(ecmwf_BUFR_TABLES_dir,testfile_medium)
        if (os.path.exists(testfile)):
            print "Using medium length BUFRtables naming convention ..."
            bufrtable_naming_convention = conv_medium

        testfile = os.path.join(ecmwf_BUFR_TABLES_dir,testfile_long)
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
                # starting from edition 3 the originating center has one digit more
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
class bufrmsg:
    #  #[
    pass
    # possible methods:
    # -AddDescriptor
    # -ExpandDescriptorList
    # -Encode
    # -Decode
    # -PrintSections012
    # -GetDescriptorProperties
    # -FillOneRealValue
    # -FillOneStringValue
    # -GetOneRealValue
    # -GetOneStringValue
    # -...
    #  #]
class bufrfile:
    #  #[
    pass
    # possible methods:
    # -SetFilename
    # -GetFilename
    # -SetFilemode (r,w)
    # -GetFilemode
    # -OpenFile
    # -CloseFile
    # -GetNumBufrMsgs
    # -ReadNextMsg
    # -WriteMsg
    # -PrintFileProperties
    # -...
    #  #]

if __name__ == "__main__":
        #  #[ test program
        print "Starting test program:"
        #  #[ instantiate the class, pass all settings to it, and build library if needed
        # (4 different tests defined for this step, with 4 different compilers)
        
        testcase = 1 # test default g95
        #testcase = 2 # test default gfortran
        #testcase = 3 # test custom gfortran
        #testcase = 4 # test custom g95-32 bit
        #testcase = 5 # test custom g95-64 bit

        if (testcase == 1):
            # tested at my laptop at home with a g95 v.0.92 (32-bit) in my search PATH
            # successfully tested 18-Dec-2009
            BI = bufr_interface_ecmwf(verbose=True,Debug_f2py_c_api=True)
        elif (testcase == 2):
            # tested at my laptop at home with a systemwide gfortran v4.3.2 installed
            # successfully tested 18-Dec-2009
            BI = bufr_interface_ecmwf(verbose=True,PreferredFortranCompiler='gfortran')
        elif (testcase==3):
            # note that the "-O" flag is allways set for each fortran compiler
            # so no need to specify it to the FFlags parameter.
            
            # tested at my laptop at home with a gfortran v4.4.0 installed in a user account
            # successfully tested 18-Dec-2009
            BI = bufr_interface_ecmwf(verbose=True,
                                      FortranCompiler="/home/jos/bin/gfortran_personal",
                                      FortranLdLibraryPath="/home/jos/bin/gcc-trunk/lib64",
                                      FFlags="-fno-second-underscore -fPIC")
        elif (testcase==4):
            # tested at my laptop at home with a g95 v0.92 (32-bit) installed in a user account
            # successfully tested 18-Dec-2009
            BI = bufr_interface_ecmwf(verbose=True,
                                      FortranCompiler="/home/jos/bin/g95_32",
                                      FFlags="-fno-second-underscore -fPIC -i4 -r8")
        elif (testcase==5):
            # tested at my laptop at home with a g95 v0.92 (64-bit) installed in a user account
            # successfully tested 18-Dec-2009
            BI = bufr_interface_ecmwf(verbose=True,
                                      FortranCompiler="/home/jos/bin/g95_64",
                                      FFlags="-fno-second-underscore -fPIC -i4 -r8")
        #  #]
        #  #[ import additional modules needed for testing
        import struct      # allow converting c datatypes and structs
        import ecmwfbufr   # import the just created wrapper module
        import numpy as np # import numerical capabilities
        #  #]
        #  #[ test of bufr file handling
        center             = 210 # = ksec1( 3)
        subcenter          =   0 # = ksec1(16)
        LocalVersion       =   1 # = ksec1( 8)
        MasterTableVersion =   0 # = ksec1(15)
        EditionNumber      =   3 # =  ksec0( 3)
        MasterTableNumber  =   0 # = ksec1(14)
        (b,d) = BI.__get_expected_ecmwf_bufr_table_names__(center,subcenter,
                                                           LocalVersion,MasterTableVersion,
                                                           EditionNumber,MasterTableNumber)
        print "tabel name B: ",b
        print "tabel name D: ",d
        assert(b == 'B0000000000210000001')
        assert(d == 'D0000000000210000001')
        #  #]
        #  #[ read the binary data
        InputTestBUFRfile = 'Testfile.BUFR'
        fd=open(InputTestBUFRfile,'rb')
        data=fd.read()
        len(data)
        
        sizewords=len(data)/4
        words = np.array(struct.unpack("<"+str(sizewords)+"i",data))
        #print 'data[:4] = ',data[:4]
        #print 'data[:4] = ',';'.join(str(data[i]) for i in range(4) if data[i].isalnum())
        #print 'words[:4] = ',words[:4]
        assert(data[:4] == 'BUFR')
        #  #]
        #  #[ pbopen/bpbufr/pbclose tests [not yet functional]
        do_pb_test = False
        if (do_pb_test):
            cFileUnit       = 0
            bufr_error_flag = 0
            print "InputTestBUFRfile = ["+InputTestBUFRfile+"]"
            (cFileUnit,bufr_error_flag) = ecmwfbufr.pbopen(InputTestBUFRfile,'R')
            # ecmwfbufr.pbopen(cFileUnit,InputTestBUFRfile,'R',bufr_error_flag)
            print "cFileUnit = ",cFileUnit
            print "bufr_error_flag = ",bufr_error_flag
            
            buffer_size_words = 12000
            buffer_size_bytes = buffer_size_words/4
            buffer = np.zeros(buffer_size_words,dtype=np.int)
            MsgSizeBytes = 0
            bufr_error_flag = 0
            ecmwfbufr.pbbufr(cFileUnit,buffer,buffer_size_bytes,
                             MsgSizeBytes,bufr_error_flag)
            print "MsgSizeBytes = ",MsgSizeBytes
            print "buffer[0:4] = ",buffer[0:4]
            print "bufr_error_flag = ",bufr_error_flag
            
            bufr_error_flag = 0        
            ecmwfbufr.pbclose(cFileUnit,bufr_error_flag)
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
        #     2          JBPW =  32,JTAB =3000,JCTAB=3000,JCTST=9000,JCTEXT=9000,
        #     3          JWORK=4096000,JKEY=46, JTMAX=10,JTCLAS=64,JTEL=255)
        
        # TODO: read this file from python, in stead of hardcoding the numbers below
        #       and provide them as module parameters for pybufr_ecmwf.py
        MAXNRDESCR    =     20 # 300
        MAXNREXPDESCR =    140 # 160000
        MAXNRSUBSETS  =    361 # 25
        
        ktdlen = MAXNRDESCR
        # krdlen = MAXNRDELREPLFACTORS
        kelem  = MAXNREXPDESCR
        kvals  = MAXNREXPDESCR*MAXNRSUBSETS
        # jbufl  = MAXBUFRMSGSIZE
        # jsup   = LENGTHKSUP

        #  #]
        #  #[ handle BUFR tables
        print '------------------------------'

        # define our own location for storing (symlinks to) the BUFR tables
        private_BUFR_TABLES_dir = os.path.abspath("./tmp_BUFR_TABLES")
        if (not os.path.exists(private_BUFR_TABLES_dir)):
            os.mkdir(private_BUFR_TABLES_dir)
            
        # make the needed symlinks
        (Source_Dir,TarFile_to_Install) = BI.__get_source_dir__()
        ecmwf_BUFR_TABLES_dir = os.path.join(Source_Dir,"bufrtables/")
        ecmwf_BUFR_TABLES_dir = os.path.abspath(ecmwf_BUFR_TABLES_dir)
        needed_B_table    = "B0000000000210000001.TXT"
        needed_D_table    = "D0000000000210000001.TXT"
        available_B_table = "B0000000000098013001.TXT"
        available_D_table = "D0000000000098013001.TXT"
        
        # NOTE: the naming scheme used by ECMWF is such, that the table name can
        #       be derived from elements from sections 0 and 1, which can be
        #       decoded without loading bufr tables.
        # TODO: implement this
        
        source      = os.path.join(ecmwf_BUFR_TABLES_dir,  available_B_table)
        destination = os.path.join(private_BUFR_TABLES_dir,needed_B_table)
        if (not os.path.exists(destination)):
            os.symlink(source,destination)

        source      = os.path.join(ecmwf_BUFR_TABLES_dir,  available_D_table)
        destination = os.path.join(private_BUFR_TABLES_dir,needed_D_table)
        if (not os.path.exists(destination)):
            os.symlink(source,destination)
            
        # make sure the BUFR tables can be found
        # also, force a slash at the end, otherwise the library fails to find the tables
        e = os.environ
        e["BUFR_TABLES"] = private_BUFR_TABLES_dir+os.path.sep

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
            # buukey expands local ECMWF information from section 2 to the key array
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
        print "kerr = ",kerr

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
            index_lat = MAXNREXPDESCR*(s-1)+24
            index_lon = MAXNREXPDESCR*(s-1)+25
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
        # Therefore it only produces correct results when either bus0123 or bufrex
        # have been called previously on the same bufr message.....
        # However, it is not clear to me why it seems to correctly produce
        # the descriptor lists (both bare and expanded), but yet it does
        # not seem to fill the ktdlen and ktdexl values.
        
        ktdlen = 0
        ktdlst = np.zeros(MAXNRDESCR,   dtype=np.int)
        ktdexl = 0
        ktdexp = np.zeros(MAXNREXPDESCR,dtype=np.int)
        kerr   = 0
        
        print "calling: ecmwfbufr.busel():"
        ecmwfbufr.busel(ktdlen, # actual number of data descriptors
                        ktdlst, # list of data descriptors
                        ktdexl, # actual number of expanded data descriptors
                        ktdexp, # list of expanded data descriptors
                        kerr)   # error  message
        print "returned from: ecmwfbufr.busel()"
        print "kerr = ",kerr

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
        ktdlst = np.zeros(MAXNRDESCR,   dtype=np.int)
        ktdexl = 0
        ktdexp = np.zeros(MAXNREXPDESCR,dtype=np.int)
        kerr   = 0
        #  #]
        #  #[ handle BUFR tables
        print '------------------------------'

        # define our own location for storing (symlinks to) the BUFR tables
        private_BUFR_TABLES_dir = os.path.abspath("./tmp_BUFR_TABLES")
        if (not os.path.exists(private_BUFR_TABLES_dir)):
            os.mkdir(private_BUFR_TABLES_dir)
            
        # make the needed symlinks
        (Source_Dir,TarFile_to_Install) = BI.__get_source_dir__()
        ecmwf_BUFR_TABLES_dir = os.path.join(Source_Dir,"bufrtables/")
        ecmwf_BUFR_TABLES_dir = os.path.abspath(ecmwf_BUFR_TABLES_dir)
        needed_B_table    = "B0000000000098015001.TXT"
        needed_D_table    = "D0000000000098015001.TXT"
        available_B_table = "B0000000000098013001.TXT"
        available_D_table = "D0000000000098013001.TXT"
        
        # NOTE: the naming scheme used by ECMWF is such, that the table name can
        #       be derived from elements from sections 0 and 1, which can be
        #       decoded without loading bufr tables.
        # TODO: implement this
        
        source      = os.path.join(ecmwf_BUFR_TABLES_dir,  available_B_table)
        destination = os.path.join(private_BUFR_TABLES_dir,needed_B_table)
        if (not os.path.exists(destination)):
            os.symlink(source,destination)

        source      = os.path.join(ecmwf_BUFR_TABLES_dir,  available_D_table)
        destination = os.path.join(private_BUFR_TABLES_dir,needed_D_table)
        if (not os.path.exists(destination)):
            os.symlink(source,destination)
            
        # make sure the BUFR tables can be found
        # also, force a slash at the end, otherwise the library fails to find the tables
        e = os.environ
        e["BUFR_TABLES"] = private_BUFR_TABLES_dir+os.path.sep

        #  #]
        #  #[ fill sections 0,1,2 and 3

        BUFR_edition              =   4
        BUFR_code_centre          =  98 # ECMWF
        BUFR_obstype              =   3 # sounding
        BUFR_subtype_L1B          = 251 # L1B
        BUFR_table_local_version  =   1
        BUFR_table_master         =   0
        BUFR_table_master_version =  15
        BUFR_code_subcentre       =   0 # L2B processing facility
        BUFR_compression_flag     =   0 #  64=compression/0=no compression
        
        (year,month,day,hour,minute,second,
         weekday,julianday,isdaylightsavingstime) = time.localtime()

        num_subsets = 4
        
        # fill section 0
        ksec0[1-1]= 0
        ksec0[2-1]= 0
        ksec0[3-1]= BUFR_edition

        # fill section 1
        ksec1[ 1-1]=   0                       # length sec1 bytes [filled by the encoder]
        ksec1[ 2-1]= BUFR_edition              # bufr edition
        ksec1[ 3-1]= BUFR_code_centre          # originating centre
        ksec1[ 4-1]=   1                       # update sequence
        ksec1[ 5-1]=   0                       # (PRESENCE SECT 2) (0/128 = no/yes)
        ksec1[ 6-1]= BUFR_obstype              # message type 
        ksec1[ 7-1]= BUFR_subtype_L1B          # subtype
        ksec1[ 8-1]= BUFR_table_local_version  # version of local table
        ksec1[ 9-1]= (year-2000)               # Without offset year - 2000
        ksec1[10-1]= month                     # month
        ksec1[11-1]= day                       # day
        ksec1[12-1]= hour                      # hour
        ksec1[13-1]= minute                    # minute
        ksec1[14-1]= BUFR_table_master         # master table
        ksec1[15-1]= BUFR_table_master_version # version of master table
        ksec1[16-1]= BUFR_code_subcentre       # originating subcentre
        ksec1[17-1]=   0
        ksec1[18-1]=   0

        # a test for ksec2 is not yet defined

        # fill section 3
        ksec3[1-1]= 0
        ksec3[2-1]= 0
        ksec3[3-1]= num_subsets                # no of data subsets
        ksec3[4-1]= BUFR_compression_flag      # compression flag
        
        #  #]
        #  #[ define a descriptor list
        
        ktdlen = 6 # length of unexpanded descriptor list
        ktdlst = np.zeros(ktdlen,dtype=np.int)

        # add descriptor 1
        DD_D_date_YYYYMMDD = 301011 # date
        # this defines the sequence:
        # 004001 ! year
        # 004002 ! month
        # 004003 ! day

        
        
        # add descriptor 2
        DD_D_time_HHMM = 301012 # time 
        # this defines the sequence:
        # 004004 ! hour 
        # 004005 ! minute 
        
        # add descriptor 3
        DD_pressure = int('007004',10) # pressure [pa]  

        # WARNING: filling the descriptor variable with 007004 will fail
        # because python will interpret this as an octal value, and thus
        # automatically convert 007004 to the decimal value 3588

        # add descriptor 4
        DD_temperature = int('012001',10) # [dry-bulb] temperature [K]  
        
        # add descriptor 5
        DD_latitude_high_accuracy = int('005001',10) # latitude (high accuracy) [degree] 

        # add descriptor 6
        DD_longitude_high_accuracy = int('006001',10) # longitude (high accuracy) [degree] 

        ktdlst[0] = DD_D_date_YYYYMMDD
        ktdlst[1] = DD_D_time_HHMM
        ktdlst[2] = DD_pressure
        ktdlst[3] = DD_temperature
        ktdlst[4] = DD_latitude_high_accuracy
        ktdlst[5] = DD_longitude_high_accuracy

        #  #]
        #  #[ call BUXDES
        # buxdes: expand the descriptor list
        #         and fill the array ktdexp and the variable ktdexp
        #         [only usefull when creating a bufr msg with table D entries

        #iprint=0 # default is to be silent
        iprint=0
        if (iprint == 1):
            print "------------------------"
            print " printing BUFR template "
            print "------------------------"

        kdata = np.zeros(1,dtype=np.int) # list of replication factors 
        ecmwfbufr.buxdes(iprint,ksec1,ktdlst,kdata,ktdexl,ktdexp,cnames,cunits,kerr)
        print "ktdlst = ",ktdlst
        print "ktdexp = ",ktdexp
        print "ktdexl = ",ktdexl # this one seems not to be filled ...
        print "kerr = ",kerr
        #print "cnames = ",cnames
        #print "cunits = ",cunits
        #  #]
        
        # add test calls to:
        #   bufren: encode a bufr message
        #   bupkey: pack ecmwf specific key into section 2
        # and possibly to:
        #   btable: tries to load a bufr-B table
        #    [usefull for testing the presence of a needed table]
        #   get_name_unit: get a name and unit string for a given descriptor
        #   buprq: sets some switches that control the bufr library
        #
        #  #]

