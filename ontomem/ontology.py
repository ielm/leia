from dataclasses import dataclass
from multiprocessing import Pool
from ontomem.memory import Memory
from typing import List, Iterable, Set, Tuple, Union

import json
import os

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ontomem.properties import Property, WILDCARD


# TODO: Following functionalities are needed at a minimum
#  - handling not
#  - value facet overrides all other facets (and can't be overridden)


# This is needed as Pool.starmap cannot access self functions, so we make a public function as a wrapper.
def _read_concept(contents_dir: str, file_name: str) -> Tuple[str, dict]:
    name = file_name[0:-4]
    file_name = "%s/%s" % (contents_dir, file_name)

    with open(file_name, "r") as file:
        contents = json.load(file)
        return name, contents


class Ontology(object):

    def __init__(self, memory: Memory, contents_dir: str, load_now: bool=True):
        self.memory = memory
        self.contents_dir = contents_dir
        self.cache = {}

        if load_now:
            self.load()

    def load(self):
        pool = Pool(4)
        files = os.listdir(self.contents_dir)

        names = map(lambda f: f[0:-4], files)
        types = map(lambda n: (n, Concept(self.memory, n, contents=None)), names)
        self.cache = dict(types)

        contents = pool.starmap(_read_concept, map(lambda file: (self.contents_dir, file), files))
        for c in contents:
            self.cache[c[0]].set_contents(c[1])

    def concept(self, name: str) -> Union['Concept', None]:
        if name not in self.cache:
            self.cache[name] = Concept(self.memory, name)
        return self.cache[name]

    def usages(self, concept: 'Concept') -> Iterable[Tuple['Concept', str, str]]:
        for c in self.cache.values():
            for sk, sv in c.slots.items():
                for fk, fv in sv.items():
                    if concept in fv:
                        yield c, sk, fk

    def common_ancestors(self, a: str, b: str) -> Set[str]:
        a_ancestors = set(map(lambda f: f.name, self.concept(a).ancestors()))
        b_ancestors = set(map(lambda f: f.name, self.concept(b).ancestors()))

        ancestors = a_ancestors.intersection(b_ancestors)
        return ancestors

    def distance_to_ancestor(self, descendant: str, ancestor: str) -> Union[int, None]:
        if descendant == ancestor:
            return 0

        ancestor = self.concept(ancestor)

        def _find_ancestor(start: Concept, distance: int) -> Union[int, None]:
            distances = []
            for parent in start.parents():
                if parent == ancestor:
                    return distance + 1
                d = _find_ancestor(parent, distance + 1)
                if d is None:
                    continue
                distances.append(d)

            if len(distances) == 0:
                return None

            return min(distances)

        result = _find_ancestor(self.concept(descendant), 0)
        return result


