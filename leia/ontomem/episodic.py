from enum import Enum
from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Concept
from leia.ontomem.properties import Property
from typing import Any, Dict, List, Type, Union

import time



class Space(object):

    def __init__(self, memory: Memory, name: str, private: bool=False):
        self.memory = memory
        self._name = name
        self._private = private

        # Contents
        self._instances: Dict[str, Instance] = {}
        self._spaces: Dict[str, Space] = {}

        # Bookkeeping
        self._instance_nums_by_concept: Dict[str, int] = {}
        self._instance_nums_by_space: Dict[str, int] = {}

    def reset(self):
        self._instances = {}
        self._spaces = {}

        self._instance_nums_by_concept = {}
        self._instance_nums_by_space = {}

    def instance(self, id: str) -> Union['Instance', None]:
        if id in self._instances:
            return self._instances[id]
        return None

    def has_instance(self, id: str) -> bool:
        return id in self._instances

    def instances(self) -> List['Instance']:
        return list(self._instances.values())

    def instances_of(self, concept: Concept, include_descendants: bool=False) -> List['Instance']:
        matches = {concept.name}
        if include_descendants:
            matches.update(set(map(lambda d: d.name, concept.descendants())))

        return list(filter(lambda i: i.concept.name in matches, self._instances.values()))

    def new_instance(self, concept: Union[str, Concept], instance_type: Type['Instance']=None) -> 'Instance':
        if instance_type is None:
            instance_type = Instance

        index = self._next_instance_for_concept(concept)
        instance = instance_type(self.memory, concept, index)
        self.register_instance(instance)
        return instance

    def register_instance(self, instance: 'Instance'):
        self._instances[instance.id()] = instance

    def remove_instance(self, instance: 'Instance'):
        if instance.id() in self._instances:
            del self._instances[instance.id()]

        for space in self._spaces.values():
            space.remove_instance(instance)

    def _next_instance_for_concept(self, concept: Union[str, Concept]) -> int:
        if isinstance(concept, Concept):
            concept = concept.name

        if concept not in self._instance_nums_by_concept:
            self._instance_nums_by_concept[concept] = 0

        self._instance_nums_by_concept[concept] += 1
        return self._instance_nums_by_concept[concept]

    def _next_id_for_space(self, space: Type['Space']) -> str:
        space_type = space.__name__
        if space_type not in self._instance_nums_by_space:
            self._instance_nums_by_space[space_type] = 0

        self._instance_nums_by_space[space_type] += 1
        return "%s.%d" % (space_type, self._instance_nums_by_space[space_type])

    def space(self, name: str) -> Union['Space', None]:
        if name in self._spaces:
            return self._spaces[name]
        return None

    def spaces(self, include_private: bool=False) -> List['Space']:
        if include_private:
            return list(self._spaces.values())
        return list(filter(lambda s: not s.is_private(), self._spaces.values()))

    def new_space(self, name: str=None, space_type: Type['Space']=None, private: bool=False) -> 'Space':
        if space_type is None:
            space_type = Space

        if name is None:
            name = self._next_id_for_space(space_type)

        space = space_type(self.memory, name, private=private)
        self._spaces[name] = space
        return space

    def name(self) -> str:
        return self._name

    def is_private(self) -> bool:
        return self._private

    def __eq__(self, other):
        if isinstance(other, Space):
            return self._instances == other._instances
        return super().__eq__(other)


