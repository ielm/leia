from enum import Enum
from pyparsing import OneOrMore, nestedExpr
from typing import Dict, List, Union


# We put the following in TYPE_CHECKING as they are only required for signatures,
# and importing anything from spacy causes a notable lag as data is loaded.  For
# unit tests, this delay serves no purpose, so we can skip it by not actually
# loading the modules at all.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from coreferee.data_model import Chain
    from spacy.tokens import Span, Token


class Syntax(object):

    @classmethod
    def from_spacy(cls, sentence: "Span") -> "Syntax":

        # Finds the NER type (as a Span) for the token, if any.  Expected 0 or 1, so the first result is returned.
        def _ner_span(token: "Token") -> Union["Span", None]:
            for entity in sentence.doc.ents:
                if token in entity:
                    return entity
            return None

        # Finds the coreference chain for the token, if any.  Expected 0 or 1, so the first results is returned.
        def _coref_chain(token: "Token") -> Union["Chain", None]:
            for chain in sentence.doc._.coref_chains:
                for mention in chain.mentions:
                    if mention.root_index == token.i:
                        return chain
            return None

        # Parses the constituency string as lisp, and then processes a top level ConstituencyNode.
        def _parse_constituencies(tree: str, words: List[Word]) -> ConstituencyNode:

            data = OneOrMore(nestedExpr()).parseString(tree)
            data = data.asList()[0]

            return ConstituencyNode.parse_lisp_results(data, words)

        words = list(
            map(
                lambda token: Word.from_spacy(
                    token, _ner_span(token), _coref_chain(token)
                ),
                sentence.subtree,
            )
        )
        constituencies = _parse_constituencies(sentence._.parse_string, words)
        dependencies = list(
            map(
                lambda token: Dependency(
                    words[token.head.i], words[token.i], token.dep_
                ),
                sentence.subtree,
            )
        )

        return Syntax(
            words, sentence.lemma_, sentence.text, constituencies, dependencies
        )

    @classmethod
    def from_dict(cls, input: dict) -> "Syntax":
        words = list(map(lambda w: Word.from_dict(w), input["words"]))

        syntax = Syntax(
            words,
            input["sentence"],
            input["original-sentence"],
            ConstituencyNode.from_dict(input["parse"], words),
            list(map(lambda d: Dependency.from_dict(d, words), input["dependencies"])),
        )

        return syntax

    def __init__(
        self,
        words: List["Word"],
        sentence: str,
        original_sentence: str,
        parse: "ConstituencyNode",
        dependencies: List["Dependency"],
    ):
        self.words = words
        self.sentence = sentence
        self.original_sentence = original_sentence
        self.parse = parse
        self.dependencies = dependencies

        self.synmap: SynMap = None

    def to_dict(self) -> dict:
        return {
            "words": list(map(lambda w: w.to_dict(), self.words)),
            "synmap": self.synmap.to_dict() if self.synmap is not None else {},
            "sentence": self.sentence,
            "original-sentence": self.original_sentence,
            "parse": self.parse.to_dict(),
            "dependencies": list(map(lambda d: d.to_dict(), self.dependencies)),
        }


class SynMap(object):

    def __init__(self, words: List[List["SenseMap"]]):
        self.words = words

    def to_dict(self) -> dict:
        return {
            "sense-maps": list(
                map(lambda l: list(map(lambda sm: sm.to_dict(), l)), self.words)
            )
        }

    def __eq__(self, other):
        if isinstance(other, SynMap):
            return self.words == other.words
        return super().__eq__(other)

    def __repr__(self):
        return "SynMap %s" % repr(self.words)


class SenseMap(object):

    def __init__(self, word: "Word", sense: str, bindings: Dict[str, Union[int, None]]):
        self.word = word
        self.sense = sense
        self.bindings = bindings

    def to_dict(self) -> dict:
        return {
            "word": self.word.index,
            "sense": self.sense,
            "bindings": self.bindings,
        }

    def __eq__(self, other):
        if isinstance(other, SenseMap):
            return self.sense == other.sense and self.bindings == other.bindings
        return super().__eq__(other)

    def __repr__(self):
        return "SenseMap %s: %s" % (self.sense, self.bindings)


