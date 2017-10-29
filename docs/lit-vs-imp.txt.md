# A Comparison Between Patent Literature and Implementation

## 1. Ambiguities in Patent Literature, and Their Computational Solutions

One of the commonly used methods in terms of "predicate selection" is "to select predicates based on context and consistency." Examples of such mentions include (in patent PDF page / line order):

**Page 2, [0017], left column, line 1**: _words is selected based on being **consistent** with the **context** of said first predicate of said first subject word._
**Page 2, [0017], left column, line 7**: _one of the predicates for each of said named third subject words is selected based on being **consistent** with the **context** of ..._
**Page 2, [0017], right column, line 10**: _always selected based on the fact that the predicates are **consistent** with the **context** of said first predicate of said..._

Because it's computationally impractical to determine the context of a word or whether its meaning (or taxonomy) is consistent, a method is used throughout the implementation to approximate contextual consistency for selected words.

Single word occurrence statistics (a.k.a. unigrams) are used to estimate contextual consistency. Every definition (def-A) of a single word (word-A) is split into an array of words (word-def-As). For each word-def-As, another round of definition lookup is performed, resulting in a two-layer series of definitions (def-Bs). Finally, the unigram calculates how many words in 'def-Bs' are present in 'word-def-As'; each match is counted. Higher values are considered higher contextual consistencies.

Note: frequent words are excluded and PoS is taken into account.

## 2. Section [0017] and its implementation

### 2.1 Step 100, getting words and their definitions

Section [0017] first mentions the first procedure of **Step 100**, which picks out a word with definitions from the dictionary.

In the implementation, this is covered by the dictionary parser in conjunction with the Python dictionary object. The relevent source file is `dmtipci/dictionary.py`, which contains a class named `Dictionary`. The function `updateFromGutenbergText` converts a Gutenberg Project Dictionary (MWUD 2000) plain text file into a Python dictionary object.

After this is done, the produced Python dictionary object is queried for a word and is returned its definition(s).

### 2.2 Step 101 - 1, gather predicates

Section [0017] then mentions gathering predicates from the definitions produced by **Step 100**. The section does not describe how the gathering is done. But, drawing from _"DMTIPCI Using Apple for software comparison 4 11 14.pdf"_, the interesting predicates are words of the same part of speech.

In the case of **"APPLE"** being _"1. The fleshy pome or fruit of a rosaceous tree (Pyrus malus) cultivated in numberless varieties in the temperate zones."_ , the interesting words would be **"POME"**, **"FRUIT"** and **"TREE"**, because they share the same part of speech.

