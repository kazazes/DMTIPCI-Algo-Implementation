#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#cython: language_level=3, boundscheck=False

import os
import json
from .dictionary    import Dictionary
from .              import util, system


class Finder:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def _getDefinitionUnigramSequence(self, bare_word, pos, definition, master_unigram):
        # For each definition, break down and flatten all words, like unigram, and find word frequencies
        unigram     = master_unigram
        sequence    = []
        # include the original word in the unigram
        unigram[bare_word]  = 1
        for word in definition.split(' '):
            # is this a taxonomy? like (Bot.) or (Hort.)
            if word.startswith('(') and word.endswith('.)'):
                continue
            if word == '{':
                break
            word        = self.dictionary.undecorateWord(word)
            word_freq   = self.dictionary.getWordFrequency(word)
            # Upon encounter of the original lookup word, stop look further in the sequence.
            # *WARNING* This decision is arbitrary with no support of scientific evidence. (1)
            # *WARNING* Removing this statement will result in a 2 point drop in precision, and a 2 point rise in coverage.
            if word == bare_word:
                break
            if word == 'OBS':   # obsolete usage comes after
                break
            # According to the procedures in the patent, potential predicates are all in the same part of speech. Plus, it's not trivial to recognize the meaning of words and their importance if we were to count occurrence for other POS. For instance, when we look for "APPLE", we may encounter the word "CULTIVATED" which may be important in sub-level predicate lookups. However, when sub-level definition contains words like "GROW", or "PRODUCE", it's not possible to consider them as the same meaning as "CULTIVATED" therefore the word "CULTIVATED" will be of no use.
            # In the procedure below, we rule out all other POSes in the unigram
            variations = self.dictionary.getWord(word)
            if not variations:
                continue
            pos_match = False
            for variation in variations:
                v_pos = Dictionary.getVariationPOS(variation)
                m_pos = [x for x in v_pos if x in pos]
                if len(m_pos) > 0:
                    pos_match = True
                    break
            if not pos_match:
                continue
            if not word in unigram and word_freq > 0:
                unigram[word] = 1
                sequence.append(word)
            elif word in unigram and word_freq > 0:
                unigram[word] += 1
        return (unigram, sequence)

    def _getDefinitionWordWeights(self, defword, pos, variations, unigram):
        weights         = []
        definition_idx  = -1
        # print('!!', defword)
        # iterate through level-2-word variations
        for l2_v in sorted(variations.keys()):
            # match identical POS
            l2_pos = Dictionary.getVariationPOS(l2_v)
            m_pos = [x for x in l2_pos if x in pos]
            if len(m_pos) == 0:
                continue
            # print(util.BOLDWHITE + str(variations[l2_v]) + util.RESET)
            # count how many level-2-word definition words matched original definition unigram
            for idx, l2_def in enumerate(variations[l2_v]):
                # print(' -', l2_def)
                def_weights = []
                for l2_w in l2_def.split(' '):
                    # is this a taxonomy? like (Bot.) or (Hort.)
                    if l2_w.startswith('(') and l2_w.endswith('.)'):
                        continue
                    l2_bw = self.dictionary.undecorateWord(l2_w)
                    # Upon encounter of definition-word, stop look further
                    # *WARNING* Same as (1), this is arbitrary with no scientific evidence.
                    if l2_bw == defword:
                        continue
                    if l2_bw in unigram:
                        weights.append(l2_bw)
                        def_weights.append(l2_bw)
                # Threshold: requiring unigram match to be at least 2 to count this definition, if it only has 1 unigram match, it'll be discarded
                # print(' ', l2_def, def_weights)
                if len(def_weights) >= system.MINIMUM_UNIGRAM_MATCH_PER_DEFINITION:
                    # print(' =', def_weights)
                    if len(def_weights) > len(weights):
                        weights = def_weights
                        definition_idx = idx
        # print('!!-', weights)
        return (definition_idx, weights)

    def _findCandidatesFromDefinitions(self, bare_word, pos, definitions, debug_print=True):
        retval      = []
        # using a 'unigram' variable, a single word will only be counted once across all definitions
        unigram     = {}
        master_candidates   = {}
        for definition in definitions:
            (unigram, sequence) = self._getDefinitionUnigramSequence(bare_word, pos, definition, unigram)
            # if '[Obs.]' in definition or 'Shak.' in definition or ('(' in definition and '.)' in definition):
            #     break
            # if '[Obs.]' in definition or 'Shak.' in definition:
            #     continue
            # print(definition, unigram)
            # print('\n[S]', sequence)
            # unigram is built for this single definition
            # in the iteration below, sequence is assumed to be more important than unigram frequency, explanation is provided below
            # example: The fleshy pome or fruit of a rosaceous tree (Pyrus malus) cultivated in numberless varieties in the temperate zones.
            # although there are many nouns in this sentence, but obviously 'fruit' is more important than 'zones', so sequence is assumed to be important
            candidates      = {}    # map word to weights
            for idx, w in enumerate(sequence):
                # `w` is a word in the definition sequence (definition-word)
                # lookup this word and find variation (pos) match
                w_vs = self.dictionary.getWord(w)
                if not w_vs:
                    # unseen words or too frequent words
                    continue
                # initialize 'word weight' to zero
                # 'word weight' is how many unigram (words) in the definition-word definition matched the current definition
                if not w in candidates:
                    candidates[w] = 0
                (def_idx, weights) = self._getDefinitionWordWeights(w, pos, w_vs, unigram)
                candidates[w] += len(weights)
            # Collect all candidates where weight >= 1 (i.e. at least two match from original definition to predicate definition.)
            # *WARNING* The choice of 'weight >= 1' is arbitrary with no scientific evidence.
            for w in sorted(candidates, key=candidates.get, reverse=True):
                if candidates[w] >= system.MINIMUM_DEFINITION_PREDICT_WEIGHT:
                    if w in master_candidates:
                        master_candidates[w] += candidates[w]
                    else:
                        master_candidates[w] = candidates[w]
                if not w in retval and candidates[w] >= system.MINIMUM_DEFINITION_PREDICT_WEIGHT:
                    retval.append(w)
        # In the final master unigram, look for clues of the words shared among all definitions, if they are in candidate list, add weights
        # *WARNING* This is arbitrary with no support of scientific evidence.
        final_gathered = {}
        for u in unigram:
            if unigram[u] >= system.MINIMUM_UNIGRAM_WORD_SHARES and u in master_candidates:
                master_candidates[u] += unigram[u]
                final_gathered[u] = unigram[u]
        # Threshold: remove any candidates with weight < MINIMUM_OUTPUT_PREDICATE_WEIGHT.
        # *WARNING* This is arbitrary with no support of scientific evidence.
        new_retval = []
        for w in retval:
            if master_candidates[w] >= system.MINIMUM_OUTPUT_PREDICATE_WEIGHT:
                new_retval.append(w)
        retval = new_retval
        if debug_print:
            for w in retval:
                print(' ·', w, master_candidates[w], ('(' + str(final_gathered[w]) + ')') if w in final_gathered else '')
        return retval

    @staticmethod
    def cleanup_definition(entry):
        # post-processing to make definition look nicer
        first_char = entry[0]
        if first_char.isdigit():
            entry = entry[entry.find(' ') + 1:]
        return entry

    def find(self, word, debug_print=True, def_mode=0):
        # def_mode: -1 = print definitions, 0 = do nothing, 1+ = select definition
        bare_word   = self.dictionary.undecorateWord(word)
        variations  = self.dictionary.getWord(bare_word)
        retval      = {}
        def_count   = 0
        if not variations:
            return None
        for variation in sorted(variations.keys()):
            if debug_print and def_mode == -1:
                print(variation)
            # for each variation, in terms of part of speech, look for similar words
            pos = Dictionary.getVariationPOS(variation)
            m_pos = [x for x in pos if not x in retval]
            if len(m_pos) == 0:
                continue
            if debug_print and def_mode == 0:
                print('[', bare_word, ','.join(pos).lower() + '.', ']')
            if def_mode == -1:
                for entry in variations[variation]:
                    print('  ' + util.BOLDWHITE + str(def_count + 1) + util.RESET + '.', self.cleanup_definition(entry))
                    def_count += 1
            elif def_mode == 0:
                retval[','.join(pos)] = self._findCandidatesFromDefinitions(bare_word, pos, variations[variation], debug_print)
            else:
                for entry in variations[variation]:
                    def_count += 1
                    if def_count == def_mode:
                        entry = self.cleanup_definition(entry)
                        print('<Selected definition ' + util.BOLDWHITE + str(def_mode) + util.RESET + '. ' + entry + '>')
                        if debug_print:
                            print('[', bare_word, ','.join(pos).lower() + '.', ']')
                        retval[','.join(pos)] = self._findCandidatesFromDefinitions(bare_word, pos, [entry], debug_print)
                        break
        if def_count > 0 and def_mode == -1:
            print('<Enter ' + util.BOLDWHITE + '1-' + str(def_count) + util.RESET + ' to select definition>')
        return retval