class Word(object):

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
    def basic(
        cls,
        index: int,
        lemma: str = "",
        pos: List[str] = None,
        token: str = "",
        char_start: int = -1,
        char_end: int = -1,
        ner: "Word.Ner" = None,
        coref: List["WordCoreference"] = None,
        morphology: Dict[str, str] = None,
    ) -> "Word":
        if pos is None:
            pos = list()
        if ner is None:
            ner = Word.Ner.NONE
        if coref is None:
            coref = list()
        if morphology is None:
            morphology = dict()

        return Word(
            index, lemma, pos, token, char_start, char_end, ner, coref, morphology
        )

    @classmethod
    def from_spacy(
        cls, token: "Token", ner: Union["Span", None], coref: Union["Chain", None]
    ) -> "Word":

        ner = Word.Ner.NONE if ner is None else Word.Ner(ner.label_)

        coref = (
            []
            if coref is None
            else list(
                map(
                    lambda index: WordCoreference(0, index, 0.9),
                    filter(
                        lambda index: index != token.i,
                        map(lambda mention: mention.root_index, coref.mentions),
                    ),
                )
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
            token.morph.to_dict(),
        )

    @classmethod
    def from_dict(cls, input: dict) -> "Word":
        return Word(
            input["index"],
            input["lemma"],
            input["pos"],
            input["token"],
            input["char-start"],
            input["char-end"],
            Word.Ner(input["ner"]),
            list(map(lambda cr: WordCoreference.from_dict(cr), input["coref"])),
            input["morphology"],
        )

    def __init__(
        self,
        index: int,
        lemma: str,
        pos: List[str],
        token: str,
        char_start: int,
        char_end: int,
        ner: "Word.Ner",
        coref: List["WordCoreference"],
        morphology: Dict[str, str],
    ):
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
            "morphology": self.morphology,
        }

    def __repr__(self):
        return "Word [%d] %s %s" % (self.index, self.lemma, self.pos)


class WordCoreference(object):

    @classmethod
    def from_dict(cls, input: dict) -> "WordCoreference":
        return WordCoreference(
            input["sentence"],
            input["word"],
            input["confidence"],
        )

    def __init__(self, sentence: int, word: int, confidence: float):
        self.sentence = sentence
        self.word = word
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "sentence": self.sentence,
            "word": self.word,
            "confidence": self.confidence,
        }

    def __eq__(self, other):
        if isinstance(other, WordCoreference):
            return (
                self.sentence == other.sentence
                and self.word == other.word
                and self.confidence == other.confidence
            )
        return super().__eq__(other)


class ConstituencyNode(object):

    @classmethod
    def parse_lisp_results(cls, lisp: list, words: List[Word]) -> "ConstituencyNode":

        token_index = 0

        def _to_nodes(parsed, parent):
            nonlocal token_index

            if len(parsed) > 1 or not isinstance(parsed[0], str):
                for p in parsed:
                    node = ConstituencyNode(p[0])
                    _to_nodes(p[1:], node)
                    parent.children.append(node)
            else:
                parent.children.append(words[token_index])
                token_index += 1

        node = ConstituencyNode(lisp[0])
        _to_nodes(lisp[1:], node)

        return node

    @classmethod
    def from_dict(cls, input: dict, words: List[Word]) -> "ConstituencyNode":
        node = ConstituencyNode(input["label"])
        for child in input["children"]:
            if "label" in child:
                node.children.append(ConstituencyNode.from_dict(child, words))
            if "word" in child:
                node.children.append(words[child["word"]])

        return node

    def __init__(self, label: str):
        self.label = label
        self.children: List[Union[ConstituencyNode, Word]] = []

    def node_children(self) -> List["ConstituencyNode"]:
        return list(filter(lambda c: isinstance(c, ConstituencyNode), self.children))

    def leftmost_word(self) -> Union[Word, None]:
        if len(self.children) == 0:
            return None

        if isinstance(self.children[0], Word):
            return self.children[0]
        return self.children[0].leftmost_word()

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "children": list(
                map(
                    lambda child: (
                        child.to_dict()
                        if isinstance(child, ConstituencyNode)
                        else {"word": child.index}
                    ),
                    self.children,
                )
            ),
        }


class Dependency(object):

    @classmethod
    def from_dict(cls, input: dict, words: List[Word]) -> "Dependency":
        return Dependency(words[input["gov"]], words[input["dep"]], input["type"])

    def __init__(self, governor: Word, dependent: Word, type: str):
        self.governor = governor
        self.dependent = dependent
        self.type = type

    def __eq__(self, other):
        if isinstance(other, Dependency):
            return (
                self.governor == other.governor
                and self.dependent == other.dependent
                and self.type == other.type
            )
        return super().__eq__(other)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "gov": self.governor.index,
            "dep": self.dependent.index,
        }


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
