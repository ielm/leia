from dataclasses import dataclass
from leia.ontomem.lexicon import SynStruc
from leia.ontomem.ontology import Ontology
from leia.ontosem.analysis import WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import ConstituencyNode, Dependency, SynMap, Syntax, Word
from typing import Iterable, List, Tuple, Type, Union


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

    def flatten(self, syntax: Syntax) -> List[Union[Word, Dependency, ConstituencyNode]]:
        # This method flattens the main syntactic elements into an ordered list representing their relative
        # locations in the text.  The three output elements are Words, Dependencies, and Constituencies.
        # Words are output in their natural order.
        # Dependencies are output following the word that is their dependent, in the order they were entered.
        # Constituencies are output following the word that is their left-most leaf, in the order they were entered;
        #  (this is a recursive output - all nodes in the constituency tree will appear in the output).

        # Organize all non-word elements by word, for easy sorting.
        dependencies_by_word = dict()
        constituencies_by_word = dict()

        for word in syntax.words:
            dependencies_by_word[word] = []
            constituencies_by_word[word] = []

        # Sort dependencies by their dependent.
        for dependency in syntax.dependencies:
            dependencies_by_word[dependency.dependent].append(dependency)

        # Sort constituencies by their leftmost word.
        def _flatten_node(node):
            word = node.leftmost_word()
            if word is not None:
                constituencies_by_word[word].append(node)

            for child in filter(lambda c: isinstance(c, ConstituencyNode), node.children):
                _flatten_node(child)

        _flatten_node(syntax.parse)

        # Define and construct the final output.
        flattened = []

        # Add the words in order
        # Following each word, add the dependencies and constituencies
        for word in syntax.words:
            flattened.append(word)

            for dependency in dependencies_by_word[word]:
                flattened.append(dependency)

            for constituency in constituencies_by_word[word]:
                flattened.append(constituency)

        return flattened

    def match(self, elements: List[SynStruc.Element], components: List[Union[Word, Dependency, ConstituencyNode]], root: Union[Word, None]) -> List['SynMatcher.SynMatchResult']:

        def _get_match_type(element: SynStruc.Element) -> Type[SynMatcher.SynMatch]:
            if isinstance(element, SynStruc.RootElement):
                return SynMatcher.RootMatch
            if isinstance(element, SynStruc.TokenElement):
                return SynMatcher.TokenMatch
            if isinstance(element, SynStruc.DependencyElement):
                return SynMatcher.DependencyMatch
            if isinstance(element, SynStruc.ConstituencyElement):
                return SynMatcher.ConstituencyMatch
            raise Exception

        def _find_matches(element: SynStruc.Element, components: List[Union[Word, Dependency, ConstituencyNode]]) -> Iterable[Tuple['SynMatcher.SynMatch', List[Union[Word, Dependency, ConstituencyNode]]]]:
            for i, component in enumerate(components):
                if self.does_element_match(element, component):
                    yield _get_match_type(element)(element, component), components[i:]

        def _expand_matches(matches: List[dict]) -> List[dict]:
            for match in matches:
                for nm in _find_matches(element, match["remaining"]):
                    yield {
                        "match": match["match"] + [nm[0]],
                        "remaining": nm[1]
                    }

        element = elements.pop(0)
        matches = list(map(lambda m: {"match": [m[0]], "remaining": m[1]}, _find_matches(element, components)))

        while len(elements) > 0:
            element = elements.pop(0)
            matches = list(_expand_matches(matches))

        return list(map(lambda m: SynMatcher.SynMatchResult(m["match"]), matches))

    def does_element_match(self, element: SynStruc.Element, *args) -> bool:
        # Generic matching of any synstruc element to any syntax component(s).  Essentially, this function verifies
        # type matching and then calls the specific does_x_match function and returns its results.

        if isinstance(element, SynStruc.RootElement):
            if len(args) == 2 and isinstance(args[0], Word) and (isinstance(args[1], Word) or args[1] is None):
                return self.does_root_match(element, args[0], args[1])
            return False

        if isinstance(element, SynStruc.TokenElement):
            if len(args) == 1 and isinstance(args[0], Word):
                return self.does_token_match(element, args[0])
            return False

        if isinstance(element, SynStruc.DependencyElement):
            if len(args) == 2 and isinstance(args[0], Dependency) and (isinstance(args[1], Word) or args[1] is None):
                return self.does_dependency_match(element, args[0], args[1])
            return False

        if isinstance(element, SynStruc.ConstituencyElement):
            if len(args) == 1 and isinstance(args[0], ConstituencyNode):
                return self.does_constituency_match(element, args[0])
            return False

        # The type is unknown, return False.
        return False


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
                if self.does_element_match(child, candidate_child):
                    found = True
                    break
            if not found:
                return False

        # No filtering has occurred; the constituency is considered a match
        return True