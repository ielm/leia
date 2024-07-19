from enum import Enum
from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Concept
from leia.utils.threads import multiprocess_read_directory
from typing import Dict, List, Set, Tuple, Union

import json
import os


RANGE = Union[
    List[Concept],
    List[str],
    Tuple['COMPARATOR', Union[int, float]],
    Tuple['COMPARATOR', Union[int, float], Union[int, float]],
    'WILDCARD'
]


class COMPARATOR(Enum):
    BETWEEN = "><"
    GT = ">"
    GTE = ">="
    GTELT = ">=<"
    GTLTE = "><="
    INCLUDE = "=>=<"
    LT = "<"
    LTE = "<="


class WILDCARD(Enum):
    ANYBOOL = "!AnyBool"
    ANYLIT = "!AnyLit"
    ANYNUM = "!AnyNum"
    ANYTYPE = "!AnyType"


# This is needed as Pool.starmap cannot access self functions, so we make a public function as a wrapper.
def _read_property(contents_dir: str, file_name: str) -> Tuple[str, dict]:
    name = file_name[0:-5]
    file_name = "%s/%s" % (contents_dir, file_name)

    with open(file_name, "r") as file:
        contents = json.load(file)
        return name, contents


class Property(object):

    class TYPE(Enum):
        BOOLEAN = "BOOLEAN"
        CASE_ROLE = "CASE_ROLE"
        LITERAL = "LITERAL"
        SCALAR = "SCALAR"
        RELATION = "RELATION"
        UNKNOWN = "UNKNOWN"

    def __init__(self, memory: Memory, name: str, contents: dict=None):
        self.memory = memory
        self.name = name
        self.contents = contents

    def set_contents(self, contents: dict):
        self.contents = contents

    def type(self) -> TYPE:
        if self.contents is None:
            return Property.TYPE.UNKNOWN
        return Property.TYPE[self.contents["type"].upper()]

    def range(self) -> RANGE:
        r = self.contents["range"]

        if isinstance(r, str) and r[0] == "!":
            r = WILDCARD(r)
        elif isinstance(r, list) and isinstance(r[0], str) and r[0][0] == "@":
            return list(map(lambda c: self.memory.ontology.concept(c[1:]), r))
        elif isinstance(r, list):
            r = set(r)

        return r

    def definition(self) -> str:
        return self.contents["def"]

    def container(self) -> Union['Property', None]:
        if self.contents is None or self.contents["container"] is None:
            return None

        c = self.contents["container"][1:]

        return self.memory.properties.get_property(c)

    def contains(self) -> List['Property']:
        return list(filter(lambda p: self == p.container(), self.memory.properties.all()))

    def inverse(self) -> Union[str, None]:
        if "inverse" not in self.contents:
            return "%s-INVERSE" % self.name

        i = self.contents["inverse"]
        if isinstance(i, str):
            i = i[1:]

        return i

    def measured_in(self) -> Union[Set['Concept'], None]:
        mi = self.contents["measured-in"]

        return set(map(lambda m: self.memory.ontology.concept(m[1:]), mi))

    def is_attribute(self) -> bool:
        return not self.is_relation()

    def is_relation(self) -> bool:
        return self.type() in {Property.TYPE.RELATION, Property.TYPE.CASE_ROLE}

    def save(self, output_dir: str):

        # TODO: Currently, this is just reading from the stored dict, and writing it back out
        # In the future, the stored dict will likely be indexed into fields (and not needed)
        # This function should continue to work, but will be reading from fields that may change during
        # execution of the agent (from learning or acquisition).

        range = self.range()
        # Default assumes the range is a WILDCARD
        if isinstance(range, WILDCARD):
            range = range.value

        # Handle literal sets
        if isinstance(range, set):
            range = list(range)
        # Handle concepts
        if isinstance(range, Concept):
            range = str(range)

        # TODO: Possibly handle more types

        out = {
            "name": "$%s" % self.name,
            "def": self.definition(),
            "type": self.type().value.lower(),
            "range": range,
            "inverse": "$%s" % self.inverse() if self.inverse() != "" else "",
            "measured-in": list(map(lambda c: str(c), self.measured_in())),
            "container": str(self.container())
        }

        file = "%s/%s.prop" % (output_dir, self.name)
        with open(file, "w") as f:
            json.dump(out, f, indent=2)

    def __repr__(self):
        return "$%s" % self.name


class PropertyInventory(object):

    def __init__(self, memory: Memory, contents_dir: str, load_now: bool=True):
        self.memory = memory
        self.contents_dir = contents_dir
        self.cache = {}
        self._loaded = False

        if load_now:
            self.load()

    def load(self):
        contents = multiprocess_read_directory(self.contents_dir, "prop")
        for c in contents:
            self.cache[c[0]] = Property(self.memory, c[0], contents=None)
        for c in contents:
            self.cache[c[0]].set_contents(c[1])
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def all(self) -> List[Property]:
        return list(self.cache.values())

    def is_property(self, name: str) -> bool:
        return name in self.cache

    def add_property(self, property: Property):
        self.cache[property.name] = property

    def get_property(self, name: str) -> Union[Property, None]:
        if name not in self.cache:
            self.cache[name] = Property(self.memory, name)
        return self.cache[name]

    def relations(self) -> List[Property]:
        return self.properties_with_type(Property.TYPE.RELATION)

    def properties_with_type(self, type: Property.TYPE) -> List[Property]:
        return list(filter(lambda p: p.type() == type, self.cache.values()))

    def inverses(self) -> Dict[str, str]:
        return dict(
            map(lambda p: (p.inverse(), p.name), filter(lambda p: p.is_relation(), self.cache.values()))
        )


if __name__ == "__main__":

    knowledge_dir = "%s/knowledge/properties" % os.getcwd()

    memory = Memory(knowledge_dir, "")
    inventory = memory.properties
    inventory.load()

    print(inventory.get_property("agent").contents)
    print(inventory.get_property("agent").name)
    print(inventory.get_property("agent").type())
    print(inventory.get_property("agent").range())
    print(inventory.get_property("agent").inverse())
    print(inventory.get_property("agent").definition())
    print(inventory.get_property("agent").container())
    print(inventory.get_property("spatial-distance").measured_in())
    print(inventory.get_property("agent").is_relation())
    print(inventory.get_property("agent").is_attribute())