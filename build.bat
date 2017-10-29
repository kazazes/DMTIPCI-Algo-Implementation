@echo off
rd /s /q dist-win
rd /s /q build
md dist-win
python setup.py build_ext
python setup.py build_ext
cython -3 --embed -o dist-win\shell.c shell.py
cl dist-win\shell.c /I "C:\Python34\include" /link /libpath:"C:\Python34\libs" /out:dist-win\shell.exe
del shell.obj
del dist-win\shell.lib
del dist-win\shell.exp
del dist-win\shell.c
md dist-win\dmtipci
xcopy build\lib.win32-3.4\*.* dist-win /s
md dist-win\dmtipci\third_party
move dist-win\inflect.pyd dist-win\dmtipci\third_party
md dist-win\dict
copy dict\pg29765.txt dist-win\dict
del dist-win\dmtipci\__init__.pyd

