from dataclasses import dataclass
from leia.ontomem.memory import Memory
from leia.utils.threads import multiprocess_read_directory
from typing import Any, Dict, List, Set, Tuple, Union

import copy
import itertools
import os


class Lexicon(object):

    def __init__(self, memory: Memory, contents_dir: str, load_now: bool=True):
        self.memory = memory
        self.contents_dir = contents_dir
        self.cache = {}
        self._loaded = False

        if load_now:
            self.load()

    def load(self):
        contents = multiprocess_read_directory(self.contents_dir, "word")
        for c in contents:
            self.cache[c[0]] = Word(self.memory, c[0], contents=c[1])
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def word(self, word: str) -> 'Word':
        # 1) Check the cache
        if word in self.cache:
            return self.cache[word]

        # 2) Create a new (empty) word
        created = self.create_word(word)
        self.cache[word] = created
        return created

    def words(self) -> List['Word']:
        return list(self.cache.values())

    def senses(self) -> List['Sense']:
        return list(itertools.chain.from_iterable(map(lambda w: w.senses(include_synonyms=False), self.words())))

    def create_word(self, word: str) -> 'Word':
        return Word(self.memory, word)

    def sense(self, sense: str) -> 'Sense':
        word = self.word(sense[0:sense.rfind("-")])
        return word.sense(sense)


class Word(object):

    def __init__(self, memory: Memory, name: str, contents: dict=None):
        self.memory = memory
        self.name = name
        self._senses = dict()

        if contents is not None:
            for k, v in contents["senses"].items():
                self._senses[k] = Sense(memory, k, contents=v)

    def add_sense(self, sense: 'Sense'):
        self._senses[sense.id] = sense

    def sense(self, sense: str) -> 'Sense':
        if sense in self._senses:
            return self._senses[sense]

        raise Exception("Unknown sense %s." % sense)

    def senses(self, include_synonyms: bool=True) -> List['Sense']:
        results = list(self._senses.values())

        if include_synonyms:
            for word in self.memory.lexicon.words():
                for sense in word.senses(include_synonyms=False):
                    if self.name in sense.synonyms():
                        results.append(sense)

        return results

    def __eq__(self, other):
        if isinstance(other, Word):
            return self.name == other.name and self._senses == other._senses


class Sense(object):

    def __init__(self, memory: Memory, id: str, contents: dict=None):
        self.memory = memory
        self.id: str = id

        self.word: Word = None
        self.pos: str = None
        self.synstruc: SynStruc = None
        self.semstruc: SemStruc = None
        self.meaning_procedures: List[MeaningProcedure] = []
        self.tmr_head: str = None
        self.output_syntax: List[str] = []

        self.definition: str = None
        self.example: str = None
        self.comments: str = None

        self._synonyms: List[str] = []
        self._hyponyms: List[str] = []

        if contents is not None:
            self._index(contents)

    def _index(self, contents: dict):
        self.word = self.memory.lexicon.word(contents["WORD"])
        self.pos = contents["CAT"]
        self.synstruc = SynStruc(contents=contents["SYN-STRUC"])
        self.semstruc = SemStruc(contents["SEM-STRUC"])
        self.meaning_procedures = list(map(lambda mp: MeaningProcedure(mp), contents["MEANING-PROCEDURES"]))
        self.tmr_head = contents["TMR-HEAD"]
        self.output_syntax = contents["OUTPUT-SYNTAX"]

        self.definition = contents["DEF"]
        self.example = contents["EX"]
        self.comments = contents["COMMENTS"]

        self._synonyms = list(contents["SYNONYMS"]) if "SYNONYMS" in contents else []
        self._hyponyms = list(contents["HYPONYMS"]) if "HYPONYMS" in contents else []

    def synonyms(self) -> List[str]:
        return list(self._synonyms)

    def to_dict(self) -> dict:
        return {
            "SENSE": self.id,
            "WORD": self.word.name,
            "CAT": self.pos,
            "SYNONYMS": list(self._synonyms),
            "HYPONYMS": list(self._hyponyms),
            "SYN-STRUC": self.synstruc.to_dict(),
            "SEM-STRUC": self.semstruc.to_dict(),
            "MEANING-PROCEDURES": list(map(lambda mp: mp.to_dict(), self.meaning_procedures)),
            "TMR-HEAD": self.tmr_head,
            "OUTPUT-SYNTAX": self.output_syntax,

            "COMMENTS": self.comments,
            "DEF": self.definition,
            "EX": self.example,

            "EXAMPLE-BINDINGS": [],
            "EXAMPLE-DEPS": [],
            "TYPES": [],
            "USE-WITH-TYPES": []
        }

    def __eq__(self, other):
        if isinstance(other, Sense):
            return self.id == other.id


