

class Memory(object):

    def __init__(self, props_path: str, ont_path: str, lex_path: str):
        from leia.ontomem.episodic import EpisodicMemory
        from leia.ontomem.lexicon import Lexicon
        from leia.ontomem.ontology import Ontology
        from leia.ontomem.properties import PropertyInventory

        self.episodic = EpisodicMemory(self)
        self.lexicon = Lexicon(self, lex_path, load_now=False)
        self.properties = PropertyInventory(self, props_path, load_now=False)
        self.ontology = Ontology(self, ont_path, load_now=False)


class TCPMemory(object):

    pass