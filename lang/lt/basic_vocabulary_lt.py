import os

CEFR_LEVELS = { # level codes are case-insensitive
    0: 'a1',
    1: 'a2',
    2: 'b1',
    3: 'b2',
    4: 'c1',
    5: 'c2',
}

POS_MAP = {
'A': 'ADJECTIVE',
'M': 'ADJECTIVE', # numeral
'N': 'NOUN',
'Nf': 'NOUN', # first name
'Ng': 'NOUN', # geographic name
'Np': 'NOUN', # proper noun
'Ns':'NOUN', # surname
'R': 'ADVERB',
'V': 'VERB',

}

FREQUENCY_INTERVALS = { # level codes are case-insensitive
    'NOUN': [400, 500, 600, 800, 700, 600,], # 3600
    'VERB': [200, 250, 300, 300, 250, 200,], # 1500
    'ADJECTIVE': [200, 250, 300, 300, 250, 200], # 1500
    'ADVERB': [50, 60, 70, 80, 70, 50], # 380
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

def load_vocabulary(file_name='JCL_lemmas.txt'):
    """ builds a "basic vocabulary" indexed by lemma and upos, enriched with CEFR-style levels,
        starting from a word list already annotated with upos and sorted by frequency
    """
    global token_level_dict
    FREQUENCY_COUNTS = {
        'NOUN': {'size': 0, 'count': 0},
        'VERB':  {'size': 0, 'count': 0},
        'ADJECTIVE': {'size': 0, 'count': 0},
        'ADVERB':  {'size': 0, 'count': 0},
    }
    # compute sizes of vocabulary sublists
    for upos, intervals in FREQUENCY_INTERVALS.items():
        for interval in intervals:
            FREQUENCY_COUNTS[upos]['size'] += interval
    lexicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    with open(lexicon_path, encoding='utf8') as infile:
        line = infile.readline()
        while line:
            lemma, upos, frequency = line.split('\t')
            upos = POS_MAP.get(upos, None)
            if not upos or FREQUENCY_COUNTS[upos]['count'] >= FREQUENCY_COUNTS[upos]['size']:
                line = infile.readline()
                continue
            index = FREQUENCY_COUNTS[upos]['count']
            if index >= FREQUENCY_COUNTS[upos]['size']:
                for upos, value in FREQUENCY_COUNTS:
                    if value['count'] < value['size']:
                        line = infile.readline()
                        continue
                break
            levels = FREQUENCY_INTERVALS[upos]
            level = frequency_to_level(index, levels)
            token_level_dict[lemma.lower()+'_'+upos.lower()] = level
            FREQUENCY_COUNTS[upos]['count'] +=1
            line = infile.readline()

load_vocabulary(file_name='JCL_lemmas.txt')
