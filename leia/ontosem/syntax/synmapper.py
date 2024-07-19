from dataclasses import dataclass
from leia.ontomem.lexicon import SynStruc
from leia.ontomem.ontology import Ontology
from leia.ontosem.analysis import WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import ConstituencyNode, Dependency, SynMap, Syntax, Word
from typing import List


class SynMapper(object):

    def __init__(self, config: OntoSemConfig, ontology: Ontology, lexicon: WMLexicon):
        self.config = config
        self.ontology = ontology
        self.lexicon = lexicon

    def run(self, syntax: Syntax) -> SynMap:
        raise NotImplementedError


class SynMatcher(object):

    """
    The job of the SynMatcher is to find any matches between an input SynStruc definition and the current syntactic
    analysis.  That is, if the SynStruc demands certain dependencies, constituencies, or tokens, the SynMatcher
    will attempt to identify and align those components in the input syntax.

    The SynMatcher respects the order of elements in the SynStruc.

    A specified root token may be optionally provided.
    """

    class SynMatch:
        pass

    @dataclass
    class RootMatch(SynMatch):
        element: SynStruc.RootElement
        match: Word

    @dataclass
    class TokenMatch(SynMatch):
        element: SynStruc.TokenElement
        match: Word

    @dataclass
    class DependencyMatch(SynMatch):
        element: SynStruc.DependencyElement
        match: Dependency

    @dataclass
    class ConstituencyMatch(SynMatch):
        element: SynStruc.ConstituencyElement
        match: ConstituencyNode

    @dataclass
    class SynMatchResult(object):
        matches: List['SynMatcher.SynMatch']

    def __init__(self, config: OntoSemConfig, ontology: Ontology, lexicon: WMLexicon):
        self.config = config
        self.ontology = ontology
        self.lexicon = lexicon

    def run(self, syntax: Syntax, synstruc: SynStruc, root: Word=None) -> List['SynMatcher.SynMatchResult']:
        raise NotImplementedError

    # [
    #     {"type": "dependency", "deptype": "nsubjpass", "governor": 0}
    # ],
    # [
    #     {"type": "constituency", "contype": "NP", "children": []},
    #     {"type": "token", "lemma": ["be"], "pos": null, "morph": {}},
    #     {"type": "token", "lemma": [], "pos": "V", "var": 0, "morph": {"tense": "past", "verbform": "part"}}
    # ]