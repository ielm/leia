from leia.ontomem.lexicon import Sense, SynStruc
from leia.ontomem.memory import Memory
from leia.ontosem.analysis import Analysis, WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import (
    ConstituencyNode,
    Dependency,
    SenseMap,
    SynMap,
    Syntax,
    Word,
)
from leia.ontosem.syntax.synmapper import SynMatcher, SynMapper
from leia.tests.LEIATestCase import LEIATestCase
from typing import Iterable
from unittest.mock import call, MagicMock, patch


class SynMapperTestCase(LEIATestCase):

    def setUp(self):
        self.analysis = Analysis()
        self.m = self.analysis.config.memory()
        self.mapper = SynMapper(self.analysis)

    @patch("leia.ontosem.syntax.synmapper.SynMatcher.run")
    def test_build_sense_maps(self, mock_matcher: MagicMock):
        sense = Sense(
            self.m,
            "word-N1",
            contents=self.mockSense("word-N1", synstruc=[{"type": "root"}]),
        )
        word = self.mockWord(123, "word", "N")
        syntax = Syntax([word], "", "", ConstituencyNode(""), [])

        mock_matcher.return_value = [
            SynMatcher.SynMatchResult(
                [SynMatcher.RootMatch(sense.synstruc.elements[0], word)]
            )
        ]

        maps = list(self.mapper.build_sense_maps(syntax, word, sense))

        self.assertEqual([SenseMap(word, "word-N1", {"$VAR0": 123})], maps)

    @patch("leia.ontosem.syntax.synmapper.SynMatcher.run")
    def test_build_sense_maps_multiple_elements(self, mock_matcher: MagicMock):
        sense = Sense(
            self.m,
            "root-V1",
            contents=self.mockSense(
                "root-V1",
                synstruc=[
                    {"type": "root"},
                    {"type": "token", "lemma": [], "pos": "N", "morph": {}, "var": 1},
                ],
            ),
        )
        root = self.mockWord(1, "root", "V")
        noun = self.mockWord(2, "noun", "N")
        syntax = Syntax([root, noun], "", "", ConstituencyNode(""), [])

        mock_matcher.return_value = [
            SynMatcher.SynMatchResult(
                [
                    SynMatcher.RootMatch(sense.synstruc.elements[0], root),
                    SynMatcher.TokenMatch(sense.synstruc.elements[1], noun),
                ]
            ),
        ]

        maps = list(self.mapper.build_sense_maps(syntax, root, sense))

        self.assertEqual(
            [
                SenseMap(root, "root-V1", {"$VAR0": 1, "$VAR1": 2}),
            ],
            maps,
        )

    @patch("leia.ontosem.syntax.synmapper.SynMatcher.run")
    def test_build_sense_maps_multiple_matches(self, mock_matcher: MagicMock):
        sense = Sense(
            self.m,
            "root-V1",
            contents=self.mockSense(
                "root-V1",
                synstruc=[
                    {"type": "root"},
                    {"type": "token", "lemma": [], "pos": "N", "morph": {}, "var": 1},
                ],
            ),
        )
        root = self.mockWord(1, "root", "V")
        noun1 = self.mockWord(2, "noun", "N")
        noun2 = self.mockWord(3, "noun", "N")
        syntax = Syntax([root, noun1, noun2], "", "", ConstituencyNode(""), [])

        mock_matcher.return_value = [
            SynMatcher.SynMatchResult(
                [
                    SynMatcher.RootMatch(sense.synstruc.elements[0], root),
                    SynMatcher.TokenMatch(sense.synstruc.elements[1], noun1),
                ]
            ),
            SynMatcher.SynMatchResult(
                [
                    SynMatcher.RootMatch(sense.synstruc.elements[0], root),
                    SynMatcher.TokenMatch(sense.synstruc.elements[1], noun2),
                ]
            ),
        ]

        maps = list(self.mapper.build_sense_maps(syntax, root, sense))

        self.assertEqual(
            [
                SenseMap(root, "root-V1", {"$VAR0": 1, "$VAR1": 2}),
                SenseMap(root, "root-V1", {"$VAR0": 1, "$VAR1": 3}),
            ],
            maps,
        )

    def test_map_variable_no_variable(self):
        element = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        component = self.mockWord(123, "word", "N")
        match = SynMatcher.TokenMatch(element, component)

        # If an element in a match has no variable assigned to it, then no mapping can occur.  This is true for
        # all match / element types.
        self.assertEqual([], self.mapper.map_variables(match))

    def test_map_variable_no_matched_component(self):
        element = SynStruc.RootElement()
        match = SynMatcher.RootMatch(element, None)

        # If any match object has no component (meaning no match was found by the matcher), then no variable
        # can be mapped.  None is returned.  This is true for all match / element types.
        self.assertEqual([], self.mapper.map_variables(match))

    def test_map_variable_root_element(self):
        element = SynStruc.RootElement()
        component = self.mockWord(123, "word", "N")
        match = SynMatcher.RootMatch(element, component)

        # When a root element is matched, variable 0 is always used; the mapping is to the matched token.
        self.assertEqual([("$VAR0", 123)], self.mapper.map_variables(match))

    def test_map_variable_token_element(self):
        element = SynStruc.TokenElement({"word"}, "N", dict(), 3, False)
        component = self.mockWord(123, "word", "N")
        match = SynMatcher.TokenMatch(element, component)

        # When a token element is matched, the variable specified on the element is used; the mapping is to the matched token.
        self.assertEqual([("$VAR3", 123)], self.mapper.map_variables(match))

    def test_map_variable_dependency_element(self):
        element = SynStruc.DependencyElement("NSUBJ", None, None, 3, False)
        dependency = Dependency(
            self.mockWord(123, "word", "V"), self.mockWord(456, "word", "N"), "NSUBJ"
        )
        match = SynMatcher.DependencyMatch(element, dependency)

        # When a dependency element is matched, the variable specified on the element is used; the mapping is to the dependent token.
        self.assertEqual([("$VAR3", 456)], self.mapper.map_variables(match))

    def test_map_variable_constituency_element(self):
        element = SynStruc.ConstituencyElement("NP", [], 3, False)
        constituency = ConstituencyNode("NP")
        constituency.children = [
            self.mockWord(123, "word", "V"),
            self.mockWord(456, "word", "N"),
        ]
        match = SynMatcher.ConstituencyMatch(element, constituency, [])

        # When a constituency element is matched, the variable specified on the element is used; the mapping is to the leftmost token.
        self.assertEqual([("$VAR3", 123)], self.mapper.map_variables(match))

    def test_map_variable_constituency_element_with_children(self):
        element = SynStruc.ConstituencyElement(
            "VP",
            [
                SynStruc.ConstituencyElement(
                    "NP",
                    [SynStruc.TokenElement({"word"}, "N", dict(), 2, False)],
                    None,
                    False,
                )
            ],
            1,
            False,
        )

        vp = ConstituencyNode("VP")
        np = ConstituencyNode("NP")
        token1 = self.mockWord(123, "word", "N")
        token2 = self.mockWord(456, "word", "N")

        vp.children = [token1, np]
        np.children = [token2]

        match = SynMatcher.ConstituencyMatch(
            element,
            vp,
            [SynMatcher.TokenMatch(element.children[0].children[0], token2)],
        )

        # When a constituency element is matched, if it has children (recursively) that have variables specified, those
        # corresponding elements must be mapped to each of their leftmost tokens (or themselves, if they are a token).
        # At present, constituency child matching (in the matcher) requires a perfect match from parent to child (no
        # skipping of levels).  That is held true for variable mapping as well.
        self.assertEqual(
            [
                ("$VAR1", 123),
                ("$VAR2", 456),
            ],
            self.mapper.map_variables(match),
        )

    def test_map_variable_constituency_element_with_children_no_top_variable(self):
        # Identical to test_map_variable_constituency_element_with_children, however the top element has no variable.
        # This verifies that recursive variables are found even if the top one would normally be skipped for having
        # a null variable.

        element = SynStruc.ConstituencyElement(
            "VP",
            [
                SynStruc.ConstituencyElement(
                    "NP",
                    [SynStruc.TokenElement({"word"}, "N", dict(), 2, False)],
                    None,
                    False,
                )
            ],
            None,
            False,
        )

        vp = ConstituencyNode("VP")
        np = ConstituencyNode("NP")
        token1 = self.mockWord(123, "word", "N")
        token2 = self.mockWord(456, "word", "N")

        vp.children = [token1, np]
        np.children = [token2]

        match = SynMatcher.ConstituencyMatch(
            element,
            vp,
            [SynMatcher.TokenMatch(element.children[0].children[0], token2)],
        )

        self.assertEqual(
            [
                ("$VAR2", 456),
            ],
            self.mapper.map_variables(match),
        )

    def test_run(self):
        # First, define some words that will be part of the input
        word0 = self.mockWord(0, "the", "ART")
        word1 = self.mockWord(1, "man", "N")

        # Next, the WMLexicon should be populated with senses for each word (possibly transformed) prior to syn-mapping,
        # so add some now.
        w0s1 = Sense(self.m, "the-art1", contents=self.mockSense("the-art1"))
        w0s2 = Sense(self.m, "the-art2", contents=self.mockSense("the-art2"))
        w1s1 = Sense(self.m, "man-n1", contents=self.mockSense("man-n1"))
        w1s2 = Sense(self.m, "man-n2", contents=self.mockSense("man-n2"))

        self.mapper.analysis.lexicon.add_sense(word0, w0s1)
        self.mapper.analysis.lexicon.add_sense(word0, w0s2)
        self.mapper.analysis.lexicon.add_sense(word1, w1s1)
        self.mapper.analysis.lexicon.add_sense(word1, w1s2)

        # Build the syntax input; only the words matter for this test, as we'll be mocking the results of the matcher.
        syntax = Syntax([word0, word1], "", "", ConstituencyNode(""), [])

        # Mock the output of build_sense_maps; each call should return an iterable of SenseMap objects.  We'll return
        # a different one for each expected call.
        sm_w0s1 = SenseMap(word0, w0s1.id, {})
        sm_w0s2 = SenseMap(word0, w0s2.id, {})
        sm_w1s1 = SenseMap(word1, w1s1.id, {})
        sm_w1s2a = SenseMap(word1, w1s2.id, {})
        sm_w1s2b = SenseMap(word1, w1s2.id, {})

        def _mock_build_sense_maps(
            syntax: Syntax, word: Word, sense: Sense
        ) -> Iterable[SenseMap]:
            return {
                word0: {w0s1.id: iter([sm_w0s1]), w0s2.id: iter([sm_w0s2])},
                word1: {w1s1.id: iter([sm_w1s1]), w1s2.id: iter([sm_w1s2a, sm_w1s2b])},
            }[word][sense.id]

        self.mapper.build_sense_maps = MagicMock(side_effect=_mock_build_sense_maps)

        # Now run the mapper.  We can test the expected synmap, as well verifying that build_sense_maps was
        # called properly for each word / sense pair.
        synmap = self.mapper.run(syntax)

        expected = SynMap(
            [
                [sm_w0s1, sm_w0s2],  # Word 0 has two possible mappings
                [
                    sm_w1s1,
                    sm_w1s2a,
                    sm_w1s2b,
                ],  # Word 1 has three possible mappings (2 of which are the same sense)
            ]
        )
        self.assertEqual(expected, synmap)

        self.mapper.build_sense_maps.assert_has_calls(
            [
                call(syntax, word0, w0s1),
                call(syntax, word0, w0s2),
                call(syntax, word1, w1s1),
                call(syntax, word1, w1s2),
            ]
        )


