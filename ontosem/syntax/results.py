from enum import Enum
from ontomem.lexicon import Sense
from pyparsing import OneOrMore, nestedExpr
from typing import Dict, List, Union


class Syntax(object):

    @classmethod
    def from_lisp_string(cls, lisp: str) -> List['Syntax']:
        data = OneOrMore(nestedExpr()).parseString(lisp)
        data = data.asList()
        data = data[0]  # Unwrap the first level; it isn't needed.

        return list(map(lambda s: Syntax.parse_lisp_results(s), data))

    @classmethod
    def parse_lisp_results(cls, lisp: list) -> 'Syntax':
        stanford = LispParser.list_key_to_value(lisp, "STANFORD")[1]
        words = LispParser.list_key_to_value(stanford, "WORDS")
        words = list(map(lambda w: Word.parse_lisp_results(w), words[1:]))
        basic_deps = LispParser.list_key_to_value(stanford, "BASICDEPS")[1]
        enhanced_deps = LispParser.list_key_to_value(stanford, "ENHANCEDDEPS")[1]
        original_sentence = LispParser.list_key_to_value(stanford, "ORIGINALSENTENCE")[1]
        sentence = LispParser.list_key_to_value(stanford, "SENTENCE")[1]
        parse = LispParser.list_key_to_value(stanford, "PARSE")[1]

        synmap = LispParser.list_key_to_value(lisp, "SYNMAP")
        synmap = SynMap.parse_lisp_results(synmap[1], words)

        lex_senses = LispParser.list_key_to_value(lisp, "LEX-SENSES")
        if lex_senses[1] == "NIL":
            lex_senses = []
        else:
            lex_senses = list(map(lambda s: Sense.parse_lisp(s), lex_senses[1]))

        if sentence.startswith("\"") and sentence.endswith("\""):
            sentence = sentence[1:-1]
        if original_sentence.startswith("\"") and original_sentence.endswith("\""):
            original_sentence = original_sentence[1:-1]

        return Syntax(words, synmap, lex_senses, sentence, original_sentence, parse, basic_deps, enhanced_deps)

    def __init__(self, words: List['Word'], synmap: 'SynMap', lex_senses: List['Sense'], sentence: str, original_sentence: str, parse: list, basic_deps: list, enhanced_deps: list):
        self.words = words
        self.synmap = synmap
        self.lex_senses = lex_senses
        self.sentence = sentence
        self.original_sentence = original_sentence
        self.parse = parse
        self.basic_deps = basic_deps
        self.enhanced_deps = enhanced_deps

    def to_dict(self) -> dict:
        return {
            "words": list(map(lambda w: w.to_dict(), self.words)),
            "synmap": self.synmap.to_dict(),
            "lex-senses": list(map(lambda s: s.to_dict(), self.lex_senses)),
            "sentence": self.sentence,
            "original-sentence": self.original_sentence,
            "parse": self.parse,
            "basic-deps": self.basic_deps,
            "enhanced-deps": self.enhanced_deps
        }


class SynMap(object):

    @classmethod
    def parse_lisp_results(cls, lisp: list, words: List['Word']) -> 'SynMap':
        sensemaps = []
        for i, word in enumerate(lisp):
            sensemap = list(map(lambda s: SenseMap.parse_lisp_results(s, words[i]), word))
            sensemaps.append(sensemap)

        return SynMap(sensemaps)

    def __init__(self, words: List[List['SenseMap']]):
        self.words = words

    def to_dict(self) -> dict:
        return {
            "sense-maps": list(map(lambda l: list(map(lambda sm: sm.to_dict(), l)), self.words))
        }

    def __repr__(self):
        return "SynMap %s" % repr(self.words)


class SenseMap(object):

    @classmethod
    def parse_lisp_results(cls, lisp: list, word: 'Word') -> 'SenseMap':
        sense = lisp[0]
        if sense.startswith("\"") and sense.endswith("\""):
            sense = sense[1:-1]

        bindings = {}
        for variable in lisp[1]:
            bindings[variable[0]] = int(variable[1]) if variable[1] != "NIL" else None
        preference = float(lisp[2][1])

        return SenseMap(word, sense, bindings, preference)

    def __init__(self, word: 'Word', sense: str, bindings: Dict[str, Union[int, None]], preference: float):
        self.word = word
        self.sense = sense
        self.bindings = bindings
        self.preference = preference

    def to_dict(self) -> dict:
        return {
            "word": self.word.index,
            "sense": self.sense,
            "bindings": self.bindings,
            "preference": self.preference
        }

    def __eq__(self, other):
        if isinstance(other, SenseMap):
            return self.sense == other.sense and self.bindings == other.bindings and self.preference == other.preference
        return super().__eq__(other)

    def __repr__(self):
        return "SenseMap %s: %s" % (self.sense, self.bindings)


