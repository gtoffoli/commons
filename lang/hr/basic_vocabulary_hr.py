import os

CEFR_LEVELS = { # level codes are case-insensitive
    0: 'a',
    1: 'b',
    2: 'c',
}

"""
A = 'a'
B = 'b'
C = 'c'

NOUN = 'NOUN'
VERB = 'VERB'
ADJ = 'ADJ'
ADV = 'ADV'
"""

FREQUENCY_INTERVALS = { # level codes are case-insensitive
    'NOUN': [1200, 1200, 1200,],
    'VERB': [500, 500, 500],
    'ADJ': [500, 500, 500],
    'ADV': [120, 120, 120],
}

def frequency_to_level(index, intervals):
    level = 0
    max_index = 0
    for interval in intervals:
        max_index += interval
        if index > max_index:
            level += 1
            if level == len(CEFR_LEVELS):
                return None
    return CEFR_LEVELS[level]  

token_level_dict = {}

def get_vocabulary():
    return token_level_dict

def load_vocabulary(file_name='hrLex_v1.3.txt'):
    """ builds in memory
    """
    global token_level_dict
    lexicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    prev_pos = ''
    with open(lexicon_path, encoding='utf8') as infile:
        line = infile.readline()
        while line:
            lemma, upos, frequency = line.split('\t')
            if not upos in ['NOUN', 'VERB', 'ADJ', 'ADV',]:
                line = infile.readline()
                continue
            if upos != prev_pos:
                index = 0
                prev_pos = upos
                levels = FREQUENCY_INTERVALS[upos]
            index += 1
            level = frequency_to_level(index, levels)
            if not level:
                line = infile.readline()
                continue
            token_level_dict[lemma.lower()+'_'+upos.lower()] = level
            line = infile.readline()

load_vocabulary(file_name='hrLex_v1.3.txt')
