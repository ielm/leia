from typing import Set


class Memory(object):

    class EditBuffers(object):

        def __init__(self, memory: 'Memory'):
            self.ontology = OntoMemEditBuffer(memory)
            self.properties = OntoMemEditBuffer(memory)
            self.lexicon = OntoMemEditBuffer(memory)

    def __init__(self, props_path: str, ont_path: str, lex_path: str):
        from leia.ontomem.episodic import Space
        from leia.ontomem.lexicon import Lexicon
        from leia.ontomem.ontology import Ontology
        from leia.ontomem.properties import PropertyInventory

        self.episodic = Space(self, "EPISODIC", private=False)
        self.lexicon = Lexicon(self, lex_path, load_now=False)
        self.properties = PropertyInventory(self, props_path, load_now=False)
        self.ontology = Ontology(self, ont_path, load_now=False)

        self.edits = Memory.EditBuffers(self)


class OntoMemEditBuffer(object):

    def __init__(self, memory: Memory):
        self.memory = memory
        self.edits = dict()

    def edited(self, source: str=None) -> Set[str]:
        if source is not None:
            return set(map(lambda x: x[0], filter(lambda i: source in i[1], self.edits.items())))

        return set(self.edits.keys())

    def note_edited(self, identifier: str, source: str):
        if identifier not in self.edits:
            self.edits[identifier] = set()

        self.edits[identifier].add(source)

    def clear(self, identifier: str=None):
        if identifier is not None:
            del self.edits[identifier]
        else:
            self.edits = dict()