class Word(object):

    class Ner(Enum):
        CAUSE_OF_DEATH = "CAUSE_OF_DEATH"
        CITY = "CITY"
        COUNTRY = "COUNTRY"
        CRIMINAL_CHARGE = "CRIMINAL_CHARGE"
        DATE = "DATE"
        DURATION = "DURATION"
        EMAIL = "EMAIL"
        HANDLE = "HANDLE"
        IDEOLOGY = "IDEOLOGY"
        LOCATION = "LOCATION"
        MISC = "MISC"
        MONEY = "MONEY"
        NONE = "O"
        NATIONALITY = "NATIONALITY"
        NUMBER = "NUMBER"
        ORDINAL = "ORDINAL"
        ORGANIZATION = "ORGANIZATION"
        PERCENT = "PERCENT"
        PERSON = "PERSON"
        RELIGION = "RELIGION"
        SET = "SET"
        STATE_OR_PROVINCE = "STATE_OR_PROVINCE"
        TIME = "TIME"
        TITLE = "TITLE"
        URL = "URL"


    @classmethod
    def basic(cls, index: int, lemma: str="", pos: List[str]=None, token: str="", char_start: int=-1, char_end: int=-1, ner: 'Word.Ner'=None, coref: List['WordCoreference']=None) -> 'Word':
        if pos is None:
            pos = list()
        if ner is None:
            ner = Word.Ner.NONE
        if coref is None:
            coref = list()

        return Word(index, lemma, pos, token, char_start, char_end, ner, coref)

    @classmethod
    def parse_lisp_results(cls, lisp: list) -> 'Word':
        index = int(LispParser.list_key_to_value(lisp, "ID")[1])
        coref = LispParser.list_key_to_value(lisp, "COREF")[1]
        coref = [] if coref == "NIL" else list(map(lambda c: WordCoreference.parse_lisp_results(c), coref))
        lemma = LispParser.list_key_to_value(lisp, "LEMMA")[1]
        ner = Word.Ner(LispParser.list_key_to_value(lisp, "NER")[1].replace("\"", ""))
        char_start = int(LispParser.list_key_to_value(lisp, "OFFSET")[1][0])
        char_end = int(LispParser.list_key_to_value(lisp, "OFFSET")[1][1])
        pos = list(LispParser.list_key_to_value(lisp, "POS")[1])
        token = LispParser.list_key_to_value(lisp, "TOKEN")[1]

        if token.startswith("\"") and token.endswith("\""):
            token = token[1:-1]

        return Word(index, lemma, pos, token, char_start, char_end, ner, coref)

    def __init__(self, index: int, lemma: str, pos: List[str], token: str, char_start: int, char_end: int, ner: 'Word.Ner', coref: List['WordCoreference']):
        self.index = index
        self.lemma = lemma
        self.pos = pos
        self.token = token
        self.char_start = char_start
        self.char_end = char_end
        self.ner = ner
        self.coref = coref

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "lemma": self.lemma,
            "pos": list(self.pos),
            "token": self.token,
            "char-start": self.char_start,
            "char-end": self.char_end,
            "ner": self.ner.name,
            "coref": list(map(lambda cr: cr.to_dict(), self.coref))
        }

    def __repr__(self):
        return "Word [%d] %s %s" % (self.index, self.lemma, self.pos)


class WordCoreference(object):

    @classmethod
    def parse_lisp_results(cls, lisp: list) -> 'WordCoreference':
        return WordCoreference(int(lisp[5][0]), int(lisp[5][1]), float(lisp[3]))

    def __init__(self, sentence: int, word: int, confidence: float):
        self.sentence = sentence
        self.word = word
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "sentence": self.sentence,
            "word": self.word,
            "confidence": self.confidence
        }

    def __eq__(self, other):
        if isinstance(other, WordCoreference):
            return self.sentence == other.sentence and self.word == other.word and self.confidence == other.confidence
        return super().__eq__(other)


class LispParser(object):

    @classmethod
    def lisp_to_list(cls, lisp: str) -> list:
        return OneOrMore(nestedExpr()).parseString(lisp).asList()

    @classmethod
    def list_key_to_value(cls, lisp: list, key: str) -> Union[List, None]:
        for element in lisp:
            if isinstance(element, list) and len(element) > 0 and element[0] == key:
                return element

        return None