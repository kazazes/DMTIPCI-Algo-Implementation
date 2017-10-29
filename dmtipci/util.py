#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#cython: language_level=3, boundscheck=False


import os
import json
import pickle


RESET       = "\033[0m"
BLACK       = "\033[30m"
RED         = "\033[31m"
GREEN       = "\033[32m"
YELLOW      = "\033[33m"
BLUE        = "\033[34m"
MAGENTA     = "\033[35m"
CYAN        = "\033[36m"
WHITE       = "\033[37m"
BOLDBLACK   = "\033[1m\033[30m"
BOLDRED     = "\033[1m\033[31m"
BOLDGREEN   = "\033[1m\033[32m"
BOLDYELLOW  = "\033[1m\033[33m"
BOLDBLUE    = "\033[1m\033[34m"
BOLDMAGENTA = "\033[1m\033[35m"
BOLDCYAN    = "\033[1m\033[36m"
BOLDWHITE   = "\033[1m\033[37m"


def load_pickle(filename, kind, required_ver):
    ret = {}
    try:
        if os.path.exists(filename):
            print("Loading", kind, "from", filename, "...")
            ret = pickle.load(open(filename, 'rb'))
            if not '---VERSION---' in ret or ret['---VERSION---'] < required_ver:
                ret = {}
            else:
                del ret['---VERSION---']    # remove, as it's not needed during runtime
    except:
        pass
    return ret


def save_pickle(data, filename, version):
    data['---VERSION---'] = version
    pickle.dump(data, open(filename + '.json.pd', 'wb'))
    open(filename + '.json', 'w', encoding='utf-8', errors='ignore').write(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=4))
    del data['---VERSION---']
