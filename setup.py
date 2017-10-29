#!/usr/local/bin/python3

from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(["dmtipci/*.py", "dmtipci/third_party/*.py"])
)
