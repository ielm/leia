from enum import Enum
from multiprocessing import Pool
from ontomem.memory import Memory
from ontomem.ontology import Concept
from typing import List, Set, Tuple, Union

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
    INCLUDE = ">=<"
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

    def __init__(self, memory: Memory, name: str, contents: dict=None):
        self.memory = memory
        self.name = name
        self.contents = contents

    def set_contents(self, contents: dict):
        self.contents = contents

    def type(self) -> TYPE:
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

    def container(self) -> 'Property':
        c = self.contents["container"][1:]

        return self.memory.properties.get_property(c)

    def inverse(self) -> Union[str, None]:
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

        if load_now:
            self.load()

    def load(self):
        pool = Pool(4)
        files = os.listdir(self.contents_dir)

        names = map(lambda f: f[0:-5], files)
        props = map(lambda n: (n, Property(self.memory, n, contents=None)), names)
        self.cache = dict(props)

        contents = pool.starmap(_read_property, map(lambda file: (self.contents_dir, file), files))
        for c in contents:
            self.cache[c[0]].set_contents(c[1])

    def add_property(self, property: Property):
        self.cache[property.name] = property

    def get_property(self, name: str) -> Union[Property, None]:
        if name in self.cache:
            return self.cache[name]
        return None


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