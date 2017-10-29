#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#cython: language_level=3, boundscheck=False

import os
import cmd
import argparse
from dmtipci.dictionary import Dictionary
from dmtipci.find       import Finder
from dmtipci            import system


class Shell(cmd.Cmd):
    intro   = '! Welcome to DMTIPCI shell. Type ? to list commands.\n  . Type any word to query:\n    apple <return>\n  . Type an empty line to quit.\n'
    prompt  = '(DMTIPCI) '

    def __init__(self, args):
        cmd.Cmd.__init__(self)
        master_text = 'dict/pg29765.txt'
        word_freq   = 'dict/pg29765_word_freq'
        word_infl   = 'dict/pg29765_word_infl'
        d = Dictionary()
        d.updateFromGutenbergText(master_text)
        d.updateWordInflection(word_infl)
        d.updateWordFrequency(word_freq)
        self.dictionary = d
        self.args = args
        self.finder = Finder(d)
        self.last_lookup = None
        print('')
        if args.auto_definition:
            print('! Using automatic definition enumeration mode. Type . to switch to manual.')
        else:
            print('! Using manual definition enumeration mode. Type . to switch to automatic.')

    def precmd(self, line):
        if len(line.strip()) == 0:
            return 'quit'
        elif line.strip() == '.':
            self.args.auto_definition = not self.args.auto_definition
            if args.auto_definition:
                print('! Using automatic definition enumeration mode.')
            else:
                print('! Using manual definition enumeration mode.')
            line = 'emptyinternal'
        elif line.strip().isdigit():
            line = 'seldef ' + line
        elif not line.lower().startswith('lookup'):
            line = 'lookup ' + line
        return line

    def do_lookup(self, arg):
        'Lookup a word: LOOKUP APPLE'
        self.last_lookup = arg
        self.finder.find(arg, def_mode=(0 if self.args.auto_definition else -1))

    def do_seldef(self, arg):
        'Select definition of a word: SELDEF 1'
        self.finder.find(self.last_lookup, def_mode=int(arg))

    def do_emptyinternal(self, arg):
        pass

    def do_quit(self, arg):
        'Quit'
        return True


if __name__ == '__main__':
    print("╔╦╗╔╦╗╔╦╗╦╔═╗╔═╗╦")
    print(" ║║║║║ ║ ║╠═╝║  ║")
    print("═╩╝╩ ╩ ╩ ╩╩  ╚═╝╩")
    print("- DMTIPCI Shell -")
    print("    v" + str(system.VERSION) + "    ")
    parser = argparse.ArgumentParser(description='DMTIPCI Shell')
    parser.add_argument('-a', '--auto-definition', action='store_true', help='Automatically enumerate all definitions (by default, manual definition selection is required)')
    args = parser.parse_args()
    shell = Shell(args)
    shell.cmdloop()
