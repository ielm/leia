from dataclasses import dataclass
from enum import Enum
from multiprocessing import Pool
from leia.ontomem.memory import Memory
from leia.utils.threads import multiprocess_read_json_file
from typing import List, Iterable, Set, Type, Tuple, Union

import os

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from leia.ontomem.properties import COMPARATOR, Property, WILDCARD


class Ontology(object):

    def __init__(self, memory: Memory, contents_dir: str, load_now: bool=True):
        self.memory = memory
        self.contents_dir = contents_dir
        self._cache = {}

        if load_now:
            self.load()

    def load(self):
        pool = Pool(4)
        files = os.listdir(self.contents_dir)

        names = map(lambda f: f[0:-4], files)
        types = map(lambda n: (n, Concept(self.memory, n, contents=None)), names)
        self._cache = dict(types)

        contents = pool.starmap(multiprocess_read_json_file, map(lambda file: (self.contents_dir, file, "ont"), files))
        for c in contents:
            self._cache[c[0]].set_contents(c[1])

    def concept(self, name: str) -> Union['Concept', None]:
        if name not in self._cache:
            self._cache[name] = Concept(self.memory, name)
        return self._cache[name]

    def concepts(self) -> List['Concept']:
        return list(self._cache.values())

    def names(self) -> Set[str]:
        return set(self._cache.keys())

    def usages(self, concept: 'Concept') -> Iterable[Tuple['Concept', str, str]]:
        for c in self._cache.values():
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

    class INHFLAG: pass

    FILLER = Union[
        'Concept',
        'Property',
        'OSet',
        List[str],
        Tuple['COMPARATOR', Union[int, float]],
        Tuple['COMPARATOR', Union[int, float], Union[int, float]],
        'WILDCARD',
        Type[INHFLAG]
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
                if concept[0] == "@":
                    self.private[concept[1:]] = Concept(self.memory, concept[1:], root=self)
                elif concept[0] == "&":
                    self.private[concept[1:]] = OSet(self.memory, concept[1:], root=self)

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
                filler = self._root.private[filler[1:]]
            elif filler[0] == "!":
                from leia.ontomem.properties import WILDCARD
                filler = WILDCARD[filler[1:].upper()]
            elif filler == "^":
                filler = Concept.INHFLAG

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

        for concept in self.memory.ontology.concepts():
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
                    if filler["value"] == Concept.INHFLAG:
                        range = self.memory.properties.get_property(slot).range()
                        if isinstance(range, list) and len(range) > 0 and isinstance(range[0], Concept):
                            pass
                        elif isinstance(range, set):
                            range = list(range)
                        else:
                            range = [range]
                        for r in range:
                            out.append(Concept.LocalRow(self, slot, facet, r, dict()))
                    else:
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

    def allowed(self, slot: str, filler) -> bool:
        return self.evaluate(slot, filler) > 0.0

    def evaluate(self, slot: str, filler) -> float:
        # Evaluate against value facet; if any are found, return here
        scores = list(map(lambda f: self._evaluate_filler(filler, f, 1.0), self.fillers(slot, "value")))
        if len(scores) > 0:
            return max(scores)

        # Evaluate against all other facets, returning the highest
        scores = []
        for facet in [("default", 1.0), ("sem", 0.9), ("relaxable-to", 0.25), ("not", 0.0)]:
            scores.extend(map(lambda f: self._evaluate_filler(filler, f, facet[1]), self.fillers(slot, facet[0])))

        if len(scores) > 0:
            return max(scores)

        return 0.0

    def _evaluate_filler(self, input, existing, penalty: float) -> float:
        if isinstance(input, str):
            return penalty * self._evaluate_literal_filler(input, existing)
        if isinstance(input, bool):
            return penalty * self._evaluate_boolean_filler(input, existing)
        if isinstance(input, float) or isinstance(input, int):
            return penalty * self._evaluate_number_filler(input, existing)
        if isinstance(input, Concept):
            return penalty * self._evaluate_concept_filler(input, existing)

        raise NotImplementedError

    def _evaluate_literal_filler(self, literal: str, existing) -> float:
        from leia.ontomem.properties import WILDCARD

        if isinstance(existing, str):
            return 1.0 if literal == existing else 0.0
        if isinstance(existing, list):
            return 1.0 if literal in existing else 0.0
        if existing == WILDCARD.ANYLIT:
            return 1.0
        return 0.0

    def _evaluate_boolean_filler(self, boolean: bool, existing) -> float:
        from leia.ontomem.properties import WILDCARD

        if isinstance(existing, bool):
            return 1.0 if boolean == existing else 0.0
        if existing == WILDCARD.ANYBOOL:
            return 1.0
        return 0.0

    def _evaluate_number_filler(self, number: Union[int, float], existing) -> float:
        from leia.ontomem.properties import COMPARATOR, WILDCARD

        if isinstance(existing, float) or isinstance(existing, int):
            return 1.0 if number == existing else 0.0
        if isinstance(existing, tuple) and isinstance(existing[0], COMPARATOR):
            if existing[0] == COMPARATOR.GT:
                return 1.0 if number > existing[1] else 0.0
            if existing[0] == COMPARATOR.GTE:
                return 1.0 if number >= existing[1] else 0.0
            if existing[0] == COMPARATOR.LT:
                return 1.0 if number < existing[1] else 0.0
            if existing[0] == COMPARATOR.LTE:
                return 1.0 if number <= existing[1] else 0.0
            if existing[0] == COMPARATOR.BETWEEN:
                return 1.0 if number > existing[1] and number < existing[2] else 0.0
            if existing[0] == COMPARATOR.INCLUDE:
                return 1.0 if number >= existing[1] and number <= existing[2] else 0.0
        if existing == WILDCARD.ANYNUM:
            return 1.0
        return 0.0

    def _evaluate_concept_filler(self, concept: 'Concept', existing) -> float:
        from leia.ontomem.properties import COMPARATOR, WILDCARD

        if isinstance(existing, Concept):
            return 1.0 if concept.isa(existing) else 0.0
        if existing == WILDCARD.ANYTYPE:
            return 1.0
        return 0.0

    def __repr__(self):
        return "@%s" % self.name


class OSet(object):

    class Type(Enum):
        CONJUNCTIVE = "CONJUNCTIVE"
        DISJUNCTIVE = "DISJUNCTIVE"

    def __init__(self, memory: Memory, name: str, contents: dict=None, root: 'Concept'=None):
        self.memory = memory
        self.name = name
        self.contents = contents
        self.root = root

        self._type = OSet.Type.CONJUNCTIVE
        self._cardinality = 0
        self._members = []

        if contents is not None:
            self._index()

    def set_contents(self, contents: dict):
        self.contents = contents
        self._index()

    def _index(self):
        self._type = OSet.Type[self.contents["type"].upper()]
        self._cardinality = self.contents["cardinality"]

        self._members = []
        for m in self.contents["members"]:
            if m.startswith("@"):
                if m[1:] in self.root.private:
                    self._members.append(self.root.private[m[1:]])
                else:
                    self._members.append(self.memory.ontology.concept(m[1:]))
            if m.startswith("&"):
                if m[1:] in self.root.private:
                    self._members.append(self.root.private[m[1:]])
            if m.startswith("$"):
                self._members.append(self.memory.properties.get_property(m[1:]))

    def type(self) -> Type:
        return self._type

    def cardinality(self) -> int:
        return self._cardinality

    def members(self) -> List[Union[Concept, 'Property', 'OSet']]:
        return list(self._members)


if __name__ == "__main__":

    knowledge_dir = "%s/leia/knowledge/concepts" % os.getcwd()

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