class SynStruc(object):

    class Element:

        @classmethod
        def parse(cls, data: dict) -> 'SynStruc.Element':
            raise NotImplementedError

        def to_variable(self) -> Union[int, None]:
            raise NotImplementedError

        def is_optional(self) -> bool:
            raise NotImplementedError

        def to_dict(self) -> dict:
            raise NotImplementedError

    @dataclass
    class RootElement(Element):

        variable: int = 0

        @classmethod
        def parse(cls, data: dict) -> 'SynStruc.RootElement':
            return SynStruc.RootElement()

        def to_variable(self) -> Union[int, None]:
            return self.variable

        def is_optional(self) -> bool:
            return False

        def to_dict(self) -> dict:
            return {"type": "root"}

    @dataclass
    class TokenElement(Element):

        lemmas: Set[str]
        pos: Union[str, None]
        morph: Dict[str, str]
        variable: Union[int, None]
        optional: bool

        @classmethod
        def parse(cls, data: dict) -> 'SynStruc.TokenElement':
            return SynStruc.TokenElement(
                set(data["lemma"]),
                data["pos"],
                data["morph"],
                data["var"] if "var" in data else None,
                data["opt"] if "opt" in data else False
            )

        def to_variable(self) -> Union[int, None]:
            return self.variable

        def is_optional(self) -> bool:
            return self.optional

        def to_dict(self) -> dict:
            return {"type": "token", "lemma": list(self.lemmas), "pos": self.pos, "morph": self.morph, "var": self.variable, "opt": self.optional}

    @dataclass
    class DependencyElement(Element):

        type: str
        governor: Union['SynStruc.TokenElement', None]
        dependent: Union['SynStruc.TokenElement', None]
        variable: Union[int, None]
        optional: bool

        @classmethod
        def parse(cls, data: dict) -> 'SynStruc.DependencyElement':

            gov = data["gov"] if "gov" in data else None
            if isinstance(gov, dict):
                gov = SynStruc.TokenElement.parse(gov)

            dep = data["dep"] if "dep" in data else None
            if isinstance(dep, dict):
                dep = SynStruc.TokenElement.parse(dep)

            return SynStruc.DependencyElement(
                data["deptype"],
                gov,
                dep,
                data["var"] if "var" in data else None,
                data["opt"] if "opt" in data else False
            )

        def to_variable(self) -> Union[int, None]:
            return self.variable

        def is_optional(self) -> bool:
            return self.optional

        def to_dict(self) -> dict:
            return {"type": "dependency", "deptype": self.type, "gov": self.governor if self.governor is None else self.governor.to_dict(), "dep": self.dependent if self.dependent is None else self.dependent.to_dict(), "var": self.variable, "opt": self.optional}

    @dataclass
    class ConstituencyElement(Element):

        type: str
        children: List[Union['SynStruc.ConstituencyElement', 'SynStruc.TokenElement']]
        variable: Union[int, None]
        optional: bool

        @classmethod
        def parse(cls, data: dict) -> 'SynStruc.ConstituencyElement':
            element_map = {
                "token": SynStruc.TokenElement,
                "constituency": SynStruc.ConstituencyElement
            }

            return SynStruc.ConstituencyElement(
                data["contype"],
                list(map(lambda child: element_map[child["type"]].parse(child), data["children"])),
                data["var"] if "var" in data else None,
                data["opt"] if "opt" in data else False
            )

        def to_variable(self) -> Union[int, None]:
            return self.variable

        def is_optional(self) -> bool:
            return self.optional

        def element_for_variable(self, variable: int) -> Union['SynStruc.Element', None]:
            if self.to_variable() == variable:
                return self
            for child in self.children:
                if child.to_variable() == variable:
                    return child
                if isinstance(child, SynStruc.ConstituencyElement):
                    match = child.element_for_variable(variable)
                    if match is not None:
                        return match
            return None

        def to_dict(self) -> dict:
            return {"type": "constituency", "contype": self.type, "children": list(map(lambda child: child.to_dict(), self.children)), "var": self.variable, "opt": self.optional}

    def __init__(self, contents: List[dict]=None):
        self.elements = []

        if contents is not None:
            self._index(contents)

    def _index(self, contents: List[dict]):
        element_map = {
            "root": SynStruc.RootElement,
            "token": SynStruc.TokenElement,
            "dependency": SynStruc.DependencyElement,
            "constituency": SynStruc.ConstituencyElement
        }

        self.elements = list(map(lambda element: element_map[element["type"]].parse(element), contents))

    def element_for_variable(self, variable: int) -> Union['SynStruc.Element', None]:
        for element in self.elements:
            if element.to_variable() == variable:
                return element
            if isinstance(element, SynStruc.ConstituencyElement):
                match = element.element_for_variable(variable)
                if match is not None:
                    return match

        return None

    def to_dict(self) -> list:
        return list(map(lambda e: e.to_dict(), self.elements))

    def __eq__(self, other):
        if isinstance(other, SynStruc):
            return self.elements == other.elements
        return super().__eq__(other)