class Concept(object):

    FILLER = Union[
        'Concept',
        'Property',
        List[str],
        Tuple['COMPARATOR', Union[int, float]],
        Tuple['COMPARATOR', Union[int, float], Union[int, float]],
        'WILDCARD'
    ]

    @dataclass
    class LocalRow:
        concept: 'Concept'
        property: str
        facet: str
        filler: 'Concept.FILLER'
        meta: dict

    @dataclass
    class BlockedRow:
        concept: 'Concept'
        property: str
        facet: str
        filler: 'Concept.FILLER'


    def __init__(self, memory: Memory, name: str, contents: dict=None, root: 'Concept'=None):
        self.memory = memory
        self.name = name
        self.contents = contents
        self.local = dict()
        self.block = dict()
        self.private = dict()
        self._root = root if root is not None else self
        self._parents: Set['Concept'] = set()

        if contents is not None:
            self._index()

    def set_contents(self, contents: dict):
        self.contents = contents
        self._index()

    def _index(self):

        self._parents = set()
        self.local = dict()
        self.block = dict()
        self.private = dict()

        if self._root == self:
            # Generate the private concepts, but don't parse them yet
            for concept in self.contents["private"].keys():
                self.private[concept[1:]] = Concept(self.memory, concept[1:], root=self)

            # Now that the private concepts all exist, each can be parsed
            for concept, contents in self.contents["private"].items():
                self.private[concept[1:]].set_contents(contents)

        for parent in self.contents["isa"]:
            self._parents.add(self.memory.ontology.concept(parent[1:]))

        for row in self.contents["local"]:
            self._parse_row(row, self.local)

        for row in self.contents["block"]:
            self._parse_row(row, self.block)

    def _parse_row(self, row: dict, into: dict):
        slot = row["slot"]
        facet = row["facet"]
        filler = row["filler"]

        # Parse various filler types
        if isinstance(filler, str):
            if filler[0] == "@":
                if filler[1:] in self._root.private:
                    filler = self._root.private[filler[1:]]
                else:
                    filler = self.memory.ontology.concept(filler[1:])
            elif filler[0] == "$":
                filler = self.memory.properties.get_property(filler[1:])
            elif filler[0] == "&":
                # TODO: get the set
                raise NotImplementedError

        if slot not in into:
            into[slot] = dict()
        if facet not in into[slot]:
            into[slot][facet] = list()

        filler = {
            "value": filler
        }

        if "meta" in row:
            filler.update(row["meta"])

        into[slot][facet].append(filler)

    def add_parent(self, parent: 'Concept') -> 'Concept':
        self._parents.add(parent)
        return self

    def remove_parent(self, parent: 'Concept') -> 'Concept':
        if parent in self._parents:
            self._parents.remove(parent)
        return self

    def parents(self) -> Set['Concept']:
        return set(self._parents)

    def ancestors(self) -> Set['Concept']:
        a = set(self._parents)
        for p in self._parents:
            a.update(p.ancestors())

        return a

    def isa(self, concept: 'Concept') -> bool:
        return concept == self or concept in self.ancestors()

    def children(self) -> Set['Concept']:
        out = set()

        for concept in self.memory.ontology.cache.values():
            if self in concept.parents():
                out.add(concept)

        return out

    def descendants(self) -> Set['Concept']:
        d = set(self.children())
        for c in set(d):
            d.update(c.descendants())

        return d

    def siblings(self) -> Set['Concept']:
        c = set()
        for p in self.parents():
            c.update(p.children())

        if self in c:
            c.remove(self)

        return c

    def add_local(self, property: str, facet: str, filler: FILLER, measured_in: str=None):
        if property not in self.local:
            self.local[property] = dict()
        if facet not in self.local[property]:
            self.local[property][facet] = list()

        filler = {
            "value": filler,
        }

        if measured_in is not None:
            filler["measured-in"] = measured_in

        self.local[property][facet].append(filler)

    def remove_local(self, property: str, facet: str, filler: FILLER):
        if property not in self.local:
            return
        if facet not in self.local[property]:
            return

        self.local[property][facet] = list(filter(lambda f: f["value"] != filler, self.local[property][facet]))

    def add_block(self, property: str, facet: str, filler: FILLER):
        if property not in self.block:
            self.block[property] = dict()
        if facet not in self.block[property]:
            self.block[property][facet] = list()

        self.block[property][facet].append(filler)

    def remove_block(self, property: str, facet: str, filler: FILLER):
        if property not in self.block:
            return
        if facet not in self.block[property]:
            return

        self.block[property][facet] = list(filter(lambda f: f != filler, self.block[property][facet]))

    def is_blocking(self, property: str, facet: str, filler: FILLER) -> bool:
        if property not in self.block:
            return False
        if facet not in self.block[property]:
            return False

        return filler in self.block[property][facet] or "*" in self.block[property][facet]

    def rows(self) -> List[FILLER]:
        out = []

        for slot, facets in self.local.items():
            for facet, fillers in facets.items():
                for filler in fillers:
                    meta = dict(filler)
                    del meta["value"]
                    out.append(Concept.LocalRow(self, slot, facet, filler["value"], meta))

        for slot, facets in self.block.items():
            for facet, fillers in facets.items():
                for filler in fillers:
                    out.append(Concept.BlockedRow(self, slot, facet, filler))

        for parent in self.parents():
            parent_rows = parent.rows()
            parent_rows = filter(lambda r: not isinstance(r, Concept.BlockedRow), parent_rows)
            parent_rows = filter(lambda r: not self.is_blocking(r.property, r.facet, r.filler), parent_rows)

            out.extend(parent_rows)

        return out

    def fillers(self, slot: str, facet: str) -> List:
        out = self.rows()
        out = filter(lambda r: not isinstance(r, Concept.BlockedRow), out)
        out = filter(lambda r: r.property == slot and r.facet == facet, out)
        out = map(lambda r: r.filler, out)

        return list(out)

    def allowed(self, slot: str, facet: str, filler) -> bool:
        raise NotImplementedError

    def evaluate(self, slot: str, facet: str, filler) -> float:
        raise NotImplementedError

    def __repr__(self):
        return "@%s" % self.name


if __name__ == "__main__":

    knowledge_dir = "%s/knowledge/concepts" % os.getcwd()

    memory = Memory("", knowledge_dir, "")
    ontology = memory.ontology

    import time
    start = time.time()
    ontology.load()
    print("Time to load: %s" % str(time.time() - start))

    print(ontology.concept("human").contents)
    print(ontology.concept("human").parents())
    print(ontology.concept("human").fillers("has-object-as-part", "sem"))
    print(ontology.concept("human").fillers("has-object-as-part", "sem")[0])

    start = time.time()
    print(ontology.concept("human").rows())
    print("Time to check rows: %s" % str(time.time() - start))

