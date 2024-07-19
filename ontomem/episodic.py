from ontomem.memory import Memory
from ontomem.ontology import Concept
from ontomem.properties import Property
from typing import Dict, Iterable, List, Union

import time


class EpisodicMemory(object):

    def __init__(self, memory: Memory):
        self.memory = memory
        self._instances: Dict[str, Frame] = {}
        self._spaces: Dict[str, Space] = {}
        self._xmrs: Dict[str, XMR] = {}

        # Bookkeeping
        self._index_nums_by_concept: Dict[str, int] = {}

    def restart(self):
        self._instances = {}
        self._spaces = {}
        self._xmrs = {}

        self._index_nums_by_concept = {}

    def instance(self, id: str) -> Union['Frame', None]:
        if id in self._instances:
            return self._instances[id]
        return None

    def instances_of(self, concept: Concept, include_descendants: bool=False) -> Iterable['Frame']:
        raise NotImplementedError

    def new_instance(self, concept: Concept) -> 'Frame':
        index = self._next_index_for(concept)
        instance = Frame(self.memory, concept, index)
        self._instances[instance.id()] = instance
        return instance

    def _next_index_for(self, concept: Concept) -> int:
        if concept.name not in self._index_nums_by_concept:
            self._index_nums_by_concept[concept.name] = 0

        self._index_nums_by_concept[concept.name] += 1
        return self._index_nums_by_concept[concept.name]

    def space(self, name: str) -> 'Space':
        if name not in self._spaces:
            self._spaces[name] = Space(self.memory, name)
        return self._spaces[name]


class Space(object):        # Examples: WM, LTE, ???, etc.

    def __init__(self, memory: Memory, name: str):
        self.memory = memory
        self.name = name
        self.instances: Dict[str, Frame] = {}


class XMR(Space):           # Additional fields on top of space, such as raw input, timestamp, etc.

    pass


class Frame(object):        # TODO: RENAME TO Instance

    def __init__(self, memory: Memory, concept: Concept, index: int):
        self.memory = memory
        self.concept = concept
        self.index = index
        self.properties: Dict[str, List[Filler]] = {}

    def id(self) -> str:
        return "%s.%d" % (self.concept.name, self.index)

    def add_filler(self, slot: str, filler: 'Filler.VALUE', timestamp: float=None) -> 'Frame':
        if slot not in self.properties:
            self.properties[slot] = []

        self.properties[slot].append(Filler(filler, timestamp=timestamp))
        return self

    def fillers(self, slot: str) -> List['Filler']:
        if slot not in self.properties:
            self.properties[slot] = []

        return list(self.properties[slot])

    def values(self, slot: str) -> List['Filler.VALUE']:
        raise NotImplementedError

    def is_a(self, parent: Concept) -> bool:
        raise NotImplementedError

    def spaces(self) -> List[Space]:
        raise NotImplementedError   # TODO: Lookup in memory; don't maintain the list locally

    def __repr__(self):
        return "#%s.%d" % (self.concept.name, self.index)


class Filler(object):

    VALUE = Union['Frame', Concept, Property, str, float, int, bool]

    def __init__(self, value: VALUE, timestamp: float=None):
        self.value = value
        self.timestamp = timestamp if timestamp is not None else time.time()

    def __eq__(self, other):
        if isinstance(other, Filler):
            return self.value == other.value and self.timestamp == other.timestamp
        return self.value == other