class SynMatcherTestCase(LEIATestCase):

    def setUp(self):
        self.analysis = Analysis()
        self.m = self.analysis.config.memory()
        self.matcher = SynMatcher(self.analysis)

    def test_attempt_element_match(self):
        # This generic function checks to see if a syn-struc element and any syntax component are a match.
        # If their core types are not compatible, the result is false.  Otherwise, the corresponding attempt_x_match
        # function is called, and its result is returned.

        # Incompatible types do not even call the correct function; they just return false.
        self.matcher.attempt_root_match = MagicMock(return_value="a")
        self.matcher.attempt_token_match = MagicMock(return_value="b")
        self.matcher.attempt_dependency_match = MagicMock(return_value="c")
        self.matcher.attempt_constituency_match = MagicMock(return_value="d")

        self.assertIsNone(
            self.matcher.attempt_element_match(SynStruc.RootElement(), None, None)
        )
        self.matcher.attempt_root_match.assert_not_called()

        self.assertIsNone(
            self.matcher.attempt_element_match(
                SynStruc.TokenElement(set(), None, dict(), None, False), None, None
            )
        )
        self.matcher.attempt_token_match.assert_not_called()

        self.assertIsNone(
            self.matcher.attempt_element_match(
                SynStruc.DependencyElement("", None, None, None, False), None, None
            )
        )
        self.matcher.attempt_dependency_match.assert_not_called()

        self.assertIsNone(
            self.matcher.attempt_element_match(
                SynStruc.ConstituencyElement("", [], None, False), None, None
            )
        )
        self.matcher.attempt_constituency_match.assert_not_called()

        # Compatible types call the correct function and return its results.
        kwargs = {"root": None}

        args = [SynStruc.RootElement(), self.mockWord(0, "X", "N")]
        self.assertEqual("a", self.matcher.attempt_element_match(*args, **kwargs))
        self.matcher.attempt_root_match.assert_called_once_with(*args, **kwargs)

        args = [
            SynStruc.TokenElement(set(), None, dict(), None, False),
            self.mockWord(0, "X", "N"),
        ]
        self.assertEqual("b", self.matcher.attempt_element_match(*args, **kwargs))
        self.matcher.attempt_token_match.assert_called_once_with(*args, **kwargs)

        args = [
            SynStruc.DependencyElement("", None, None, None, False),
            Dependency(self.mockWord(1, "A", "N"), self.mockWord(2, "B", "N"), "Z"),
        ]
        self.assertEqual("c", self.matcher.attempt_element_match(*args, **kwargs))
        self.matcher.attempt_dependency_match.assert_called_once_with(*args, **kwargs)

        args = [
            SynStruc.ConstituencyElement("", [], None, False),
            ConstituencyNode("NP"),
        ]
        self.assertEqual("d", self.matcher.attempt_element_match(*args, **kwargs))
        self.matcher.attempt_constituency_match.assert_called_once_with(*args, **kwargs)

    def test_attempt_root_match(self):
        root = self.mockWord(0, "root", "N")
        other = self.mockWord(1, "other", "N")

        # attempt_root_match is a trivial comparison of the specified input root (if any) against any given token;
        # it primarily exists for consistency and as a sanity check
        element = SynStruc.RootElement()

        self.assertIsNone(self.matcher.attempt_root_match(element, root, None))
        self.assertIsNone(self.matcher.attempt_root_match(element, root, other))
        self.assertEqual(
            SynMatcher.RootMatch(element, root),
            self.matcher.attempt_root_match(element, root, root),
        )

    def test_attempt_token_match_single_lemma(self):
        word = self.mockWord(0, "word", "N")

        # An empty lemma cannot be matched
        element = SynStruc.TokenElement(set(), None, dict(), None, False)
        self.assertIsNone(self.matcher.attempt_token_match(element, word, None))

        # An incorrect lemma is not a match
        element = SynStruc.TokenElement({"other"}, None, dict(), None, False)
        self.assertIsNone(self.matcher.attempt_token_match(element, word, None))

        # A correct lemma is a match
        element = SynStruc.TokenElement({"word"}, None, dict(), None, False)
        self.assertEqual(
            SynMatcher.TokenMatch(element, word),
            self.matcher.attempt_token_match(element, word, None),
        )

    def test_attempt_token_match_multiple_lemmas(self):
        word = self.mockWord(0, "word", "N")

        # At least one lemma must be a match
        element = SynStruc.TokenElement({"other1", "other2"}, None, dict(), None, False)
        self.assertIsNone(self.matcher.attempt_token_match(element, word, None))

        element = SynStruc.TokenElement(
            {"word", "other1", "other2"}, None, dict(), None, False
        )
        self.assertEqual(
            SynMatcher.TokenMatch(element, word),
            self.matcher.attempt_token_match(element, word, None),
        )

    def test_attempt_token_match_pos(self):
        word = self.mockWord(0, "word", "N")

        # An null POS is cannot be matched
        element = SynStruc.TokenElement(set(), None, dict(), None, False)
        self.assertIsNone(self.matcher.attempt_token_match(element, word, None))

        # An incorrect POS is not a match
        element = SynStruc.TokenElement({}, "V", dict(), None, False)
        self.assertIsNone(self.matcher.attempt_token_match(element, word, None))

        # A correct POS is a match
        element = SynStruc.TokenElement({}, "N", dict(), None, False)
        self.assertEqual(
            SynMatcher.TokenMatch(element, word),
            self.matcher.attempt_token_match(element, word, None),
        )

        # An ancestor POS is a match
        element = SynStruc.TokenElement({}, "ANCESTOR-N", dict(), None, False)
        self.m.parts_of_speech.get("N").parents = [
            self.m.parts_of_speech.get("ANCESTOR-N")
        ]
        self.assertEqual(
            SynMatcher.TokenMatch(element, word),
            self.matcher.attempt_token_match(element, word, None),
        )

    def test_attempt_token_match_morphology(self):
        word = self.mockWord(0, "word", "N", morphology={"A": 1, "B": 2})

        # An empty morphology is a match
        element = SynStruc.TokenElement({"word"}, None, dict(), None, False)
        self.assertEqual(
            SynMatcher.TokenMatch(element, word),
            self.matcher.attempt_token_match(element, word, None),
        )

        # A partially matching morphology is a match
        element = SynStruc.TokenElement({"word"}, None, {"A": 1}, None, False)
        self.assertEqual(
            SynMatcher.TokenMatch(element, word),
            self.matcher.attempt_token_match(element, word, None),
        )

        # A fully matching morphology is a match
        element = SynStruc.TokenElement({"word"}, None, {"A": 1, "B": 2}, None, False)
        self.assertEqual(
            SynMatcher.TokenMatch(element, word),
            self.matcher.attempt_token_match(element, word, None),
        )

        # Any contradiction in the element is not a match
        element = SynStruc.TokenElement(
            {"word"}, None, {"A": 1, "B": 2, "C": 3}, None, False
        )
        self.assertIsNone(self.matcher.attempt_token_match(element, word, None))

        element = SynStruc.TokenElement({"word"}, None, {"A": 1, "B": 3}, None, False)
        self.assertIsNone(self.matcher.attempt_token_match(element, word, None))

    def test_attempt_token_match_multiple_criteria(self):
        word = self.mockWord(0, "word", "N", morphology={"A": 1, "B": 2})

        element = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        self.assertEqual(
            SynMatcher.TokenMatch(element, word),
            self.matcher.attempt_token_match(element, word, None),
        )

        element = SynStruc.TokenElement({"word", "other"}, "N", {"A": 1}, None, False)
        self.assertEqual(
            SynMatcher.TokenMatch(element, word),
            self.matcher.attempt_token_match(element, word, None),
        )

        element = SynStruc.TokenElement({"word", "other"}, "V", {"A": 1}, None, False)
        self.assertIsNone(self.matcher.attempt_token_match(element, word, None))

    def test_attempt_dependency_match_no_root(self):
        gov = self.mockWord(0, "gov", "N")
        dep = self.mockWord(1, "dep", "N")

        dep1 = Dependency(gov, dep, "NSUBJ")
        dep2 = Dependency(dep, gov, "NSUBJ")
        dep3 = Dependency(gov, dep, "DOBJ")

        # The only part of the element to match is the type; gov/dep in the element are for variable mapping, and are
        # not used here in any way.
        element = SynStruc.DependencyElement("NSUBJ", None, None, None, False)

        self.assertEqual(
            SynMatcher.DependencyMatch(element, dep1),
            self.matcher.attempt_dependency_match(element, dep1, None),
        )
        self.assertEqual(
            SynMatcher.DependencyMatch(element, dep2),
            self.matcher.attempt_dependency_match(element, dep2, None),
        )
        self.assertIsNone(self.matcher.attempt_dependency_match(element, dep3, None))

    def test_attempt_dependency_match_with_root(self):
        gov = self.mockWord(0, "gov", "N")
        dep = self.mockWord(1, "dep", "N")

        dep1 = Dependency(gov, dep, "NSUBJ")
        dep2 = Dependency(dep, gov, "NSUBJ")
        dep3 = Dependency(gov, dep, "DOBJ")

        element = SynStruc.DependencyElement("NSUBJ", None, None, None, False)

        # In order to match with a specified root, the root must be the governor.
        self.assertEqual(
            SynMatcher.DependencyMatch(element, dep1),
            self.matcher.attempt_dependency_match(element, dep1, gov),
        )
        self.assertIsNone(self.matcher.attempt_dependency_match(element, dep2, gov))
        self.assertIsNone(self.matcher.attempt_dependency_match(element, dep3, gov))

    def test_attempt_constituency_match_no_children(self):
        node1 = ConstituencyNode("NP")
        node2 = ConstituencyNode("VP")

        element = SynStruc.ConstituencyElement("NP", [], None, False)

        # The node type must always be a match, regardless of any children
        self.assertEqual(
            SynMatcher.ConstituencyMatch(element, node1, []),
            self.matcher.attempt_constituency_match(element, node1, None),
        )
        self.assertIsNone(self.matcher.attempt_constituency_match(element, node2, None))

    def test_attempt_constituency_match_with_constituency_children(self):
        node1 = ConstituencyNode("NP")
        node1.children = [ConstituencyNode("X")]

        node2 = ConstituencyNode("NP")
        node2.children = [ConstituencyNode("Y")]

        element = SynStruc.ConstituencyElement(
            "NP", [SynStruc.ConstituencyElement("X", [], None, False)], None, False
        )

        # The children must match as well as the outer type.  Children can be other constituency nodes.
        self.assertEqual(
            SynMatcher.ConstituencyMatch(
                element,
                node1,
                [
                    SynMatcher.ConstituencyMatch(
                        element.children[0], node1.children[0], []
                    )
                ],
            ),
            self.matcher.attempt_constituency_match(element, node1, None),
        )
        self.assertIsNone(self.matcher.attempt_constituency_match(element, node2, None))

    def test_attempt_constituency_match_with_token_children(self):
        node1 = ConstituencyNode("NP")
        node1.children = [self.mockWord(0, "a", "N")]

        node2 = ConstituencyNode("NP")
        node2.children = [self.mockWord(0, "b", "N")]

        element = SynStruc.ConstituencyElement(
            "NP", [SynStruc.TokenElement({"a"}, "N", dict(), None, False)], None, False
        )

        # The children must match as well as the outer type.  Children can be words.
        self.assertEqual(
            SynMatcher.ConstituencyMatch(
                element,
                node1,
                [SynMatcher.TokenMatch(element.children[0], node1.children[0])],
            ),
            self.matcher.attempt_constituency_match(element, node1, None),
        )
        self.assertIsNone(self.matcher.attempt_constituency_match(element, node2, None))

    def test_attempt_constituency_match_with_multiple_children(self):
        node1 = ConstituencyNode("NP")
        node1.children = [ConstituencyNode("X"), ConstituencyNode("Y")]

        node2 = ConstituencyNode("NP")
        node2.children = [ConstituencyNode("X")]

        node3 = ConstituencyNode("NP")
        node3.children = [ConstituencyNode("Y"), ConstituencyNode("X")]

        element = SynStruc.ConstituencyElement(
            "NP",
            [
                SynStruc.ConstituencyElement("X", [], None, False),
                SynStruc.ConstituencyElement("Y", [], None, False),
            ],
            None,
            False,
        )

        # Multiple children may be required; their ordering matters..
        self.assertEqual(
            SynMatcher.ConstituencyMatch(
                element,
                node1,
                [
                    SynMatcher.ConstituencyMatch(
                        element.children[0], node1.children[0], []
                    ),
                    SynMatcher.ConstituencyMatch(
                        element.children[1], node1.children[1], []
                    ),
                ],
            ),
            self.matcher.attempt_constituency_match(element, node1, None),
        )
        self.assertIsNone(self.matcher.attempt_constituency_match(element, node2, None))
        self.assertIsNone(self.matcher.attempt_constituency_match(element, node3, None))

    def test_attempt_constituency_match_recursive_children(self):
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

        element = SynStruc.ConstituencyElement(
            "NP",
            [
                SynStruc.ConstituencyElement(
                    "A",
                    [SynStruc.ConstituencyElement("C", [], None, False)],
                    None,
                    False,
                ),
                SynStruc.ConstituencyElement("B", [], None, False),
            ],
            None,
            False,
        )

        # The child structure is fully recursive.
        self.assertEqual(
            SynMatcher.ConstituencyMatch(
                element,
                node1,
                [
                    SynMatcher.ConstituencyMatch(
                        element.children[0],
                        node1a,
                        [
                            SynMatcher.ConstituencyMatch(
                                element.children[0].children[0], node1c, []
                            )
                        ],
                    ),
                    SynMatcher.ConstituencyMatch(element.children[1], node1b, []),
                ],
            ),
            self.matcher.attempt_constituency_match(element, node1, None),
        )
        self.assertIsNone(self.matcher.attempt_constituency_match(element, node2, None))

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

        syntax = Syntax(
            [word1, word2, word3], "", "", ConstituencyNode(""), [dep1, dep2, dep3]
        )

        # Flattened dependencies are sorted after their dependent words in the order they are entered.
        # The constituency node should be skipped as it has no inner token (it is essentially empty).

        self.assertEqual(
            [word1, dep1, dep2, word2, dep3, word3], self.matcher.flatten(syntax)
        )

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

        self.assertEqual(
            [
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
            ],
            self.matcher.flatten(syntax),
        )

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

        self.assertEqual(
            [
                word1,
                dep1,
                node0,
                word2,
                dep2,
            ],
            self.matcher.flatten(syntax),
        )

    def test_match_single_element(self):
        element = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        component1 = self.mockWord(1, "word", "N")
        component2 = self.mockWord(2, "word", "V")

        # A single component can be matched
        results = self.matcher.match([element], [component1, component2], None)

        self.assertEqual(
            [SynMatcher.SynMatchResult([SynMatcher.TokenMatch(element, component1)])],
            results,
        )

    def test_match_single_element_multiple_times(self):
        element = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        component1 = self.mockWord(1, "word", "N")
        component2 = self.mockWord(2, "word", "V")
        component3 = self.mockWord(3, "word", "N")

        # A single component can be matched multiple times
        results = self.matcher.match(
            [element], [component1, component2, component3], None
        )

        self.assertEqual(
            [
                SynMatcher.SynMatchResult([SynMatcher.TokenMatch(element, component1)]),
                SynMatcher.SynMatchResult([SynMatcher.TokenMatch(element, component3)]),
            ],
            results,
        )

    def test_match_multiple_elements(self):
        element1 = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        element2 = SynStruc.TokenElement({"word"}, "V", dict(), None, False)
        component1 = self.mockWord(1, "word", "N")
        component2 = self.mockWord(2, "word", "J")
        component3 = self.mockWord(3, "word", "V")
        component4 = self.mockWord(4, "word", "N")

        # Multiple components can be matched; gapping is allowed
        results = self.matcher.match(
            [element1, element2], [component1, component2, component3, component4], None
        )

        self.assertEqual(
            [
                SynMatcher.SynMatchResult(
                    [
                        SynMatcher.TokenMatch(element1, component1),
                        SynMatcher.TokenMatch(element2, component3),
                    ]
                )
            ],
            results,
        )

    def test_match_multiple_elements_multiple_times(self):
        element1 = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        element2 = SynStruc.TokenElement({"word"}, "V", dict(), None, False)
        component1 = self.mockWord(1, "word", "N")
        component2 = self.mockWord(2, "word", "N")
        component3 = self.mockWord(3, "word", "V")
        component4 = self.mockWord(4, "word", "N")

        # Multiple components can be matched; gapping is allowed
        results = self.matcher.match(
            [element1, element2], [component1, component2, component3, component4], None
        )

        self.assertEqual(
            [
                SynMatcher.SynMatchResult(
                    [
                        SynMatcher.TokenMatch(element1, component1),
                        SynMatcher.TokenMatch(element2, component3),
                    ]
                ),
                SynMatcher.SynMatchResult(
                    [
                        SynMatcher.TokenMatch(element1, component2),
                        SynMatcher.TokenMatch(element2, component3),
                    ]
                ),
            ],
            results,
        )

    def test_match_optional_elements(self):
        element1 = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        element2 = SynStruc.TokenElement({"word"}, "V", dict(), None, True)
        component1 = self.mockWord(1, "word", "N")
        component2 = self.mockWord(2, "word", "V")
        component3 = self.mockWord(3, "word", "N")

        # Optional elements can always be skipped in the match; they will be returned in the result with a null
        # value in the component field.  Actual matches will be returned as well.
        results = self.matcher.match(
            [element1, element2], [component1, component2, component3], None
        )

        self.assertEqual(
            [
                SynMatcher.SynMatchResult(
                    [
                        SynMatcher.TokenMatch(element1, component1),
                        SynMatcher.TokenMatch(element2, component2),
                    ]
                ),
                SynMatcher.SynMatchResult(
                    [
                        SynMatcher.TokenMatch(element1, component1),
                        SynMatcher.TokenMatch(element2, None),
                    ]
                ),
                SynMatcher.SynMatchResult(
                    [
                        SynMatcher.TokenMatch(element1, component3),
                        SynMatcher.TokenMatch(element2, None),
                    ]
                ),
            ],
            results,
        )

    def test_match_remaining_elements(self):
        # If any element, including the first, has no matches, the remaining elements are still attempted to
        # be matched.

        element1 = SynStruc.TokenElement({"word"}, "N", dict(), None, False)
        element2 = SynStruc.TokenElement({"word"}, "V", dict(), None, False)

        component1 = self.mockWord(1, "word", "ADJ")
        component2 = self.mockWord(2, "word", "V")
        component3 = self.mockWord(3, "word", "ADJ")

        results = self.matcher.match(
            [element1, element2], [component1, component2, component3], None
        )

        self.assertEqual(
            [SynMatcher.SynMatchResult([SynMatcher.TokenMatch(element2, component2)])],
            results,
        )

    def test_run(self):
        flattened = ["MOCK", "FLATTENED", "SYNTAX"]
        expected = ["MOCK", "EXPECTED", "RESULTS"]

        syntax = Syntax([], "", "", ConstituencyNode(""), [])
        synstruc = SynStruc()
        synstruc.elements = [
            SynStruc.RootElement(),
            SynStruc.TokenElement({"A", "B"}, "N", {"x": 1}, 123, False),
        ]
        root = self.mockWord(0, "ROOT", "R")

        self.matcher.flatten = MagicMock(return_value=flattened)
        self.matcher.match = MagicMock(return_value=expected)

        results = self.matcher.run(syntax, synstruc, root=root)
        self.assertEqual(expected, results)

        self.matcher.flatten.assert_called_once_with(syntax)
        self.matcher.match.assert_called_once_with(synstruc.elements, flattened, root)


