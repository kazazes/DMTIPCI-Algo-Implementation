DMTIPCI
=======

This is a rudementiary implementation of [US20120173228 A1](http://www.google.com/patents/US8321205).

[A Comparison Between Patent Literature and Implementation](https://github.com/kazazes/DMTIPCI/blob/master/docs/lit-vs-imp.txt.md)

### Building Cython based executable on Mac OS X

At DMTIPCI folder, run `build.sh` to build. A new folder `dist` will be made containing executables (only `shell`), modules (`.so` dynamic libraries), and the dictionary text file. Zip this folder to deliver to another computer running Mac OS X 10.6+ (64 bit only).

Script `build.sh` assumes official Python 3 (setup package acquired from https://www.python.org/) installation location. And it currently assumes version 3.4 will be used. Before compilation, Cython also has to be installed (`pip3 install cython`). Xcode is required for compilation.

### Building Cython based executable on Windows

At DMTIPCI folder, first run `"C:\Program Files\Microsoft Visual Studio 10.0\VC\vcvarsall.bat"
`, then run `build.bat` to build. Folder `dist-win` will be made containing executables (only `shell`), modules and dictionary text file. Zip this folder to deliver to another computer running Windows XP+ (32/64bit).

Compilation requires Visual C++ Express 2010 (http://www.visualstudio.com/en-us/downloads/download-visual-studio-vs#DownloadFamilies_4 - Note: no other version can be used for compatibility with Python 3.4), Python 3.4 official Windows package, and Cython installed via `pip3 install cython`. After installation is completed, make sure `C:\Python34;C:\Python34\Scripts;` is inserted into `PATH` environment variable. Minimum Windows version is XP 32bit.

Script `build.bat` assumes Windows XP 32bit, Python 3.4, Visual Studio and Cython to be installed in their default location and settings.

Note: due to a bug with either Python distutil or Cython on Windows causing MSVC unable to compile `__init__.py` - the empty package place holder file. As far as program running is concerned, this presents no harm. A workaround in the batch file is provided to address this issue.

Known issue: Windows console do not display unicode characters. When such strings are encountered, it throws an exception and quits. Currently there are no workarounds. Certain entries may contain such characters due to their Hispanic nature. It makes sense to notify Windows user of this problem prior to working with the program.
