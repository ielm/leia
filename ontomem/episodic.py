from ontomem.memory import Memory
from ontomem.ontology import Concept
from ontomem.properties import Property
from typing import Any, Dict, Iterable, List, Union

import time


class EpisodicMemory(object):

    def __init__(self, memory: Memory):
        self.memory = memory
        self._instances: Dict[str, Frame] = {}
        self._spaces: Dict[str, Space] = {}
        self._xmrs: Dict[str, XMR] = {}

        # Bookkeeping
        self._instance_nums_by_concept: Dict[str, int] = {}
        self._instance_nums_by_xmr: Dict[str, int] = {}

    def reset(self):
        self._instances = {}
        self._spaces = {}
        self._xmrs = {}

        self._instance_nums_by_concept = {}

    def instance(self, id: str) -> Union['Frame', None]:
        if id in self._instances:
            return self._instances[id]
        return None

    def instances_of(self, concept: Concept, include_descendants: bool=False) -> Iterable['Frame']:
        raise NotImplementedError

    def new_instance(self, concept: Concept) -> 'Frame':
        index = self._next_instance_for_concept(concept)
        instance = Frame(self.memory, concept, index)
        self._instances[instance.id()] = instance
        return instance

    def _next_instance_for_concept(self, concept: Concept) -> int:
        if concept.name not in self._instance_nums_by_concept:
            self._instance_nums_by_concept[concept.name] = 0

        self._instance_nums_by_concept[concept.name] += 1
        return self._instance_nums_by_concept[concept.name]

    def _next_id_for_xmr(self, xmr: 'XMR') -> str:
        xmr_type = xmr.__class__.__name__
        if xmr_type not in self._instance_nums_by_xmr:
            self._instance_nums_by_xmr[xmr_type] = 0

        self._instance_nums_by_xmr[xmr_type] += 1
        return "%s.%d" % (xmr_type, self._instance_nums_by_xmr[xmr_type])

    def space(self, name: str) -> 'Space':
        if name not in self._spaces:
            self._spaces[name] = Space(self.memory, name)
        return self._spaces[name]


class Space(object):        # Examples: WM, LTE, ???, etc.

    def __init__(self, memory: Memory, name: str):
        self.memory = memory
        self.name = name
        self.instances: Dict[str, Frame] = {}


class XMR(Space):

    def __init__(self, memory: Memory, name: str=None, raw: Any=None, timestamp: float=None):
        super().__init__(memory, name if name is not None else memory.episodic._next_id_for_xmr(self))

        self.raw = raw
        self.timestmap = timestamp if timestamp is not None else time.time()

    def root(self) -> 'Frame':
        raise NotImplementedError


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

    def remove_filler(self, slot: str, filler: 'Filler.VALUE') -> 'Frame':
        if slot not in self.properties:
            return self

        to_remove = list(filter(lambda f: f.value == filler, self.fillers(slot)))
        for x in to_remove:
            self.properties[slot].remove(x)

        if len(self.properties[slot]) == 0:
            del self.properties[slot]

        return self

    def fillers(self, slot: str) -> List['Filler']:
        if slot not in self.properties:
            return []

        return list(self.properties[slot])

    def values(self, slot: str) -> List['Filler.VALUE']:
        return list(map(lambda f: f.value, self.fillers(slot)))

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