In the implementation, this is covered by the first procedure of the `Finder` class in `dmtipci/finder.py`. Its method `find` first identifies the part of speech of the query word: [line 160](https://github.com/kazazes/DMTIPCI/blob/d1adb05d802ddc4653c77819d312617a0c6bc511/dmtipci/find.py#L160), then, at [line 170](https://github.com/kazazes/DMTIPCI/blob/d1adb05d802ddc4653c77819d312617a0c6bc511/dmtipci/find.py#L170), calls `_findCandidatesFromDefinitions` which asks `_getDefinitionUnigramSequence` to produce a unigram sequence of words from the definition.

In the result of this call, a sequence of words from the definition is returned as a list. The order of the words is the exact order of word appearance in the definition sentence. Multiple occurrences are present only once. Such a design follows the original patent literature, where sequence of words appears to be an important factor. Further, the list contains only words that are the same part of speech as the query. Dictionary-wide frequent words are removed from this list. Some of the word forms (plural, etc.) are simplified in this list (see inflection mapping issue #4).

All words in this list are potential predicate and 'primary word' candidates.

### 2.3 Step 101 - 2, fine tuning results

The patent literature and research documentation _"DMTIPCI Using Apple for software comparison 4 11 14.pdf"_ claim that the procedure of selecting predicates is primarily concerned that the:

1. definition (usage) is related to the word itself
2. definition's (usage) context is consistent with the word

As described in Chapter 1, these procedures are computationally impractical. To properly select predicates, the aforementioned unigram weight solution is used. An example is illustrated below, using the query word **"APPLE"** and its first definition _"1. The fleshy pome or fruit of a rosaceous tree (Pyrus malus) cultivated in numberless varieties in the temperate zones."_:

1. As described in 2.2, Step 101 results in the following potential candidates: **"POME"**, **"FRUIT"**, **"TREE"**, **"PYRUS"**, **"VARIETY"**, **"ZONE"**.
2. As described in the patent procedures, for each of the potential candidates, step 100 and 101 are repeated. For instance, **"POME"** has one definition _*"1. (Bot.) A fruit composed of several cartilaginous or bony carpels inclosed in an adherent fleshy mass, which is partly receptacle and partly calyx, as an apple, quince, or pear."*_, which breaks down into the following words in the first step of 101: **"FRUIT"**, **"CARPEL"**, **"MASS"**, **"APPLE"**, **"QUINCE"**, **"PEAR"**.
3. The query word **"APPLE"** itself will be added to the unigram, so the unigram contains all the words in 1. plus **"APPLE"**. In the example of **"POME"**, it is seen that both **"FRUIT"** and **"APPLE"** have unigram matches. The weight is 2 because 2 words are matched.
4. This step is repeated for all candidates. The current system threshold requires a minimum weight of 2, or the definition will be discarded. This threshold is controlled by the `MINIMUM_UNIGRAM_MATCH_PER_DEFINITION` constant in `dmtipci/system.py`. This works on a per-definition basis. If a definition is not able to produce a weight of at least 2, the entire definition is discarded from consideration.
5. The constant `MINIMUM_DEFINITION_PREDICT_WEIGHT` in `dmtipci/system.py` controls the minimum number of definitions required to mark a candidate as valid. Currently it's 1, which means 1 definition match is required. While set to 1, this only discards words that are not present in the dictionary.

This entire procedure is inside the `_getDefinitionWordWeights` function of class `Finder` in `dmtipci/finder.py`. After this procedure, the list of potential candidates is refinied and the original candidates are are evaluated to meet the minimum weight requirement.

### 2.4 Non-patent procedures for result fine tuning

It is also mentioned in #9 that in some of the cases, the best primary word does not necessarily reflect largest unigram coverage. In the case of **"APPLE"**: _"1. The fleshy pome or fruit of a rosaceous tree (Pyrus malus) cultivated in numberless varieties in the temperate zones."_, the best choice of primary word **"FRUIT"** has the somewhat unrelated definition: _"1. Whatever is produced for the nourishment or enjoyment of man or animals by the processes of vegetable growth, as corn, grass, cotton, flax, etc.; -- commonly used in the plural. Six years thou shalt sow thy land, and shalt gather in the fruits thereof. Ex. xxiii. 10."_ .

In this particular case none of the words in the **"FRUIT"** definition match the definition of **"APPLE"**. It is again computationally impractical to establish relations between these two words.

To solve this problem, another mechanism is used to include words like **"FRUIT"** in the results of **"APPLE"**. This mechanism builds another set of word occurrence statistics to discover common words inside the definitions.

In the case of **"APPLE"**, definition look ups of **"POME"**, **"PYRUS"** both shared high occurrences of the word **"FRUIT"**. Because this word is in the potential candidate list, it's added back to the output despite the fact that the definition of **"FRUIT"** has nothing to do with **"APPLE"**. The constant `MINIMUM_UNIGRAM_WORD_SHARES` in `dmtipci/system.py` controls the minimum number of occurrences required. It is currently set to 2.

This final gather mechanism is at [line 123](https://github.com/kazazes/DMTIPCI/blob/d1adb05d802ddc4653c77819d312617a0c6bc511/dmtipci/find.py#L123) of the `_findCandidatesFromDefinitions` function of `dmtipci/find.py`.

## 3. Other Sections in the Patent, and Current Status

### 3.1 The rest of the patent

Multi-level lookups, although described as a different procedure in the patent, are implemented using a nested variation of the same methods described above.

_"DMTIPCI Using Apple for software comparison 4 11 14.pdf"_ does not reference the rest of the patent.

### 3.2 Current status

_"Primary Words 4 11 14.pdf"_ mentions using a rule-based approach; this needs to be explored.

Multi-level lookup can be implemented. However, only one extra level, a total of 2, should be implemented to keep already-noisy results managable.

Inflection mapping can be improved to handle adjectives and verbs better. The mapping covers conversion between alternate word forms. Since WordNet is not going to be a dependency, generating the inflection map itself is a big task.