class SemStruc(object):

    MPS = {
        "FIND-NOUN-ATTRIBUTE", "APPLY-COUNT-NP", "ABSOLUTE-TIME",
        "SEEK-SPONSOR-IN-TEXT", "PASS-THROUGH-MEANING", "INCREASE-IN-VALUE",
        "FIND-ANCHOR-SPEAKER", "APPLY-MEANING", "FIND-ANCHOR-PLACE",
        "SEEK-CONTEXTUAL-SPONSOR", "FIND-ANCHOR-TIME", "REQUEST-INFO-TRACE",
        "EVALUATED-ACCORDINT-TO", "COMBINE-TIME", "CALCULATE-QUOTIENT",
        "COREF", "COMBINE-AMOUNT"
    }

    IEQS = {
        "=", ">", "<", "><", ">=<", ">=", "<=", "OR", "NOT"
    }

    class Element:
        def properties(self) -> List[Tuple[str, Any]]:
            raise NotImplementedError

    @dataclass
    class Head(Element):
        concept: str = "ALL"
        contents: dict = None

        def properties(self) -> List[Tuple[str, Any]]:
            return list(self.contents.items())

    @dataclass
    class Sub:
        index: int
        concept: str = "ALL"
        contents: dict = None

        def properties(self) -> List[Tuple[str, Any]]:
            return list(self.contents.items())

    @dataclass
    class RefSem:
        index: int
        semstruc: 'SemStruc' = None

        def properties(self) -> List[Tuple[str, Any]]:
            return list(self.semstruc.data.items())

    @dataclass
    class Variable:
        index: int
        contents: dict = None

        def properties(self) -> List[Tuple[str, Any]]:
            return list(self.contents.items())

    @dataclass
    class Property:
        variable: int
        property: str
        value: Any = None

        def properties(self) -> List[Tuple[str, Any]]:
            return [("RANGE", self.value)]

    def __init__(self, data: Union[dict, list, str]):
        if data == "":
            data = {}
        if isinstance(data, str):
            data = {data: {}}
        if isinstance(data, list):
            data = {data[0]: {}}

        self.data: dict = data

    def elements(self, bound_variable_filter: Set[str]=None) -> List[Union['SemStruc.Head', 'SemStruc.Sub', 'SemStruc.RefSem', 'SemStruc.Variable', 'SemStruc.Property']]:
        # Returns all of the HEAD, SUB, REFSEM and VARIABLE elements in this semstruc.
        # If the bound_variable_filter is provided (which must be a set of variable names, e.g., ^$VAR1), then all
        # matching VARIABLE elements will be included in the result as-is, but any variables found in the semstruc
        # that are not in the filter will be decomposed into their PROPERTY elements instead.

        # In the event that the semstruc is entirely empty, return a HEAD that is *NOTHING*.  This is used for
        # null senses.  They automatically null-sem themselves, so they will be removed from the TMR, but provide
        # a temporary placeholder for various purposes.
        if len(self.data.items()) == 0:
            return [SemStruc.Head("*NOTHING*", {"NULL-SEM": "+"})]

        results = []

        sub_index = 0
        for k, v in self.data.items():
            if k.startswith("REFSEM"):
                index = int(k.replace("REFSEM", ""))
                results.append(SemStruc.RefSem(index, SemStruc(v)))
                continue
            if k.startswith("^$VAR"):
                index = int(k.replace("^$VAR", ""))
                # Include the VARIABLE if no filter was applied, or if the variable is in the filter
                if bound_variable_filter is None or k[1:] in bound_variable_filter:
                    results.append(SemStruc.Variable(index, v))
                    continue
                # Otherwise, decompose the variable into PROPERTY elements; skip NULL-SEM properties (essentially
                # if the variable is not bound, then we don't need to explicitly declare it NULL-SEM'd anyway)
                else:
                    for property in v.keys():
                        if property == "NULL-SEM" or property == "SEM":
                            continue
                        results.append(SemStruc.Property(index, property, v[property]))
                    continue

            # TODO: Here, if k is not a concept, probably should error, skip, or output some sort of "other"
            if sub_index == 0:
                results.append(SemStruc.Head(k, v))
                sub_index += 1
            else:
                results.append(SemStruc.Sub(sub_index, k, v))
                sub_index += 1

        return results

    def head(self) -> Union['SemStruc.Head', None]:
        for e in self.elements():
            if isinstance(e, SemStruc.Head):
                return e

        return None

    def subs(self) -> List['SemStruc.Sub']:
        return list(filter(lambda e: isinstance(e, SemStruc.Sub), self.elements()))

    def refsems(self) -> List['SemStruc.RefSem']:
        return list(filter(lambda e: isinstance(e, SemStruc.RefSem), self.elements()))

    def variables(self, bound_variable_filter: Set[str]=None) -> List['SemStruc.Variable']:
        return list(filter(lambda e: isinstance(e, SemStruc.Variable), self.elements(bound_variable_filter=bound_variable_filter)))

    def properties(self, bound_variable_filter: Set[str]) -> List['SemStruc.Property']:
        return list(filter(lambda e: isinstance(e, SemStruc.Property), self.elements(bound_variable_filter=bound_variable_filter)))

    def to_dict(self) -> dict:
        return copy.deepcopy(self.data)

    def __repr__(self):
        return repr(self.data)

    def __eq__(self, other):
        if isinstance(other, SemStruc):
            return self.data == other.data
        return super().__eq__(other)


