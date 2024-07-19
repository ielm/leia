from leia.ontosem.syntax.results import ConstituencyNode, Dependency, LispParser, SenseMap, SynMap, Syntax, Word, WordCoreference
from unittest import TestCase
from unittest.mock import call, MagicMock, patch


class SyntaxTestCase(TestCase):

    @patch("leia.ontosem.syntax.results.Word.from_spacy")
    @patch("leia.ontosem.syntax.results.ConstituencyNode.parse_lisp_results")
    def test_from_spacy(self, mock_parse_lisp_results: MagicMock, mock_word_from_spacy: MagicMock):
        mock_parse_lisp_results.side_effect = lambda input, words: input
        mock_word_from_spacy.side_effect = lambda input, ner, coref: input

        word1 = MagicMock()
        word1.i = 0
        word1.dep_ = "test"
        word1.head = MagicMock()
        word1.head.i = 1

        word2 = MagicMock()
        word2.i = 1
        word2.dep_ = "ROOT"
        word2.head = MagicMock()
        word2.head.i = 1

        sentence = MagicMock()
        sentence.subtree = [word1, word2]
        sentence._ = MagicMock()
        sentence._.parse_string = "(TEST (PARSE (STRING)))"


        syntax = Syntax.from_spacy(sentence)
        self.assertEqual([word1, word2], syntax.words)
        self.assertEqual(["TEST", ["PARSE", ["STRING"]]], syntax.parse)
        self.assertEqual([Dependency(word2, word1, "test"), Dependency(word2, word2, "ROOT")], syntax.dependencies)

        mock_parse_lisp_results.assert_called_once_with(["TEST", ["PARSE", ["STRING"]]], [word1, word2])
        mock_word_from_spacy.assert_has_calls([call(word1, None, None), call(word2, None, None)])


class SynMapTestCase(TestCase):

    pass


class SenseMapTestCase(TestCase):

    pass


class WordTestCase(TestCase):

    pass


class WordCoreferenceTestCase(TestCase):

    pass


class ConstituencyNodeTestCase(TestCase):

    def test_parse_lisp_results(self):
        words = [
            Word(0, "word", [], "word", 0, 0, Word.Ner.NONE, [], {}),
            Word(1, "bird", [], "bird", 0, 0, Word.Ner.NONE, [], {}),
        ]

        parsed = ConstituencyNode.parse_lisp_results(["S", ["V", "Word"], ["N", "bird"]], words)

        self.assertEqual("S", parsed.label)
        self.assertEqual(2, len(parsed.children))

        self.assertEqual("V", parsed.children[0].label)
        self.assertEqual([words[0]], parsed.children[0].children)

        self.assertEqual("N", parsed.children[1].label)
        self.assertEqual([words[1]], parsed.children[1].children)

    def test_node_children(self):
        node0 = ConstituencyNode("0")
        node1 = ConstituencyNode("1")
        node2 = ConstituencyNode("2")

        word1 = Word(1, "word", [], "word", 0, 0, Word.Ner.NONE, [], {})
        word2 = Word(2, "word", [], "word", 0, 0, Word.Ner.NONE, [], {})

        node0.children = [node1, word1, node2, word2]

        self.assertEqual([node1, node2], node0.node_children())

    def test_leftmost_word(self):
        word1 = Word(1, "w1", [], "w1", 0, 0, Word.Ner.NONE, [], {})
        word2 = Word(2, "w2", [], "w2", 0, 0, Word.Ner.NONE, [], {})
        word3 = Word(3, "w3", [], "w3", 0, 0, Word.Ner.NONE, [], {})
        word4 = Word(4, "w4", [], "w4", 0, 0, Word.Ner.NONE, [], {})

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

        self.assertEqual(word1, node0.leftmost_word())
        self.assertEqual(word1, node1.leftmost_word())
        self.assertEqual(word3, node2.leftmost_word())
        self.assertEqual(word2, node3.leftmost_word())
        self.assertEqual(word3, node4.leftmost_word())
        self.assertEqual(word4, node5.leftmost_word())


class LispParserTestCase(TestCase):

    def test_lisp_to_list(self):
        lisp = "((XYZ ABC) ((DEF 1 2 3) BLAH))"
        results = LispParser.lisp_to_list(lisp)

        self.assertEqual([[
            ["XYZ", "ABC"],
            [
                ["DEF", "1", "2", "3"],
                "BLAH"
            ]
        ]], results)

    def test_list_key_to_value(self):
        lisp = [
            ["XYZ", "ABC"],
            ["DEF", ["1", "2", "3"], "BLAH"]
        ]

        self.assertEqual(["XYZ", "ABC"], LispParser.list_key_to_value(lisp, "XYZ"))
        self.assertEqual(["DEF", ["1", "2", "3"], "BLAH"], LispParser.list_key_to_value(lisp, "DEF"))