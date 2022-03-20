import os
import pyexcel
file_name = 'KELLY_EL.xlsx'
source = 'https://inventory.clarin.gr/lcr/741'
attribution = """KELLY word-list Greek by Institute for Language and Speech Processing - Athena Research Center used under Creative Commons Attribution Non Commercial 4.0 International (https://creativecommons.org/licenses/by-nc/4.0/legalcode, https://creativecommons.org/licenses/by-nc/4.0/). Source: http://hdl.handle.net/11500/ATHENA-0000-0000-25C1-C (CLARIN:EL)"""

# Μέρος του Λόγου (Part of speech)
pos_map = {
   'ουσιαστικό': 'noun',
   'αντωνυμία': 'pronoun',
   'επίθετο': 'adjective',
   'επίθετο (κλιτή μορφή)': 'adjective',
   'επίθετο (συγκριτικός βαθμός)': 'adjective', # adjective (comparative degree)
   'επίθετο (συγκρ. βαθμός)': 'adjective', # adjective (comparative degree)
   'άρθρο': 'determiner',
   'ρήμα': 'verb',
   'ρήμα (έκφραση)': 'verb', # verbal expression ?
   'ρήμα (απρ. έκφρ.)': 'verb',
   'επίρρημα': 'adverb',
   'επιρρηματική έκφραση': 'adverb', # adverbial expression
   'πρόθεση': 'preposition',
   'σύνδεσμος': 'conjunction',
   'επιφώνημα': 'exclamation',
   'επιφώνημα (μόριο)': 'exclamation',
   'αριθμητικό': 'number', # => adjective, noun (see code)
   'μετοχή': 'adjective', # past participle ?
   'μόριο': '?', # 'particle: prefix or suffix ?
   'έκφραση': '?', # expression, present participle ?
   'έκρφαση': '?', # spelling error!
   'συντομογραφία': '?', # 'abbreviation',
   'συντομογραφία/σύντμηση': '?', #'abbreviation/syntax',
   '': '?',
}

# ending of some base forms of adjectives (?) for which other endings are listed
base_ends = ['ος', 'ός', 'ής', 'ών',]

# the vocabulary annotated with CEFR level to be created by interpreting the KELLY_EL file
voc_el = [
]

def list_to_dict(lst):
    return {k: v for v, k in enumerate(lst)}

def split_lemma(lemma):
    els = [x.strip() for x in lemma.split(',')]
    if len(els) == 1:
        lemmas = [lemma]
    else:
        if lemma.count('-'):
            base = els[0]
            lemmas = [base]
            for end in base_ends:
                if base.endswith(end):
                    root = base[:-len(end)]
                    for el in els[1:]:
                        lemmas.append(root+el[1:])
        else:
            lemmas = els
    return lemmas           

def split_postag(postag):
    els = [x.strip() for x in postag.split(',')]
    postags = [pos_map[postag.lower()] for postag in els]
    if 'number' in postags:
        postags = ['adjective', 'noun',]
    return postags

def make_entries(voc_cols_dict, row):
    entries = []
    level = row[voc_cols_dict['CEF level']]
    lemma = row[voc_cols_dict['Λήμμα (Lemma)']]
    lemmas = split_lemma(lemma)
    postag = row[voc_cols_dict['Μέρος του Λόγου (Part of speech)']]
    postags = split_postag(postag)
    for lemma in lemmas:
        for postag in postags:
            entries.append([lemma, postag, level.lower()])
    return entries

def load_vocabulary (file_name=''):
    global voc_el
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    f = open(file_path, "br")
    extension = file_name.split(".")[-1]
    content = f.read()
    f.close()
    book = pyexcel.get_book(file_type=extension, file_content=content)
    book_dict = book.to_dict()
    voc_table = book_dict["Sheet1"]
    voc_cols = voc_table[0]
    voc_rows = voc_table[1:]
    voc_cols_dict = list_to_dict(voc_cols)
    # print(voc_cols_dict)
    for row in voc_rows:
        voc_el.extend(make_entries(voc_cols_dict, row))

load_vocabulary(file_name)
"""
for entry in voc_el:
    print(entry)
"""
