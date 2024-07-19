from typing import Set

import importlib


class Memory(object):

    class EditBuffers(object):

        def __init__(self, memory: "Memory"):
            self.ontology = OntoMemEditBuffer(memory)
            self.properties = OntoMemEditBuffer(memory)
            self.lexicon = OntoMemEditBuffer(memory)

    def __init__(
        self,
        knowledge_path: str = None,
        props_path: str = None,
        ont_path: str = None,
        lex_path: str = None,
        trans_path: str = None,
        pos_file: str = None,
    ):
        if knowledge_path is None:
            knowledge_path = (
                "%s/knowledge" % importlib.import_module("leia").__path__[0]
            )

        if props_path is None:
            props_path = "%s/properties" % knowledge_path
        if ont_path is None:
            ont_path = "%s/concepts" % knowledge_path
        if lex_path is None:
            lex_path = "%s/words" % knowledge_path
        if trans_path is None:
            trans_path = "%s/transformations" % knowledge_path
        if pos_file is None:
            pos_file = "%s/grammar/pos.json" % knowledge_path

        from leia.ontomem.episodic import Space
        from leia.ontomem.grammar import POSInventory
        from leia.ontomem.lexicon import Lexicon
        from leia.ontomem.ontology import Ontology
        from leia.ontomem.properties import PropertyInventory
        from leia.ontomem.transformations import TransformationsCatalogue

        self.episodic = Space(self, "EPISODIC", private=False)
        self.lexicon = Lexicon(self, lex_path, load_now=False)
        self.properties = PropertyInventory(self, props_path, load_now=False)
        self.ontology = Ontology(self, ont_path, load_now=False)
        self.transformations = TransformationsCatalogue(
            self, trans_path, load_now=False
        )
        self.parts_of_speech = POSInventory(self, pos_file, load_now=False)

        self.edits = Memory.EditBuffers(self)


class OntoMemEditBuffer(object):

    def __init__(self, memory: Memory):
        self.memory = memory
        self.edits = dict()

    def edited(self, source: str = None) -> Set[str]:
        if source is not None:
            return set(
                map(
                    lambda x: x[0], filter(lambda i: source in i[1], self.edits.items())
                )
            )

        return set(self.edits.keys())

    def note_edited(self, identifier: str, source: str):
        if identifier not in self.edits:
            self.edits[identifier] = set()

        self.edits[identifier].add(source)

    def clear(self, identifier: str = None):
        if identifier is not None:
            del self.edits[identifier]
        else:
            self.edits = dict()
