# see http://graficnotes.blogspot.com/2012/08/6.html
vowels = 'αειηουω'
diphthongs = ['αι', 'αη', 'οι', 'οη',]
abusive = ['ει', 'οι', 'ι', 'υ',]
abusive_diphthongs = [a+d for a in abusive for d in diphthongs]
abusive_diphthongs += [a+v for a in abusive for v in vowels]
vowel_groups = abusive_diphthongs + diphthongs + ['αυ', 'ευ',]

def count_word_syllables(word):
    n_syllables = 0
    for group in vowel_groups:
        if word.count(group):
            n_syllables += 1
            word = word.replace(group, '')
    for c in word:
        if c in vowels:
            n_syllables += 1
    return n_syllables
 