class SynMatchResultTestCase(LEIATestCase):

    def test_match_for_var(self):
        result = SynMatcher.SynMatchResult([])
        self.assertIsNone(result.match_for_var(0))
        self.assertIsNone(result.match_for_var(1))

        result.matches = [
            SynMatcher.TokenMatch(
                SynStruc.TokenElement({"A"}, "N", dict(), 0, False),
                self.mockWord(0, "A", "N"),
            )
        ]

        self.assertEqual(result.matches[0], result.match_for_var(0))
        self.assertIsNone(result.match_for_var(1))

    def test_match_for_var_inside_constituency(self):
        word1 = self.mockWord(1, "A", "N")
        word2 = self.mockWord(2, "B", "N")

        element = SynStruc.ConstituencyElement(
            "NP",
            [
                SynStruc.TokenElement({"A"}, "N", dict(), 0, False),
                SynStruc.TokenElement({"B"}, "N", dict(), None, False),
            ],
            None,
            False,
        )

        node = ConstituencyNode("NP")
        node.children = [word1, word2]

        result = SynMatcher.SynMatchResult(
            [
                SynMatcher.ConstituencyMatch(
                    element,
                    node,
                    [
                        SynMatcher.TokenMatch(element.children[0], word1),
                        SynMatcher.TokenMatch(element.children[1], word2),
                    ],
                )
            ]
        )

        self.assertEqual(result.matches[0].children[0], result.match_for_var(0))
        self.assertIsNone(result.match_for_var(1))

    def test_element_for_var(self):
        # element_for_var just wraps match_for_var and pulls out the element

        result = SynMatcher.SynMatchResult([])
        result.match_for_var = MagicMock(return_value=None)

        self.assertIsNone(result.element_for_var(0))
        result.match_for_var.assert_called_once_with(0)

        mocked_match = MagicMock()
        mocked_match.element = 123
        result.match_for_var = MagicMock(return_value=mocked_match)

        self.assertEqual(123, result.element_for_var(0))
        result.match_for_var.assert_called_once_with(0)

    def test_component_for_var(self):
        # component_for_var just wraps match_for_var and pulls out the component

        result = SynMatcher.SynMatchResult([])
        result.match_for_var = MagicMock(return_value=None)

        self.assertIsNone(result.component_for_var(0))
        result.match_for_var.assert_called_once_with(0)

        mocked_match = MagicMock()
        mocked_match.component = 123
        result.match_for_var = MagicMock(return_value=mocked_match)

        self.assertEqual(123, result.component_for_var(0))
        result.match_for_var.assert_called_once_with(0)
