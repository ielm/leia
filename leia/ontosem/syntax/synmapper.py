from dataclasses import dataclass
from leia.ontomem.lexicon import Sense, SynStruc
from leia.ontomem.ontology import Ontology
from leia.ontosem.analysis import WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import ConstituencyNode, Dependency, SenseMap, SynMap, Syntax, Word
from typing import Any, Iterable, List, Tuple, Type, Union


class SynMapper(object):

    """
    The job of the SynMapper is to find all possible variable matches for each sense of each word in the input
    syntax.  The SynMapper does not prune any possibilities at this point, but does apply scoring penalties
    when a sense is a poor match (e.g., it is the wrong POS, or not all of its non-optional synstruc elements
    can be aligned to a syntactic component).
    """

    def __init__(self, config: OntoSemConfig, ontology: Ontology, lexicon: WMLexicon):
        self.config = config
        self.ontology = ontology
        self.lexicon = lexicon

    def run(self, syntax: Syntax) -> SynMap:
        raise NotImplementedError

    def build_sense_maps(self, syntax: Syntax, word: Word, sense: Sense) -> Iterable[SenseMap]:
        results = SynMatcher(self.config, self.ontology, self.lexicon).run(syntax, sense.synstruc, root=word)

        for result in results:
            bindings = dict()

            for match in result.matches:
                varmap = self.map_variable(match)
                if varmap is not None:
                    bindings[varmap[0]] = varmap[1]

            yield SenseMap(word, sense.id, bindings, 1.0)

    def map_variable(self, match: 'SynMatcher.SynMatch') -> Union[Tuple[str, int], None]:
        variable = match.element.to_variable()

        if variable is None:
            return None

        if match.component is None:
            return None

        if isinstance(match, SynMatcher.RootMatch) and variable == 0:
            return ("$VAR%d" % variable, match.component.index)

        if isinstance(match, SynMatcher.TokenMatch):
            return ("$VAR%d" % variable, match.component.index)

        if isinstance(match, SynMatcher.DependencyMatch):
            return ("$VAR%d" % variable, match.component.dependent.index)

        if isinstance(match, SynMatcher.ConstituencyMatch):
            return ("$VAR%d" % variable, match.component.leftmost_word().index)

        # If none of the above can be selected, no variable can be mapped.
        return None


class SynMatcher(object):

    """
    The job of the SynMatcher is to find any matches between an input SynStruc definition and the current syntactic
    analysis.  That is, if the SynStruc demands certain dependencies, constituencies, or tokens, the SynMatcher
    will attempt to identify and align those components in the input syntax.

    The SynMatcher respects the order of elements in the SynStruc.

    A specified root token may be optionally provided.
    """

    class SynMatch:
        element: SynStruc.Element
        component: Any

    @dataclass
    class RootMatch(SynMatch):
        element: SynStruc.RootElement
        component: Word

    @dataclass
    class TokenMatch(SynMatch):
        element: SynStruc.TokenElement
        component: Word

    @dataclass
    class DependencyMatch(SynMatch):
        element: SynStruc.DependencyElement
        component: Dependency

    @dataclass
    class ConstituencyMatch(SynMatch):
        element: SynStruc.ConstituencyElement
        component: ConstituencyNode

    @dataclass
    class SynMatchResult(object):
        matches: List['SynMatcher.SynMatch']

    def __init__(self, config: OntoSemConfig, ontology: Ontology, lexicon: WMLexicon):
        self.config = config
        self.ontology = ontology
        self.lexicon = lexicon

    def run(self, syntax: Syntax, synstruc: SynStruc, root: Word=None) -> List['SynMatcher.SynMatchResult']:
        elements = synstruc.elements
        components = self.flatten(syntax)

        return self.match(elements, components, root)

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

        # Takes an ordered list of elements from a syn-struc and a flattened list of components from a syntactic parse.
        # Finds all possible alignments of those elements into the components, allowing for any gaps in between, so
        # long as ordering is maintained.

        # Elements that are marked as optional will produce a result with a null match, in addition to any results
        # with actual matching components.

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
            # Finds all matches of the element from the input list of components, yielding each match in order.
            # Yielded results include the match, and the remaining components (that is, components which are ordered
            # after the match, as any further match attempts for this result set must follow in order).
            for i, component in enumerate(components):
                if self.does_element_match(element, component, root=root):
                    yield _get_match_type(element)(element, component), components[i:]

        def _expand_matches(matches: List[dict]) -> Iterable[dict]:
            # Given a list of partial matches (that is, some set of elements -> components), take the next element
            # (declared in the loop below), and find the next matching component for it starting from the next
            # available component (per match).  In addition, if the element is optional, add an additional null
            # match to each current match set.
            for match in matches:
                for nm in _find_matches(element, match["remaining"]):
                    yield {
                        "match": match["match"] + [nm[0]],
                        "remaining": nm[1]
                    }
                if element.is_optional():
                    yield {
                        "match": match["match"] + [_get_match_type(element)(element, None)],
                        "remaing": list(match["remaining"])
                    }

        # Start with the first element.  Find all matches to that element; if the element is optional, add another
        # "match" to a null component.
        element = elements.pop(0)
        matches = list(map(lambda m: {"match": [m[0]], "remaining": m[1]}, _find_matches(element, components)))
        if element.is_optional():
            matches.append({"match": [_get_match_type(element)(element, None)], "remaining": list(components)})

        # Now continue with each element in order, passing in the full list of matches from the prior set of results.
        while len(elements) > 0:
            element = elements.pop(0)
            matches = list(_expand_matches(matches))

        # Convert the results into SynMatchResult objects.
        return list(map(lambda m: SynMatcher.SynMatchResult(m["match"]), matches))

    def does_element_match(self, element: SynStruc.Element, component: Union[Word, Dependency, ConstituencyNode], root: Word=None) -> bool:
        # Generic matching of any synstruc element to any syntax component(s).  Essentially, this function verifies
        # type matching and then calls the specific does_x_match function and returns its results.

        if isinstance(element, SynStruc.RootElement):
            if isinstance(component, Word):
                return self.does_root_match(element, component, root=root)

        if isinstance(element, SynStruc.TokenElement):
            if isinstance(component, Word):
                return self.does_token_match(element, component, root=root)

        if isinstance(element, SynStruc.DependencyElement):
            if isinstance(component, Dependency):
                return self.does_dependency_match(element, component, root=root)

        if isinstance(element, SynStruc.ConstituencyElement):
            if isinstance(component, ConstituencyNode):
                return self.does_constituency_match(element, component, root=root)

        # The type is unknown, return False.
        return False


    def does_root_match(self, element: SynStruc.RootElement, word: Word, root: Union[Word, None]) -> bool:
        # This matching function is trivial; it takes the candidate word and checks to see if the root specified (if any)
        # is the same word.  This primarily exists for consistency (all syn-struc element types can have a corresponding
        # "does_x_match" function), and also as a home for any future complexities if needed.

        return word == root

    def does_token_match(self, element: SynStruc.TokenElement, word: Word, root: Union[Word, None]) -> bool:
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

    def does_constituency_match(self, element: SynStruc.ConstituencyElement, node: ConstituencyNode, root: Union[Word, None]) -> bool:
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