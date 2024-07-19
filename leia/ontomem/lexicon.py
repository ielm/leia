from collections import OrderedDict
from dataclasses import dataclass
from leia.ontomem.memory import Memory
from typing import Any, List, Set, Tuple, Union
from leia.utils.formatting import FormatFromLISP

import json
import os


class Lexicon(object):

    def __init__(self, memory: Memory, contents_dir: str, load_now: bool=True):
        self.memory = memory
        self.contents_dir = contents_dir
        self.cache = {}

        if load_now:
            self.load()

    def load(self):
        # This method has been added to mirror the ontology loading pattern; the lexicon is intended to be
        # lazy loaded, so this method does nothing for now.  In the future, should something be needed as
        # part of an initial load, it can be placed here.
        pass

    def word(self, word: str) -> 'Word':
        # 1) Check the cache
        if word in self.cache:
            return self.cache[word]

        # 2) Lazy load from the contents_dir
        loaded = self.load_word(word)
        if loaded is not None:
            self.cache[word] = loaded
            return loaded

        # 3) Create a new (empty) word
        created = self.create_word(word)
        self.cache[word] = created
        return created

    def load_word(self, word: str) -> Union['Word', None]:
        try:
            with open("%s/%s.word" % (self.contents_dir, word), "r") as f:
                return Word(self.memory, word, contents=json.load(f))
        except FileNotFoundError:
            return None

    def create_word(self, word: str) -> 'Word':
        return Word(self.memory, word)

    def sense(self, sense: str) -> 'Sense':
        word = self.word(sense[0:sense.rfind("-")])
        return word.sense(sense)


class Word(object):

    def __init__(self, memory: Memory, name: str, contents: dict=None):
        self.memory = memory
        self.name = name
        self.contents = contents if contents is not None else {
            "name": self.name,
            "senses": {}
        }

    def add_sense(self, sense: dict):
        self.contents["senses"][sense["SENSE"]] = sense

    def sense(self, sense: str) -> 'Sense':
        if sense in self.contents["senses"]:
            return Sense(self.memory, sense, contents=self.contents["senses"][sense])

        raise Exception("Unknown sense %s." % sense)

    def __eq__(self, other):
        if isinstance(other, Word):
            return self.name == other.name and self.contents == other.contents


class Sense(object):

    @classmethod
    def parse_lisp(cls, memory: Memory, lisp: list) -> 'Sense':
        parsed = FormatFromLISP().list_to_sense(lisp)
        return Sense(memory, parsed["SENSE"], {
            "SENSE": parsed["SENSE"],
            "WORD": parsed["WORD"],
            "CAT": parsed["CAT"],
            "SYN-STRUC": parsed["SYN-STRUC"],
            "SEM-STRUC": parsed["SEM-STRUC"],
            "MEANING-PROCEDURES": parsed["MEANING-PROCEDURES"] if parsed["MEANING-PROCEDURES"] != "NIL" else []
        })

    def __init__(self, memory: Memory, id: str, contents: dict=None):
        self.memory = memory
        self.id = id
        self.contents = contents if contents is not None else {}

        self.word = None
        self.pos = None
        self.synstruc = None
        self.semstruc = None
        self.meaning_procedures = []

        if contents is not None:
            self._index()

    def _index(self):
        self.word = self.memory.lexicon.word(self.contents["WORD"])
        self.pos = self.contents["CAT"]
        self.synstruc = SynStruc(self.contents["SYN-STRUC"])
        self.semstruc = SemStruc(self.contents["SEM-STRUC"])
        self.meaning_procedures = list(map(lambda mp: MeaningProcedure(mp), self.contents["MEANING-PROCEDURES"]))

    def __eq__(self, other):
        if isinstance(other, Sense):
            return self.id == other.id and self.contents == other.contents


class SynStruc(object):

    def __init__(self, data: OrderedDict):
        self.data = data

    def to_dict(self) -> dict:
        return self.data

    def __eq__(self, other):
        if isinstance(other, SynStruc):
            return self.data == other.data
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
        return self.data

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

    def __eq__(self, other):
        if isinstance(other, MeaningProcedure):
            return self.data == other.data
        return super().__eq__(other)


if __name__ == "__main__":

    knowledge_dir = "%s/leia/knowledge/words" % os.getcwd()

    memory = Memory("", "", knowledge_dir)
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