import os

CEFR_LEVELS = { # level codes are case-insensitive
    0: 'a1',
    1: 'a2',
    2: 'b1',
    3: 'b2',
    4: 'c1',
    5: 'c2',
}

"""
FREQUENCY_INTERVALS = { # level codes are case-insensitive
    'NOUN': [1200, 1200, 1200,],
    'VERB': [500, 500, 500],
    'ADJECTIVE': [500, 500, 500],
    'ADVERB': [120, 120, 120],
}
"""
FREQUENCY_INTERVALS = { # level codes are case-insensitive
    'NOUN': [400, 500, 600, 800, 700, 600,],
    'VERB': [200, 250, 300, 300, 250, 200,],
    'ADJECTIVE': [200, 250, 300, 300, 250, 200],
    'ADVERB': [50, 60, 70, 80, 70, 50],
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
            if upos == 'ADJ':
                upos = 'ADJECTIVE'
            elif upos == 'ADV':
                upos = 'ADVERB'
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
