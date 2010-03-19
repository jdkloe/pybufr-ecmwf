#!/usr/bin/env python

#  #[ documentation
#
# This module implements building the ECMWF BUFR library and creation of
# a python interface around the BUFR library provided by
# ECMWF to allow reading and writing the WMO BUFR file standard.
#
# Note about the use of the "#  #[" and "#  #]" comments:
#   these are folding marks for my favorite editor, emacs, combined with its
#   folding mode
#   (see http://www.emacswiki.org/emacs/FoldingMode for more details)
# Please do not remove them.
#
# For details on the revision history, refer to the log-notes in
# the mercurial revisioning system hosted at google code.
#
# Written by: J. de Kloe, KNMI (www.knmi.nl),
#
# License: GPL v2.
#
#  #]
#  #[ imported modules
import os          # operating system functions
#import sys         # system functions
import re          # regular expression handling
import glob        # allow for filename expansion
import tarfile     # handle tar archives
import subprocess  # support running additional executables
import shutil      # portable file copying functions
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
#  #[ some helper subroutines
def run_shell_command(cmd,libpath=None,catch_output=True,
                      verbose=True):
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
            
    if (verbose):
        print "Executing command: ",cmd
        
    if (catch_output):
        subpr = subprocess.Popen(cmd,
                                 shell=True,
                                 env=e,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        
        # wait until the child process is done
        # subpr.wait() # seems not necessary when catching stdout and stderr
            
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
#  #]

class InstallBUFRInterfaceECMWF:
    #  #[
    """
    a class that downloads and builds the interface between the ECMWF
    BUFR library and python
    """
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
        self.debug_f2py_c_api           = debug_f2py_c_api

        # save the verbose setting
        self.verbose = verbose

        # save the location to be used for installing the ECMWF BUFR library
        self.ecmwf_bufr_lib_dir  = "./ecmwf_bufr_lib"

        # define the names of the library and shared object files
        # that will be created by this class
        self.bufr_lib_file = "libbufr.a"
        self.wrapper_name = "ecmwfbufr.so"

        #  #]
    def build(self):
        #  #[
        
        # check for the presence of the library
        if (os.path.exists(self.bufr_lib_file)):
            pass
            #print "library seems present"
        else:
            print "Entering installation sequence:"
            self.install()

        if (os.path.exists(self.wrapper_name)):
            #print "python wrapper seems already present"
            return
        else:
            print "Entering wrapper generation sequence:"
            (source_dir,tarfile_to_install) = self.get_source_dir()
            self.generate_python_wrapper(source_dir)

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

        # NOTE: this one is copied for now into BUFRInterfaceECMWF
        # since I need it there as well.
        # TODO: solve this in a more elegant way.
        
        # save the location to be used for installing the ECMWF BUFR library
        ecmwf_bufr_lib_dir  = "./ecmwf_bufr_lib"
        list_of_bufr_tarfiles = glob.glob(os.path.join(ecmwf_bufr_lib_dir,
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

        source_dir = os.path.join(ecmwf_bufr_lib_dir,bufr_dir)

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
        else:
            #(lines_stdout,lines_stderr) = \
            #      run_shell_command(cmd,libpath=libpath)
            run_shell_command(cmd,libpath=libpath,catch_output=False)
        #  #]

        #  #[ check the result
        fullname_bufr_lib_file = os.path.join(source_dir,self.bufr_lib_file)
        if (os.path.exists(fullname_bufr_lib_file)):
            print "Build seems successfull"
            # remove any old symlink that might be present
            if (os.path.exists(self.bufr_lib_file)):
                os.remove(self.bufr_lib_file)
            # make a symlink in a more convenient location
            os.symlink(fullname_bufr_lib_file,self.bufr_lib_file)
            # make a symlink to the directory holding the provided
            # BUFR tables, to more convenient (constant) name
            fullname_table_dir = os.path.join(source_dir,"bufrtables")
            table_dir = "ecmwf_bufrtables"
            os.symlink(fullname_table_dir,table_dir)
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
    def check_presence(self,command):
        #  #[
        if (self.verbose):
            print "checking for presence of command: "+str(command)
        
        result = []

        if (command == None):
            return False
        
        # get the real command, in case it was an alias
        cmd = "which "+command
        (lines_stdout,lines_stderr) = run_shell_command(cmd,catch_output=True)

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
            run_shell_command(cmd,libpath=libpath,catch_output=False)

        # now execute the just generated test program to verify if we succeeded
        cmd = fortran_test_executable
        if (libpath == ""):
            (lines_stdout,lines_stderr) = run_shell_command(cmd)
        else:
            (lines_stdout,lines_stderr) = run_shell_command(cmd,libpath=libpath)

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
            run_shell_command(cmd,libpath=libpath,catch_output=False)

        # now execute the just generated test program to verify if we succeeded
        cmd = c_test_executable
        if (libpath == ""):
            (lines_stdout,lines_stderr) = run_shell_command(cmd)
        else:
            (lines_stdout,lines_stderr) = run_shell_command(cmd,libpath=libpath)

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
    def generate_python_wrapper(self,source_dir):
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
            #       run_shell_command(cmd,catch_output=True)
        else:
            #(lines_stdout,lines_stderr) = \
            #       run_shell_command(cmd,libpath=libpath,
            #                              catch_output=True)
            run_shell_command(cmd,libpath=libpath,catch_output=False)
    
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
        if (self.debug_f2py_c_api):
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
            #       run_shell_command(cmd,catch_output=False)
        else:
            #(lines_stdout,lines_stderr) = \
            #       run_shell_command(cmd,libpath=libpath,
            #                              catch_output=True)
            run_shell_command(cmd,libpath=libpath,catch_output=False)
            
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
    #  #]

if __name__ == "__main__":
    print "Building ecmwfbufr.so interface:"
    #  #[ define how to build the library and interface
    
    # instantiate the class, and build library if needed
    # (4 different tests defined for this step, with 4 different compilers)
    
    testcase = 1 # test default g95
    #testcase = 2 # test default gfortran
    #testcase = 3 # test custom gfortran
    #testcase = 4 # test custom g95-32 bit
    #testcase = 5 # test custom g95-64 bit
    
    if (testcase == 1):
        # tested at my laptop at home with a g95 v.0.92 (32-bit)
        # in my search PATH
        # successfully tested 19-Mar-2010
        BI = InstallBUFRInterfaceECMWF(verbose=True)
        #BI = InstallBUFRInterfaceECMWF(verbose=True,debug_f2py_c_api=True)
    elif (testcase == 2):
        # tested at my laptop at home with a systemwide
        # gfortran v4.3.2 installed
        # successfully tested 19-Mar-2010
        BI = InstallBUFRInterfaceECMWF(verbose=True,
                                       preferred_fortran_compiler='gfortran')
    elif (testcase==3):
        # note that the "-O" flag is allways set for each fortran compiler
        # so no need to specify it to the fortran_flags parameter.
        
        # tested at my laptop at home with a gfortran v4.4.0 installed
        # in a user account
        # successfully tested 19-Mar-2010
        BI = InstallBUFRInterfaceECMWF(verbose=True,
                    fortran_compiler="/home/jos/bin/gfortran_personal",
                    fortran_ld_library_path="/home/jos/bin/gcc-trunk/lib64",
                    fortran_flags="-fno-second-underscore -fPIC")
    elif (testcase==4):
        # tested at my laptop at home with a g95 v0.92 (32-bit) installed
        # in a user account
        # successfully tested 19-Mar-2010
        BI = InstallBUFRInterfaceECMWF(verbose=True,
                    fortran_compiler="/home/jos/bin/g95_32",
                    fortran_flags="-fno-second-underscore -fPIC -i4 -r8")
    elif (testcase==5):
        # tested at my laptop at home with a g95 v0.92 (64-bit)
        # installed in a user account
        # successfully tested 19-Mar-2010
        BI = InstallBUFRInterfaceECMWF(verbose=True,
                    fortran_compiler="/home/jos/bin/g95_64",
                    fortran_flags="-fno-second-underscore -fPIC -i4 -r8")
    #  #]

    # Build ecmwfbufr.so interface
    BI.build()
    
    #  #[ check for success
    so_file = "ecmwfbufr.so"
    if os.path.exists(so_file):
        print "successfully build:",so_file
    else:
        print "cannot find file:",so_file
        print "something seems wrong here ..."
        raise InterfaceBuildError
    #  #]
