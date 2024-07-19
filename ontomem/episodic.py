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

    def remove_instance(self, instance: 'Frame'):
        if instance.id() in self._instances:
            del self._instances[instance.id()]

        for space in self._spaces.values():
            space.remove_instance(instance)

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

    def new_instance(self, concept: Concept) -> 'Frame':
        # Calls memory's new_instance method, and then adds the instance to this space
        instance = self.memory.episodic.new_instance(concept)
        self.instances[instance.id()] = instance
        return instance

    def remove_instance(self, instance: 'Frame'):
        # Removes the instance from this space (but does not remove it from memory)
        if instance.id() in self.instances:
            del self.instances[instance.id()]


class XMR(Space):

    def __init__(self, memory: Memory, name: str=None, raw: Any=None, timestamp: float=None):
        super().__init__(memory, name if name is not None else memory.episodic._next_id_for_xmr(self))

        self.raw = raw
        self.timestmap = timestamp if timestamp is not None else time.time()

    def root(self) -> Union['Frame', None]:
        # Finds the current root of the XMR.
        # The root is the frame that has the least incoming and most outgoing relations.
        # EVENTs take priority over OBJECTs, who take priority over PROPERTYs (that is, a less good matching EVENT
        # is still better than any OBJECT).
        # In the case of a tie, the lower instance number wins.  Further ties = select "the first one".

        if len(self.instances) == 0:
            return None

        # Setup the scoring index
        root_scoring = {}
        for frame in self.instances.values():
            subtree = None
            ancestors = frame.concept.ancestors()
            ancestors.add(frame.concept)
            if self.memory.ontology.concept("EVENT") in ancestors:
                subtree = "EVENT"
            elif self.memory.ontology.concept("OBJECT") in ancestors:
                subtree = "OBJECT"
            elif self.memory.ontology.concept("PROPERTY") in ancestors:
                subtree = "PROPERTY"

            root_scoring[frame.id()] = {
                "frame_id": frame.id(),
                "subtree": subtree,
                "incoming": 0,
                "outgoing": 0,
                "instance": frame.index
            }

        # Now modify each score
        for frame in self.instances.values():
            for property in frame.properties.keys():
                for filler in frame.values(property):
                    if isinstance(filler, Frame):
                        root_scoring[frame.id()]["outgoing"] += 1
                        root_scoring[filler.id()]["incoming"] += 1

        # Now find the best root
        candidates = []
        subtrees_present = list(map(lambda s: s["subtree"], root_scoring.values()))
        if "EVENT" in subtrees_present:
            candidates = list(filter(lambda s: s["subtree"] == "EVENT", root_scoring.values()))
        elif "OBJECT" in subtrees_present:
            candidates = list(filter(lambda s: s["subtree"] == "OBJECT", root_scoring.values()))
        elif "PROPERTY" in subtrees_present:
            candidates = list(filter(lambda s: s["subtree"] == "PROPERTY", root_scoring.values()))

        # Calculate the final score for each candidate
        for candidate in candidates:
            candidate["score"] = candidate["outgoing"] - candidate["incoming"]

        # Find the best score, then filter to candidates with that score
        best_score = max(candidates, key=lambda x: x["score"])["score"]
        candidates = list(filter(lambda c: c["score"] == best_score, candidates))

        # Find the lowest instance number, then filter to candidates with that instance
        lowest_instance = min(candidates, key=lambda x: x["instance"])["instance"]
        candidates = list(filter(lambda c: c["instance"] == lowest_instance, candidates))

        # Return the first (ideally only) candidate
        return self.instances[candidates[0]["frame_id"]]


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