from dataclasses import dataclass
from leia.ontomem.lexicon import SynStruc
from leia.ontomem.ontology import Ontology
from leia.ontosem.analysis import WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import ConstituencyNode, Dependency, SynMap, Syntax, Word
from typing import List, Union


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

    def does_root_match(self, element: SynStruc.RootElement, word: Word, specified_root: Union[Word, None]) -> bool:
        # This matching function is trivial; it takes the candidate word and checks to see if the root specified (if any)
        # is the same word.  This primarily exists for consistency (all syn-struc element types can have a corresponding
        # "does_x_match" function), and also as a home for any future complexities if needed.

        return word == specified_root

    def does_token_match(self, element: SynStruc.TokenElement, word: Word) -> bool:
        # If both lemmas and POS are unspecified, no match is allowed
        if len(element.lemmas) == 0 and element.pos is None:
            return False

        # If lemmas are specified, at least one must be a match; case insensitive
        if len(element.lemmas) > 0:
            if word.lemma.lower() not in set(map(lambda l: l.lower(), element.lemmas)):
                return False

        # If POS is specified, at least one must be a match; case insensitive
        # TODO: Possibly use a hierarchy of POS matching here
        if element.pos is not None:
            if element.pos.lower() not in set(map(lambda p: p.lower(), word.pos)):
                return False

        # If any morphology is specified, each must be a match; case sensitive
        for k, v in element.morph.items():
            if k not in word.morphology:
                return False
            if word.morphology[k] != v:
                return False

        # No filtering has occurred; the token is considered a match
        return True

    def does_dependency_match(self, element: SynStruc.DependencyElement, dependency: Dependency, root: Union[Word, None]) -> bool:
        # The type must match
        if element.type.lower() != dependency.type.lower():
            return False

        # If a root was provided, it must be the governor
        if root is not None:
            if dependency.governor != root:
                return False

        # No filtering has occurred; the dependency is considered a match
        return True

    def does_constituency_match(self, element: SynStruc.ConstituencyElement, node: ConstituencyNode) -> bool:
        # The type must match
        if element.type.lower() != node.label.lower():
            return False

        # If any children are specified, they must be found, IN ORDER, in the node;
        # valid children are more constituencies, or tokens.
        candidate_children = iter(node.children)
        for child in element.children:
            found = False
            for candidate_child in candidate_children:
                if isinstance(child, SynStruc.ConstituencyElement) and isinstance(candidate_child, ConstituencyNode):
                    if self.does_constituency_match(child, candidate_child):
                        found = True
                        break
                if isinstance(child, SynStruc.TokenElement) and isinstance(candidate_child, Word):
                    if self.does_token_match(child, candidate_child):
                        found = True
                        break
            if not found:
                return False

        # No filtering has occurred; the constituency is considered a match
        return True