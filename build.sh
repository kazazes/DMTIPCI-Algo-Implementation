#!/bin/bash

PYTHON_DEV="/Library/Frameworks/Python.framework/Versions/"
PYTHON_VER="3.4"

PYTHON_INC=$PYTHON_DEV$PYTHON_VER"/include/python"$PYTHON_VER"m"
PYTHON_LIB=$PYTHON_DEV$PYTHON_VER"/lib"
LINK_TARGET="python"$PYTHON_VER"m"

rm -rf ./dist
rm -rf ./build
mkdir ./dist
python3 setup.py build_ext
cython -3 --embed -o ./dist/shell.c ./shell.py
gcc -Os -I$PYTHON_INC -L$PYTHON_LIB -o ./dist/shell ./dist/shell.c -l$LINK_TARGET -lpthread -lm -lutil -ldl
cp -R build/lib.*/* dist/
mkdir dist/dmtipci/third_party
mv dist/inflect.so dist/dmtipci/third_party
rm -rf ./build
rm ./dist/shell.c

mkdir dist/dict
cp dict/pg29765.txt dist/dict
