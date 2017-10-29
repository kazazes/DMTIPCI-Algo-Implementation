#!/usr/local/bin/python3


import os
import json
import pickle
import glob
import time
from dmtipci.dictionary import Dictionary
from dmtipci.find       import Finder
from dmtipci.debug      import _assert, __LINE__, __FILE__
from dmtipci            import util, system


WORDNET_CACHE_VERSION = system.VERSION


def parse_wordnet_line(line, kind):
    line = line.strip()
    # {...} works for nouns and verbs
    if line.startswith('{') and line.endswith('}'):
        # information regarding the words
        def_start   = line.find('(')
        def_end     = line.rfind(')')
        def_content = line[def_start+1:def_end-1]
        # def_content is supposedly the definition of the word (aka gloss)
        line        = line[1:def_start]
        # information about word usage context in square brackets: [] are not used, they have to be ignored
        line_p      = ''
        in_bracket  = False
        for char in line:
            if char == '[':
                in_bracket = True
            elif char == ']':
                in_bracket = False
                continue
            if not in_bracket:
                line_p += char
        elements    = [x.strip(',1234567890') for x in line_p.strip().split(' ') if len(x.strip(',')) > 0]
        # process words formatted like noun.plant:pome
        for i in range(0, len(elements)):
            element = elements[i]
            semi_c  = element.rfind(':')
            if '.' in element and semi_c > 0:
                element = element[semi_c + 1:]
                elements[i] = element
        subject     = elements[0]
        if not subject.endswith(',@'):  # only a single hypernym? disregard
            i_hypernyms = []    # indirect hypernyms
            for i in range(1, len(elements)):
                if elements[i].endswith(',@') or elements[i].endswith(';c') or elements[i].endswith(';r') or elements[i].endswith(';u') or elements[i].endswith(',~'):
                    element = elements[i][:-2]  # remove ,@
                    i_hypernyms.append(element.strip(',1234567890').upper())
                elif elements[i].endswith(',@i') or elements[i].endswith(',~i'):
                    element = elements[i][:-3]
                    i_hypernyms.append(element.strip(',1234567890').upper())
            return {
                'subject':      subject.upper(),
                'i_hypernyms':  i_hypernyms
            }
    return {}


def load_wordnet():
    wordnet_cache_dir   = 'wordnet_db/cache/'
    wordnet_files       = 'wordnet_db/dbfiles/'
    os.makedirs(wordnet_cache_dir, exist_ok=True)
    db = util.load_pickle(wordnet_cache_dir + 'wordnet.json.pd', 'wordnet', WORDNET_CACHE_VERSION)
    if len(db) != 0:
        return db
    # Note: Only hypernyms are being parsed.
    # Hypernyms are those with ,@ pointer syntax in wordnet, according to http://wordnet.princeton.edu/wordnet/man/wninput.5WN.html .
    # Refer to https://github.com/kazazes/DMTIPCI/issues/1 for the reasons we are only interested in hypernyms.
    # adj and adv are temporarily ignored because they use a more complex format
    for filename in glob.glob(wordnet_files + 'noun.*'):
        # nouns
        print("Parsing", filename, "...")
        for line in open(filename, 'r').readlines():
            l = parse_wordnet_line(line, 'noun')
            if l:
                hns = []
                if l['subject'] in db:
                    hns = db[l['subject']]
                for key in l['i_hypernyms']:
                    if not key in hns:
                        hns.append(key)
                if len(hns) > 0:
                    db[l['subject']] = hns
    for filename in glob.glob(wordnet_files + 'verb.*'):
        # nouns
        print("Parsing", filename)
    util.save_pickle(db, wordnet_cache_dir + 'wordnet', WORDNET_CACHE_VERSION)
    if len(db) == 0:
        print("DMTIPCI Evaluation requires WordNet, instructions:")
        print("- Download from http://wordnetcode.princeton.edu/wn3.1.dict.tar.gz")
        print("- Unpack and get a folder named 'dict', rename it to 'wordnet_db'")
        print("- Place 'wordnet_db' in the same folder as", __FILE__())
        print("- Re-run the script")
        quit()
    return db


def main():
    db = load_wordnet()
    print('WordNet has', len(db), 'entries.')
    master_text = 'dict/pg29765.txt'
    word_freq   = 'dict/pg29765_word_freq'
    word_infl   = 'dict/pg29765_word_infl'
    d = Dictionary()
    d.updateFromGutenbergText(master_text)
    d.updateWordInflection(word_infl)
    d.updateWordFrequency(word_freq)
    finder = Finder(d)
    precision_total = 0
    coverage_total  = 0
    total_counted   = 0
    last_checkpoint = time.time()
    print('Evaluation started.')
    for idx, word in enumerate(db):
        dst = db[word]
        src = finder.find(word, debug_print=False)
        if src and 'N' in src:
            src = src['N']
        if not src:
            continue
        total_counted += 1
        dst_ = []
        for e in dst:
            dst_ += e.split('_')
        # print(src)
        # print(dst)
        # print(dst_)
        correct = 0
        for e in src:
            for e_ in dst_:
                if e in e_:
                    correct += 1
        precision_total += correct / len(src)
        # print('Precision', correct, 'of', len(src))
        correct = 0
        for e_ in dst_:
            for e in src:
                if e in e_:
                    correct += 1
        # print('Coverage', correct, 'of', len(dst_))
        coverage_total += correct / len(dst_)
        checkpoint = time.time()
        if checkpoint - last_checkpoint >= 15:
            print('Precision: %.8f, Coverage (Recall): %.8f' % (precision_total / total_counted, coverage_total / total_counted), ' %d%%' % (100 * (idx + 1) / len(db)))
            last_checkpoint = checkpoint
    print('Final Precision: %.8f, Coverage (Recall): %.8f' % (precision_total / total_counted, coverage_total / total_counted))


if __name__ == '__main__':
    print("╔╦╗╔╦╗╔╦╗╦╔═╗╔═╗╦")
    print(" ║║║║║ ║ ║╠═╝║  ║")
    print("═╩╝╩ ╩ ╩ ╩╩  ╚═╝╩")
    print("- DMTIPCI Eval. -")
    print("    v" + str(system.VERSION) + "    ")
    main()
