import pyphen

# currently use hyphenation as a proxy of syllabification
class GenericSyllabizer():

    def __init__(self, language_code):
        if language_code in pyphen.LANGUAGES:
            self.dic = pyphen.Pyphen(lang=language_code)
        else:
            self.dic = None

    def syllabize(self, word):
        if self.dic:
            hyphenated = self.dic.inserted(word)
            return hyphenated.split('-')
        else:
            return []
