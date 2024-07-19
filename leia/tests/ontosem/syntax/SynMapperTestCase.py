from leia.ontomem.lexicon import SynStruc
from leia.ontomem.memory import Memory
from leia.ontosem.analysis import WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import ConstituencyNode, Dependency, Syntax
from leia.ontosem.syntax.synmapper import SynMatcher, SynMapper
from leia.tests.LEIATestCase import LEIATestCase
from unittest.mock import MagicMock


class SynMapperTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory("", "", "")


class SynMatcherTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory("", "", "")
        self.matcher = SynMatcher(OntoSemConfig(), self.m.ontology, WMLexicon())

    def test_does_element_match(self):
        # This generic function checks to see if a syn-struc element and any syntax component are a match.
        # If their core types are not compatible, the result is false.  Otherwise, the corresponding does_x_match
        # function is called, and its result is returned.

        # Incompatible types do not even call the correct function; they just return false.
        self.matcher.does_root_match = MagicMock(return_value="a")
        self.matcher.does_token_match = MagicMock(return_value="b")
        self.matcher.does_dependency_match = MagicMock(return_value="c")
        self.matcher.does_constituency_match = MagicMock(return_value="d")

        self.assertFalse(self.matcher.does_element_match(SynStruc.RootElement(), None))
        self.matcher.does_root_match.assert_not_called()

        self.assertFalse(self.matcher.does_element_match(SynStruc.TokenElement(set(), None, dict(), None, False), None))
        self.matcher.does_token_match.assert_not_called()

        self.assertFalse(self.matcher.does_element_match(SynStruc.DependencyElement("", None, None, None, False), None))
        self.matcher.does_dependency_match.assert_not_called()

        self.assertFalse(self.matcher.does_element_match(SynStruc.ConstituencyElement("", [], None, False), None))
        self.matcher.does_constituency_match.assert_not_called()

        # Compatible types call the correct function and return its results.
        args = [SynStruc.RootElement(), self.mockWord(0, "X", "N"), None]
        self.assertEqual("a", self.matcher.does_element_match(*args))
        self.matcher.does_root_match.assert_called_once_with(*args)

        args = [SynStruc.TokenElement(set(), None, dict(), None, False), self.mockWord(0, "X", "N")]
        self.assertEqual("b", self.matcher.does_element_match(*args))
        self.matcher.does_token_match.assert_called_once_with(*args)

        args = [SynStruc.DependencyElement("", None, None, None, False), Dependency(self.mockWord(1, "A", "N"), self.mockWord(2, "B", "N"), "Z"), self.mockWord(0, "X", "N")]
        self.assertEqual("c", self.matcher.does_element_match(*args))
        self.matcher.does_dependency_match.assert_called_once_with(*args)

        args = [SynStruc.ConstituencyElement("", [], None, False), ConstituencyNode("NP"),]
        self.assertEqual("d", self.matcher.does_element_match(*args))
        self.matcher.does_constituency_match.assert_called_once_with(*args)

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

    def test_does_constituency_match_no_children(self):
        node1 = ConstituencyNode("NP")
        node2 = ConstituencyNode("VP")

        element = SynStruc.ConstituencyElement("NP", [], None, False)

        # The node type must always be a match, regardless of any children
        self.assertTrue(self.matcher.does_constituency_match(element, node1))
        self.assertFalse(self.matcher.does_constituency_match(element, node2))

    def test_does_constituency_match_with_constituency_children(self):
        node1 = ConstituencyNode("NP")
        node1.children = [ConstituencyNode("X")]

        node2 = ConstituencyNode("NP")
        node2.children = [ConstituencyNode("Y")]

        element = SynStruc.ConstituencyElement("NP", [SynStruc.ConstituencyElement("X", [], None, False)], None, False)

        # The children must match as well as the outer type.  Children can be other constituency nodes.
        self.assertTrue(self.matcher.does_constituency_match(element, node1))
        self.assertFalse(self.matcher.does_constituency_match(element, node2))

    def test_does_constituency_match_with_token_children(self):
        node1 = ConstituencyNode("NP")
        node1.children = [self.mockWord(0, "a", "N")]

        node2 = ConstituencyNode("NP")
        node2.children = [self.mockWord(0, "b", "N")]

        element = SynStruc.ConstituencyElement("NP", [SynStruc.TokenElement({"a"}, "N", dict(), None, False)], None, False)

        # The children must match as well as the outer type.  Children can be words.
        self.assertTrue(self.matcher.does_constituency_match(element, node1))
        self.assertFalse(self.matcher.does_constituency_match(element, node2))

    def test_does_constituency_match_with_multiple_children(self):
        node1 = ConstituencyNode("NP")
        node1.children = [ConstituencyNode("X"), ConstituencyNode("Y")]

        node2 = ConstituencyNode("NP")
        node2.children = [ConstituencyNode("X")]

        node3 = ConstituencyNode("NP")
        node3.children = [ConstituencyNode("Y"), ConstituencyNode("X")]

        element = SynStruc.ConstituencyElement("NP", [
            SynStruc.ConstituencyElement("X", [], None, False),
            SynStruc.ConstituencyElement("Y", [], None, False),
        ], None, False)

        # Multiple children may be required; their ordering matters..
        self.assertTrue(self.matcher.does_constituency_match(element, node1))
        self.assertFalse(self.matcher.does_constituency_match(element, node2))
        self.assertFalse(self.matcher.does_constituency_match(element, node3))

    def test_does_constituency_match_recursive_children(self):
        node1 = ConstituencyNode("NP")
        node1a = ConstituencyNode("A")
        node1b = ConstituencyNode("B")
        node1c = ConstituencyNode("C")

        node1.children = [node1a, node1b]
        node1a.children = [node1c]

        node2 = ConstituencyNode("NP")
        node2a = ConstituencyNode("A")
        node2b = ConstituencyNode("B")
        node2c = ConstituencyNode("C")

        node2.children = [node2a, node2b]
        node2b.children = [node2c]

        element = SynStruc.ConstituencyElement("NP", [
            SynStruc.ConstituencyElement("A", [
                SynStruc.ConstituencyElement("C", [], None, False)
            ], None, False),
            SynStruc.ConstituencyElement("B", [], None, False),
        ], None, False)

        # The child structure is fully recursive.
        self.assertTrue(self.matcher.does_constituency_match(element, node1))
        self.assertFalse(self.matcher.does_constituency_match(element, node2))

    def test_flatten_syntax_words_only(self):
        word1 = self.mockWord(1, "w1", "N")
        word2 = self.mockWord(2, "w2", "N")
        word3 = self.mockWord(3, "w3", "N")

        syntax = Syntax([word1, word2, word3], "", "", ConstituencyNode(""), [])

        # Flattened words is trivial; the order they are entered is the order they are emitted.
        # The constituency node should be skipped as it has no inner token (it is essentially empty).

        self.assertEqual([word1, word2, word3], self.matcher.flatten(syntax))

    def test_flatten_syntax_words_with_dependencies(self):
        word1 = self.mockWord(1, "w1", "N")
        word2 = self.mockWord(2, "w2", "N")
        word3 = self.mockWord(3, "w3", "N")

        dep1 = Dependency(word1, word1, "X")
        dep2 = Dependency(word1, word1, "Y")
        dep3 = Dependency(word1, word2, "Z")

        syntax = Syntax([word1, word2, word3], "", "", ConstituencyNode(""), [dep1, dep2, dep3])

        # Flattened dependencies are sorted after their dependent words in the order they are entered.
        # The constituency node should be skipped as it has no inner token (it is essentially empty).

        self.assertEqual([
            word1,
            dep1,
            dep2,
            word2,
            dep3,
            word3
        ], self.matcher.flatten(syntax))

    def test_flatten_syntax_words_with_consituencies(self):
        word1 = self.mockWord(1, "w1", "N")
        word2 = self.mockWord(2, "w2", "N")
        word3 = self.mockWord(3, "w3", "N")
        word4 = self.mockWord(4, "w4", "N")

        node0 = ConstituencyNode("0")
        node1 = ConstituencyNode("1")
        node2 = ConstituencyNode("2")
        node3 = ConstituencyNode("3")
        node4 = ConstituencyNode("4")
        node5 = ConstituencyNode("5")

        """
        The constituency tree looks like:
        
        N0
            N1
                W1
                N3
                    W2
            N2
                N4
                    W3
                N5
                    W4
        """

        node0.children = [node1, node2]
        node1.children = [word1, node3]
        node3.children = [word2]
        node2.children = [node4, node5]
        node4.children = [word3]
        node5.children = [word4]

        syntax = Syntax([word1, word2, word3, word4], "", "", node0, [])

        # Flattened constituencies are sorted after their leftmost word in the order they appear.

        self.assertEqual([
            word1,
            node0,
            node1,
            word2,
            node3,
            word3,
            node2,
            node4,
            word4,
            node5,
        ], self.matcher.flatten(syntax))

    def test_flatten_syntax_all_elements(self):
        word1 = self.mockWord(1, "w1", "N")
        word2 = self.mockWord(2, "w2", "N")

        dep1 = Dependency(word1, word1, "X")
        dep2 = Dependency(word1, word2, "Y")

        node0 = ConstituencyNode("0")
        node0.children = [word1]

        syntax = Syntax([word1, word2], "", "", node0, [dep1, dep2])

        # All ordering from individual components is maintained.
        # Words > Dependencies > Constituencies

        self.assertEqual([
            word1,
            dep1,
            node0,
            word2,
            dep2,
        ], self.matcher.flatten(syntax))

    def test_match_single_element(self):
        element = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        component1 = self.mockWord(1, "word", "N")
        component2 = self.mockWord(2, "word", "V")

        # A single component can be matched
        results = self.matcher.match([element], [component1, component2], None)

        self.assertEqual([SynMatcher.SynMatchResult([
            SynMatcher.TokenMatch(element, component1)
        ])], results)

    def test_match_single_element_multiple_times(self):
        element = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        component1 = self.mockWord(1, "word", "N")
        component2 = self.mockWord(2, "word", "V")
        component3 = self.mockWord(3, "word", "N")

        # A single component can be matched multiple times
        results = self.matcher.match([element], [component1, component2, component3], None)

        self.assertEqual([
            SynMatcher.SynMatchResult([
                SynMatcher.TokenMatch(element, component1)
            ]),
            SynMatcher.SynMatchResult([
                SynMatcher.TokenMatch(element, component3)
            ])
        ], results)

    def test_match_multiple_elements(self):
        element1 = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        element2 = SynStruc.TokenElement({"word"}, "V", dict(), None, False)
        component1 = self.mockWord(1, "word", "N")
        component2 = self.mockWord(2, "word", "J")
        component3 = self.mockWord(3, "word", "V")
        component4 = self.mockWord(4, "word", "N")

        # Multiple components can be matched; gapping is allowed
        results = self.matcher.match([element1, element2], [component1, component2, component3], None)

        self.assertEqual([SynMatcher.SynMatchResult([
            SynMatcher.TokenMatch(element1, component1),
            SynMatcher.TokenMatch(element2, component3),
        ])], results)

    def test_match_multiple_elements_multiple_times(self):
        element1 = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        element2 = SynStruc.TokenElement({"word"}, "V", dict(), None, False)
        component1 = self.mockWord(1, "word", "N")
        component2 = self.mockWord(2, "word", "N")
        component3 = self.mockWord(3, "word", "V")
        component4 = self.mockWord(4, "word", "N")

        # Multiple components can be matched; gapping is allowed
        results = self.matcher.match([element1, element2], [component1, component2, component3], None)

        self.assertEqual([
            SynMatcher.SynMatchResult([
                SynMatcher.TokenMatch(element1, component1),
                SynMatcher.TokenMatch(element2, component3),
            ]),
            SynMatcher.SynMatchResult([
                SynMatcher.TokenMatch(element1, component2),
                SynMatcher.TokenMatch(element2, component3),
            ])
        ], results)

    def test_run(self):
        # TODO: Test calls flatten, calls match, returns results
        fail()