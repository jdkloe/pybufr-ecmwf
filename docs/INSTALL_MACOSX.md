## Installation on Mac OSX machines

For installation on machines running MacOSX it is essential
to ensure that you have the exact same gcc compiler installed
that was used to build the python interpreter you wish to use.
The software will only build and function correctly if this is the case.
Since Apple does not provide the gcc compiler in its default installation,
some extra steps are needed.

One easy way (although there may be other ways) is to use the homebrew
repository to install new versions of both python and gcc
(see http://brew.sh/)
The following procedure is known to work well:

* first install homebrew, if not already installed:
```bash
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
```

* then install the needed packages for gcc
```bash
brew update
brew unlink gcc
brew install gcc
```

* and install the needed packages for python2 usage:
```bash
brew tap Homebrew/python
brew install python
brew install homebrew/python/numpy
```

* or install the needed packages for python3 usage:
```bash
brew tap Homebrew/python
brew install python3
brew install homebrew/python/numpy --with-python3
```

* then get the pybufr-ecmwf software from github:
```bash
git clone https://github.com/jdkloe/pybufr-ecmwf.git
cd pybufr-ecmwf
```
(note that MacOSX comes with a preinstalled version of git,
 I hope it is recent enough, otherwise homebrew provides a newer version)

* finally install the pybufr-ecmwf software for python2:
```bash
python setup.py build
python ./unittests.py
python setup.py install --user --user --prefix=
```

* or install the pybufr-ecmwf software for python3:
```bash
python3 setup.py build
python3 ./unittests.py
python3 setup.py install --user
```

The --user installs in your user account. If you don't want that, add
sudo in front of the install step.
The '--prefix=' switch for the python2 case actually is a workaround
for a bug in the install script that occurs in some specific setups.
It may not be necessary for you, but it will not hurt either.
see:  see http://stackoverflow.com/questions/4495120/combine-user-with-prefix-error-with-setup-py-install

If you know of other ways to install it, please let me know.

J. de Kloe, 18-Aug-2016.
