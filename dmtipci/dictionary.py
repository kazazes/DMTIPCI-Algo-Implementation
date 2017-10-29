#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#cython: language_level=3, boundscheck=False

import os
import json
import pickle

from .third_party   import inflect
from .debug         import _assert, __LINE__, __FILE__
from .              import util, system

class Dictionary:

    def __init__(self):
        self.dictionary = {}
        self.word_freq  = {}
        self.word_infl  = {}
        self.version    = system.VERSION

    @staticmethod
    def isFloat(word):
        try:
            float(word)
            return True
        except ValueError:
            return False

    @staticmethod
    def getVariationPOS(variation):
        if variation.find(' n.') > 0:
            return ['N']
        elif variation.find(' a.') > 0:
            if variation.find('as a noun') > 0:
                return ['N', 'A']
            return ['A']
        elif variation.find(' adv.') > 0:
            return ['ADV']
        elif variation.find(' prep.') > 0:
            return ['PREP']
        elif variation.find(' v.i.') > 0 or variation.find(' v. i.') > 0:
            return ['VI']
        elif variation.find(' v.t.') > 0 or variation.find(' v. t.') > 0:
            return ['VT']
        elif variation.find(' p.p.') > 0 or variation.find(' p. p.') > 0:
            return ['PP']
        return []

    def undecorateWord(self, word):
        # remove unnecessary marks from a word, for statistics
        bare_word = word.strip('.,!?;:\'" \t\n#()&@+=-*/$[]{}|£§').upper()
        if not bare_word in self.word_freq and bare_word in self.word_infl:
            # flawed, just pick the first POS tag
            pos = next(iter(self.word_infl[bare_word]))
            # flawed, pick the first inflected word
            bare_word = self.word_infl[bare_word][pos][0]
        return bare_word

    def updateFromGutenbergText(self, filename):
        # dictionary is in the following format:
        # ----------------------------------------
        # WORD
        # Word variation, incl POS, and etymology
        #
        # Defn: Definitions
        # ----------------------------------------
        self.dictionary = {}
        filename_json   = filename.replace('.txt', '.json')
        filename_pd     = filename_json + '.pd'
        self.dictionary = util.load_pickle(filename_pd, 'dictionary', self.version)

        if len(self.dictionary) == 0:
            print("Updating dictionary from Gutenberg text:", filename, "...")
            current_word        = ''
            current_variation   = ''
            current_def         = []
            variation_solid     = False
            for idx, line in enumerate(open(filename, 'r', encoding='utf-8', errors='ignore').readlines()):
                # cleanup a line
                line = line.strip()
                if line.startswith('*** '):
                    # Gutenberg marker
                    continue
                if len(line) == 0:
                    # empty line
                    if current_word and current_variation and not variation_solid:
                        # variation can come across multiple lines
                        variation_solid = True
                    elif current_word and current_variation and variation_solid and current_def:
                        # append an entry to definition
                        current_def[len(current_def) - 1] = current_def[len(current_def) - 1].strip()
                        # 'Note:' section in definitions are being ignored because they usually contain usage information and explanation of related terms. Since they are not like 'definitions', they won't be able to contribute to predicate selection.
                        if current_def[len(current_def) - 1].startswith('Note: '):
                            del current_def[len(current_def) - 1]
                        # A situation where the previous definition is just a class (i.e. 3. (bot.) or 5. (law)) and the real definition came in 'current_def', merge with previous
                        elif len(current_def) >= 2 and len(current_def[len(current_def) - 2]) > 0 and current_def[len(current_def) - 2][0].isdigit() and current_def[len(current_def) - 2][-1:] == ')':
                            current_def[len(current_def) - 2] += ' ' + current_def[len(current_def) - 1]
                            del current_def[len(current_def) - 1]
                        current_def.append('')
                    continue
                if line.isupper():
                    # upper case indicates a new word
                    if current_word and current_variation and current_def and variation_solid:
                        # collect the current word
                        if not current_word in self.dictionary:
                            self.dictionary[current_word] = {}
                        if not current_variation in self.dictionary[current_word]:
                            self.dictionary[current_word][current_variation] = [x for x in current_def if len(x) > 0]
                    # start a new word
                    current_word        = line
                    current_variation   = ''
                    current_def         = []
                    variation_solid     = False
                    continue
                if current_word and not current_variation:
                    # new variation segment
                    current_variation   = line
                    continue
                if current_word and current_variation and not variation_solid:
                    # variation continued
                    current_variation   += ' ' + line
                    continue
                if current_word and current_variation and variation_solid:
                    # definitions
                    if len(current_def) == 0:
                        current_def.append('')
                    current_def[len(current_def) - 1] += ' ' + line.replace('Defn: ', '')
                    continue
            util.save_pickle(self.dictionary, filename.replace('.txt', ''), self.version)

    def updateWordFrequency(self, filename):
        _assert(len(self.dictionary) > 0, __FILE__(), __LINE__(), "Word frequency update requires dictionary to be loaded beforehand.")
        _assert(len(self.word_infl) > 0, __FILE__(), __LINE__(), "Word frequency update requires inflection update beforehand.")
        self.word_freq  = {}
        filename_json   = filename + '.json'
        filename_pd     = filename_json + '.pd'
        self.word_freq  = util.load_pickle(filename_pd, 'word frequencies', self.version)

        if len(self.word_freq) == 0:
            print("Writing word frequency to", filename, "...")
            self.word_freq = {}
            sum_all_words = 0
            for word in self.dictionary:
                for variation in self.dictionary[word]:
                    for definition in self.dictionary[word][variation]:
                        for def_word in definition.split(' '):
                            bare_word = self.undecorateWord(def_word)
                            if not bare_word in self.dictionary and bare_word in self.word_infl:
                                # flawed, just pick the first POS tag
                                pos = list(self.word_infl[bare_word].keys())[0]
                                # flawed, pick the first inflected word
                                bare_word = self.word_infl[bare_word][pos][0]
                            # don't count empties, numbers
                            if len(bare_word) == 0 or bare_word.isdecimal() or bare_word.isdigit() or self.isFloat(bare_word):
                                continue
                            sum_all_words += 1
                            if not bare_word in self.word_freq:
                                self.word_freq[bare_word] = 1
                            else:
                                self.word_freq[bare_word] += 1
            print('----- Top 100 Words ----')
            top_words = []
            for idx, w in enumerate(sorted(self.word_freq, key=self.word_freq.get, reverse=True)):
                if idx >= 100:
                    break
                top_words.append(w)
            self.word_freq['---SUM---'] = sum_all_words
            # cut off logic: any word above this count is never likely to be a target match, so there will be no need to look them up
            # the current 'cut off' word is 'ZOÖL', review the top 100 word list for the words being cut off
            try:
                # deal with Windows quirks
                print(top_words)
                print('Cut off set to ZOÖL', self.word_freq['ZOÖL'])
            except:
                pass
            self.word_freq['---CUTOFF---'] = self.word_freq['ZOÖL']
            util.save_pickle(self.word_freq, filename.replace('.txt', ''), self.version)

    def updateWordInflection(self, filename):
        _assert(len(self.dictionary) > 0, __FILE__(), __LINE__(), "Word inflection update requires dictionary to be loaded.")
        self.word_infl  = {}
        filename_json   = filename + '.json'
        filename_pd     = filename_json + '.pd'
        self.word_infl  = util.load_pickle(filename_pd, 'word inflection map', self.version)

        if len(self.word_infl) == 0:
            # Note: This inflection map has a flaw when not used with POS tagger.
            #
            # A word like 'SAW' has a match in the dictionary as a noun word (as
            # in 'SAW BLADE'), the upper implementation may never choose to look
            # up this inflection table, and discover it's also a past tense of
            # 'SEE'.
            # 
            # This flaw is currently ignored due to minority nature of such words.
            #
            # Note: Verb forms are not yet fully implemented
            #
            print("Writing word inflection map to", filename, "...")
            self.word_infl = {}
            p = inflect.engine()
            for word in self.dictionary:
                for variation in self.dictionary[word]:
                    pos = self.getVariationPOS(variation)
                    if 'N' in pos:
                        # add plural for nouns
                        plural = p.plural(word.lower()).upper()
                        if not plural in self.word_infl:
                            self.word_infl[plural] = {}
                        if not 'N' in self.word_infl[plural]:
                            self.word_infl[plural]['N'] = []
                        self.word_infl[plural]['N'].append(word)
                    elif 'VT' in pos or 'VI' in pos:
                        # handling present participles
                        # warning: past tense / participles are not yet handled
                        pp = p.present_participle(word.lower()).upper()
                        if not pp in self.word_infl:
                            self.word_infl[pp] = {}
                        if not 'VT' in self.word_infl[pp]:
                            self.word_infl[pp]['VT'] = []
                        self.word_infl[pp]['VT'].append(word)
            util.save_pickle(self.word_infl, filename.replace('.txt', ''), self.version)

    def getWord(self, bare_word):
        _assert(len(self.dictionary) > 0, __FILE__(), __LINE__(), "Dictionary is still empty.")
        if bare_word in self.dictionary:
            return self.dictionary[bare_word]
        return None

    def getWordFrequency(self, bare_word):
        _assert(len(self.word_freq) > 0, __FILE__(), __LINE__(), "Dictionary word frequency is still empty.")
        _assert(len(self.word_infl) > 0, __FILE__(), __LINE__(), "Dictionary word inflection map is still empty.")
        if bare_word in self.word_freq:
            # boundary cutoff, if it's more frequent than 'WHICH' (incl.) or less frequent than 1 (incl.)
            if (self.word_freq[bare_word] >= self.word_freq["---CUTOFF---"]) or self.word_freq[bare_word] <= 1:
                return 0
            return self.word_freq[bare_word]
        return 0
