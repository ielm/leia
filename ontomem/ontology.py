from multiprocessing import Pool
from ontomem.memory import Memory
from typing import List, Iterable, Set, Tuple, Union

import json
import os


# TODO: Following functionalities are needed at a minimum
#  - handling not
#  - handling overrides (import, process, assign, remove)
#  - handling metadata (import, process, assign, remove)
#  - general editing (assign, remove, update)
#  - listing of a frame by rows (with inh/block) for the editor
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
        if name in self.cache:
            return self.cache[name]
        return None

    def usages(self, concept: 'Concept') -> Iterable[Tuple['Concept', str, str]]:
        for c in self.cache.values():
            for sk, sv in c.slots.items():
                for fk, fv in sv.items():
                    if concept in fv:
                        yield c, sk, fk


class Concept(object):

    def __init__(self, memory: Memory, name: str, contents: dict=None):
        self.memory = memory
        self.name = name
        self.contents = contents
        self.slots = dict()

        if contents is not None:
            self._index()

    def set_contents(self, contents: dict):
        self.contents = contents
        self._index()

    def _index(self):

        self.slots = dict()

        for row in self.contents["local"]:
            slot = row["slot"]
            facet = row["facet"]
            filler = row["filler"]

            # Parse various filler types
            if isinstance(filler, str):
                if filler[0] == "@":
                    # TODO: this isn't handling private concepts currently; override the namespace if needed
                    filler = self.memory.ontology.concept(filler[1:])
                elif filler[0] == "$":
                    filler = self.memory.properties.get_property(filler[1:])
                elif filler[0] == "&":
                    # TODO: get the set
                    raise NotImplementedError

            if slot not in self.slots:
                self.slots[slot] = dict()
            if facet not in self.slots[slot]:
                self.slots[slot][facet] = list()
            self.slots[slot][facet].append(filler)

    def parents(self) -> Set['Concept']:
        return set(map(lambda p: self.memory.ontology.concept(p[1:]), self.contents["isa"]))

    def ancestors(self) -> Set['Concept']:
        raise NotImplementedError

    def children(self) -> Set['Concept']:
        raise NotImplementedError

    def descendants(self) -> Set['Concept']:
        raise NotImplementedError

    def siblings(self) -> Set['Concept']:
        raise NotImplementedError

    def fillers(self, slot: str, facet: str) -> List:
        results = []

        if slot in self.slots:
            if facet in self.slots[slot]:
                results.extend(self.slots[slot][facet])

        for parent in self.parents():
            results.extend(parent.fillers(slot, facet))

        return results

    def allowed(self, slot: str, facet: str, filler) -> bool:
        raise NotImplementedError

    def evaluate(self, slot: str, facet: str, filler) -> float:
        raise NotImplementedError

    def __repr__(self):
        return "@%s" % self.name


if __name__ == "__main__":

    knowledge_dir = "%s/knowledge/concepts" % os.getcwd()

    memory = Memory("", knowledge_dir)
    ontology = memory.ontology
    ontology.load()

    print(ontology.concept("human").contents)
    print(ontology.concept("human").parents())
    print(ontology.concept("human").fillers("has-object-as-part", "sem"))
    print(ontology.concept("human").fillers("has-object-as-part", "sem")[0].contents)

