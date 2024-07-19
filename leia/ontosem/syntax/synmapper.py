from leia.ontomem.ontology import Ontology
from leia.ontosem.analysis import WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import SynMap, Syntax


class SynMapper(object):

    def __init__(self, config: OntoSemConfig, ontology: Ontology, lexicon: WMLexicon):
        self.config = config
        self.ontology = ontology
        self.lexicon = lexicon

    def run(self, syntax: Syntax) -> SynMap:
        raise NotImplementedError