class MeaningProcedure(object):

    def __init__(self, data: List[Union[str, List[str]]]):
        if len(data) == 0:
            data = ["UNKNOWN-MP"]
        self.data = data

    def name(self) -> str:
        return self.data[0]

    def parameters(self) -> List[Union[str, List[str]]]:
        return self.data[1:]

    def to_dict(self) -> list:
        return self.data

    def __eq__(self, other):
        if isinstance(other, MeaningProcedure):
            return self.data == other.data
        return super().__eq__(other)


if __name__ == "__main__":

    knowledge_dir = "%s/leia/knowledge/words" % os.getcwd()

    memory = Memory(lex_path=knowledge_dir)
    lexicon = memory.lexicon

    import time
    start = time.time()
    lexicon.load()
    print("Time to load: %s" % str(time.time() - start))

    start = time.time()
    print(lexicon.word("BE").contents)
    print("Time to load BE: %s" % str(time.time() - start))

    start = time.time()
    print(lexicon.word("BE").contents)
    print("Time to read BE from cache: %s" % str(time.time() - start))

    start = time.time()
    print(lexicon.sense("BE-V1").contents)
    print(lexicon.sense("BE-V2").contents)
    print("Time to read BE-V1 and BE-V2 from cache: %s" % str(time.time() - start))