from coreferee.data_model import Chain
from enum import Enum
from leia.ontomem.lexicon import Sense
from pyparsing import OneOrMore, nestedExpr
from spacy.tokens import Span, Token
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

    @classmethod
    def from_spacy(cls, sentence: Span) -> 'Syntax':

        def _ner_span(token: Token) -> Union[Span, None]:
            for entity in sentence.doc.ents:
                if token in entity:
                    return entity
            return None

        def _coref_chain(token: Token) -> Union[Chain, None]:
            for chain in sentence.doc._.coref_chains:
                for mention in chain.mentions:
                    if mention.root_index == token.i:
                        return chain
            return None

        words = list(map(lambda token: Word.from_spacy(token, _ner_span(token), _coref_chain(token)), sentence.subtree))


        # print("\nDEPENDENCIES:")
        # for sent in doc.sents:
        #     for token in sent.subtree:
        #         print("GOV(%s-%d)  -[%s]->  DEP(%s-%d)" % (
        #         token.head.text, token.head.i, token.dep_, token.text, token.i))
        #
        # print("\nNOUN PHRASES:")
        # for chunk in doc.noun_chunks:
        #     print(list(map(lambda token: "%s-%d" % (token.text, token.i), chunk)))
        #
        # def _format_constituency_parse(node, depth):
        #     indent = "  ".join(map(lambda i: "", range(depth + 1)))
        #
        #     if len(node._.labels) > 0:
        #         print("%s%s" % (indent, node._.labels[0]))
        #     else:
        #         print("%s%s %s-%d" % (indent, node.root.tag_, node.root.text, node.root.i))
        #     for child in node._.children:
        #         _format_constituency_parse(child, depth + 1)
        #
        # class TreeNode(object):
        #
        #     def __init__(self, label: str):
        #         self.label = label
        #         self.children = []
        #
        #     def pretty_print(self, depth: int = 0):
        #         indent = "  ".join(map(lambda i: "", range(depth + 1)))
        #         print("%s%s" % (indent, self.label))
        #         for child in self.children:
        #             if isinstance(child, TreeNode):
        #                 child.pretty_print(depth=depth + 1)
        #             else:
        #                 indent = "  ".join(map(lambda i: "", range(depth + 2)))
        #                 print("%s%s-%d" % (indent, child.text, child.i))
        #
        # from pyparsing import OneOrMore, nestedExpr
        #
        # def _parse_constituencies(sentence, tree: str):
        #
        #     data = OneOrMore(nestedExpr()).parseString(tree)
        #     data = data.asList()[0]
        #
        #     token_index = 0
        #
        #     def _to_nodes(parsed, parent):
        #         nonlocal token_index
        #
        #         if len(parsed) > 1 or not isinstance(parsed[0], str):
        #             for p in parsed:
        #                 node = TreeNode(p[0])
        #                 _to_nodes(p[1:], node)
        #                 parent.children.append(node)
        #         else:
        #             parent.children.append(sentence[token_index])
        #             token_index += 1
        #
        #     node = TreeNode(data[0])
        #     _to_nodes(data[1:], node)
        #
        #     return node
        #
        # print("\nCONSTITUENCY PARSES:")
        # for sent in doc.sents:
        #     print(sent._.parse_string)
        #     # _format_constituency_parse(sent, 0)
        #     _parse_constituencies(sent, sent._.parse_string).pretty_print()

        return Syntax(words, None, None, None, None, None, None, None)


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

    # class Ner(Enum):
    #     CAUSE_OF_DEATH = "CAUSE_OF_DEATH"
    #     CITY = "CITY"
    #     COUNTRY = "COUNTRY"
    #     CRIMINAL_CHARGE = "CRIMINAL_CHARGE"
    #     DATE = "DATE"
    #     DURATION = "DURATION"
    #     EMAIL = "EMAIL"
    #     HANDLE = "HANDLE"
    #     IDEOLOGY = "IDEOLOGY"
    #     LOCATION = "LOCATION"
    #     MISC = "MISC"
    #     MONEY = "MONEY"
    #     NONE = "O"
    #     NATIONALITY = "NATIONALITY"
    #     NUMBER = "NUMBER"
    #     ORDINAL = "ORDINAL"
    #     ORGANIZATION = "ORGANIZATION"
    #     PERCENT = "PERCENT"
    #     PERSON = "PERSON"
    #     RELIGION = "RELIGION"
    #     SET = "SET"
    #     STATE_OR_PROVINCE = "STATE_OR_PROVINCE"
    #     TIME = "TIME"
    #     TITLE = "TITLE"
    #     URL = "URL"

    class Ner(Enum):
        CARDINAL = "CARDINAL"
        DATE = "DATE"
        EVENT = "EVENT"
        FAC = "FAC"
        GPE = "GPE"
        LANGUAGE = "LANGUAGE"
        LAW = "LAW"
        LOC = "LOC"
        MONEY = "MONEY"
        NONE = "NONE"
        NORP = "NORP"
        ORDINAL = "ORDINAL"
        ORG = "ORG"
        PERCENT = "PERCENT"
        PERSON = "PERSON"
        PRODUCT = "PRODUCT"
        QUANTITY = "QUANTITY"
        TIME = "TIME"
        WORK_OF_ART = "WORK_OF_ART"


    @classmethod
    def basic(cls, index: int, lemma: str="", pos: List[str]=None, token: str="", char_start: int=-1, char_end: int=-1, ner: 'Word.Ner'=None, coref: List['WordCoreference']=None, morphology: Dict[str, str]=None) -> 'Word':
        if pos is None:
            pos = list()
        if ner is None:
            ner = Word.Ner.NONE
        if coref is None:
            coref = list()
        if morphology is None:
            morphology = dict()

        return Word(index, lemma, pos, token, char_start, char_end, ner, coref, morphology)

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

        return Word(index, lemma, pos, token, char_start, char_end, ner, coref, {})

    @classmethod
    def from_spacy(cls, token: Token, ner: Union[Span, None], coref: Union[Chain, None]) -> 'Word':

        ner = Word.Ner.NONE if ner is None else Word.Ner(ner.label_)

        coref = [] if coref is None else list(
            map(lambda index: WordCoreference(0, index, 0.9),
                filter(lambda index: index != token.i,
                    map(lambda mention: mention.root_index, coref.mentions))
            )
        )

        # Note: The coreference index is relative to the first sentence (hence sentencenum = 0).
        # Consider recalculating to find the sentence index and the word's index relative to that sentence
        # if needed.

        return Word(
            token.i,
            token.lemma_,
            [token.pos_, token.tag_],
            token.text,
            token.idx,
            token.idx + len(token.text),
            ner,
            coref,
            token.morph.to_dict()
        )

    def __init__(self, index: int, lemma: str, pos: List[str], token: str, char_start: int, char_end: int, ner: 'Word.Ner', coref: List['WordCoreference'], morphology: Dict[str, str]):
        self.index = index
        self.lemma = lemma
        self.pos = pos
        self.token = token
        self.char_start = char_start
        self.char_end = char_end
        self.ner = ner
        self.coref = coref
        self.morphology = morphology

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "lemma": self.lemma,
            "pos": list(self.pos),
            "token": self.token,
            "char-start": self.char_start,
            "char-end": self.char_end,
            "ner": self.ner.name,
            "coref": list(map(lambda cr: cr.to_dict(), self.coref)),
            "morphology": self.morphology
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