class XMR(Space):

    class Status(Enum):
        RAW = "RAW"                     # The XMR represents input that is not yet interpreted
        INTERPRETED = "INTERPRETED"     # The XMR represents input that has been interpreted
        ISSUED = "ISSUED"               # The XMR represents output that has not yet been rendered
        RENDERED = "RENDERED"           # The XMR represents output that has been rendered

    class Priority(Enum):
        LOW = "LOW"
        ASAP = "ASAP"
        INTERRUPT = "INTERRUPT"

    def __init__(self, memory: Memory, name: str=None, private: bool=False, raw: Any=None, timestamp: float=None, status: Status=None, priority: Priority=None):
        super().__init__(memory, name if name is not None else memory.episodic._next_id_for_space(self.__class__), private=private)

        self._raw = raw
        self.timestmap = timestamp if timestamp is not None else time.time()
        self._status = status if status is not None else XMR.Status.RAW
        self._priority = priority if priority is not None else XMR.Priority.LOW

    def set_raw(self, raw: Any):
        self._raw = raw

    def raw(self) -> Any:
        return self._raw

    def set_status(self, status: Status):
        self._status = status

    def status(self) -> Status:
        return self._status

    def set_priority(self, priority: Priority):
        self._priority = priority

    def priority(self) -> Priority:
        return self._priority

    def root(self) -> Union['Instance', None]:
        # Finds the current root of the XMR.
        # The root is the frame that has the least incoming and most outgoing relations.
        # EVENTs take priority over OBJECTs, who take priority over PROPERTYs (that is, a less good matching EVENT
        # is still better than any OBJECT).
        # In the case of a tie, the lower instance number wins.  Further ties = select "the first one".

        if len(self.instances()) == 0:
            return None

        # Setup the scoring index
        root_scoring = {}
        for frame in self.instances():
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
        for frame in self.instances():
            for property in frame.properties.keys():
                for filler in frame.values(property):
                    if isinstance(filler, Instance):
                        root_scoring[frame.id()]["outgoing"] += 1

                        # Update incoming only if the instance is part of the XMR's space.
                        if filler in self.instances():
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
        return self.instance(candidates[0]["frame_id"])

    def to_dict(self) -> dict:
        return {
            "instances": list(map(lambda f: f.to_dict(), self.instances()))
        }


class Instance(object):

    class TooManyFillersError(Exception): pass

    def __init__(self, memory: Memory, concept: Union[str, Concept], index: int, private_to: Space=None):
        self.memory = memory
        self.concept = concept if isinstance(concept, Concept) else memory.ontology.concept(concept)
        self.index = index
        self._private_to = private_to
        self.properties: Dict[str, List[Filler]] = {}

    def id(self) -> str:
        if self._private_to is not None:
            return "%s:%s.%d" % (self._private_to.name, self.concept.name, self.index)

        return "%s.%d" % (self.concept.name, self.index)

    def add_filler(self, slot: str, filler: 'Filler.VALUE', timestamp: float=None) -> 'Instance':
        if slot not in self.properties:
            self.properties[slot] = []

        self.properties[slot].append(Filler(filler, timestamp=timestamp))
        return self

    def remove_filler(self, slot: str, filler: 'Filler.VALUE') -> 'Instance':
        if slot not in self.properties:
            return self

        to_remove = list(filter(lambda f: f.value == filler, self.fillers(slot)))
        for x in to_remove:
            self.properties[slot].remove(x)

        if len(self.properties[slot]) == 0:
            del self.properties[slot]

        return self

    def set_filler(self, slot: str, filler: Union['Filler.VALUE', List['Filler.VALUE']], timestamp: float=None) -> 'Instance':
        if not isinstance(filler, list):
            filler = [filler]

        filler = list(map(lambda f: Filler(f, timestamp=timestamp), filler))

        self.properties[slot] = filler

        return self

    def fillers(self, slot: str) -> List['Filler']:
        if slot not in self.properties:
            return []

        return list(self.properties[slot])

    def values(self, slot: str) -> List['Filler.VALUE']:
        return list(map(lambda f: f.value, self.fillers(slot)))

    def value(self, slot: str) -> Union['Filler.VALUE', None]:
        fillers = self.fillers(slot)
        if len(fillers) == 0:
            return None
        if len(fillers) == 1:
            return fillers[0].value
        raise Instance.TooManyFillersError

    def isa(self, parent: Concept) -> bool:
        return self.concept.isa(parent)

    def private_to(self) -> Union[Space, None]:
        return self._private_to

    def spaces(self) -> List[Space]:
        raise NotImplementedError   # TODO: Lookup in memory; don't maintain the list locally

    def to_dict(self) -> dict:
        return {
            "id": self.id(),
            "concept": str(self.concept),
            "index": self.index,
            "properties": dict(map(lambda i: (i[0], list(map(lambda f: str(f.value), i[1]))), self.properties.items())),
        }

    def __repr__(self):
        return "#%s.%d" % (self.concept.name, self.index)


class Filler(object):

    VALUE = Union['Instance', Concept, Property, str, float, int, bool]

    def __init__(self, value: VALUE, timestamp: float=None):
        self.value = value
        self.timestamp = timestamp if timestamp is not None else time.time()

    def __eq__(self, other):
        if isinstance(other, Filler):
            return self.value == other.value and self.timestamp == other.timestamp
        return self.value == other