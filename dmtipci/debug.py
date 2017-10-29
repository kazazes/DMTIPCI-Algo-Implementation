#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#cython: language_level=3, boundscheck=False

import sys
import inspect

def __LINE__():
    try:
        raise Exception
    except:
        try:
            return sys.exc_info()[2].tb_frame.f_back.f_lineno
        except:
            return 0


def __FILE__():
    try:
        return inspect.getouterframes(inspect.currentframe())[1][0].f_code.co_filename
    except:
        return ''


def _assert(condition, filename, line, content=None):
    if not condition:
        print("FATAL ERROR! at", filename + ":" + str(line))
        if content:
            print(content)
        sys.exit(1)
