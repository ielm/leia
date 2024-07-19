from leia.ontomem.lexicon import SynStruc
from leia.ontomem.memory import Memory
from leia.ontosem.analysis import WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import Dependency
from leia.ontosem.syntax.synmapper import SynMatcher, SynMapper
from leia.tests.LEIATestCase import LEIATestCase


class SynMapperTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory("", "", "")


class SynMatcherTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory("", "", "")
        self.matcher = SynMatcher(OntoSemConfig(), self.m.ontology, WMLexicon())

    def test_does_root_match(self):
        root = self.mockWord(0, "root", "N")
        other = self.mockWord(1, "other", "N")

        # does_root_match is a trivial comparison of the specified input root (if any) against any given token;
        # it primarily exists for consistency and as a sanity check
        element = SynStruc.RootElement()

        self.assertFalse(self.matcher.does_root_match(element, root, None))
        self.assertFalse(self.matcher.does_root_match(element, root, other))
        self.assertTrue(self.matcher.does_root_match(element, root, root))

    def test_does_token_match_single_lemma(self):
        word = self.mockWord(0, "word", "N")

        # An empty lemma cannot be matched
        element = SynStruc.TokenElement(set(), None, dict(), None, False)
        self.assertFalse(self.matcher.does_token_match(element, word))

        # An incorrect lemma is not a match
        element = SynStruc.TokenElement({"other"}, None, dict(), None, False)
        self.assertFalse(self.matcher.does_token_match(element, word))

        # A correct lemma is a match
        element = SynStruc.TokenElement({"word"}, None, dict(), None, False)
        self.assertTrue(self.matcher.does_token_match(element, word))

    def test_does_token_match_multiple_lemmas(self):
        word = self.mockWord(0, "word", "N")

        # At least one lemma must be a match
        element = SynStruc.TokenElement({"other1", "other2"}, None, dict(), None, False)
        self.assertFalse(self.matcher.does_token_match(element, word))

        element = SynStruc.TokenElement({"word", "other1", "other2"}, None, dict(), None, False)
        self.assertTrue(self.matcher.does_token_match(element, word))

    def test_does_token_match_pos(self):
        word = self.mockWord(0, "word", "N")

        # An null POS is cannot be matched
        element = SynStruc.TokenElement(set(), None, dict(), None, False)
        self.assertFalse(self.matcher.does_token_match(element, word))

        # An incorrect POS is not a match
        element = SynStruc.TokenElement({}, "V", dict(), None, False)
        self.assertFalse(self.matcher.does_token_match(element, word))

        # A correct POS is a match
        element = SynStruc.TokenElement({}, "N", dict(), None, False)
        self.assertTrue(self.matcher.does_token_match(element, word))

    def test_does_token_match_morphology(self):
        word = self.mockWord(0, "word", "N", morphology={"A": 1, "B": 2})

        # An empty morphology is a match
        element = SynStruc.TokenElement({"word"}, None, dict(), None, False)
        self.assertTrue(self.matcher.does_token_match(element, word))

        # A partially matching morphology is a match
        element = SynStruc.TokenElement({"word"}, None, {"A": 1}, None, False)
        self.assertTrue(self.matcher.does_token_match(element, word))

        # A fully matching morphology is a match
        element = SynStruc.TokenElement({"word"}, None, {"A": 1, "B": 2}, None, False)
        self.assertTrue(self.matcher.does_token_match(element, word))

        # Any contradiction in the element is not a match
        element = SynStruc.TokenElement({"word"}, None, {"A": 1, "B": 2, "C": 3}, None, False)
        self.assertFalse(self.matcher.does_token_match(element, word))

        element = SynStruc.TokenElement({"word"}, None, {"A": 1, "B": 3}, None, False)
        self.assertFalse(self.matcher.does_token_match(element, word))

    def test_does_token_match_multiple_criteria(self):
        word = self.mockWord(0, "word", "N", morphology={"A": 1, "B": 2})

        element = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        self.assertTrue(self.matcher.does_token_match(element, word))

        element = SynStruc.TokenElement({"word", "other"}, "N", {"A": 1}, None, False)
        self.assertTrue(self.matcher.does_token_match(element, word))

        element = SynStruc.TokenElement({"word", "other"}, "V", {"A": 1}, None, False)
        self.assertFalse(self.matcher.does_token_match(element, word))

    def test_does_dependency_match_no_root(self):
        gov = self.mockWord(0, "gov", "N")
        dep = self.mockWord(1, "dep", "N")

        dep1 = Dependency(gov, dep, "NSUBJ")
        dep2 = Dependency(dep, gov, "NSUBJ")
        dep3 = Dependency(gov, dep, "DOBJ")

        # The only part of the element to match is the type; gov/dep in the element are for variable mapping, and are
        # not used here in any way.
        element = SynStruc.DependencyElement("NSUBJ", None, None, None, False)

        self.assertTrue(self.matcher.does_dependency_match(element, dep1, None))
        self.assertTrue(self.matcher.does_dependency_match(element, dep2, None))
        self.assertFalse(self.matcher.does_dependency_match(element, dep3, None))

    def test_does_dependency_match_with_root(self):
        gov = self.mockWord(0, "gov", "N")
        dep = self.mockWord(1, "dep", "N")

        dep1 = Dependency(gov, dep, "NSUBJ")
        dep2 = Dependency(dep, gov, "NSUBJ")
        dep3 = Dependency(gov, dep, "DOBJ")

        element = SynStruc.DependencyElement("NSUBJ", None, None, None, False)

        # In order to match with a specified root, the root must be the governor.
        self.assertTrue(self.matcher.does_dependency_match(element, dep1, gov))
        self.assertFalse(self.matcher.does_dependency_match(element, dep2, gov))
        self.assertFalse(self.matcher.does_dependency_match(element, dep3, gov))

    """
    TODO: tests to run:
    - can it match a dependency
        - type (from root)
        - type (without root, matches all possible)
    - can it match a constituency
        - type
        - with children
        - recursive
    - does it match multiple elements in a row
        - respect ordering (for now, allow gapping)
        - ordering for constituencies at the top level implies flattening
        - does it skip optional (or, rather, returns a None in the match column)
    - does it find multiple possible combinations
    """