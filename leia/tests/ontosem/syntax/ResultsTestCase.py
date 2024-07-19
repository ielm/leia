from leia.ontosem.syntax.results import LispParser, SenseMap, SynMap, Syntax, Word, WordCoreference
from unittest import TestCase
from unittest.mock import call, MagicMock, patch


class SyntaxTestCase(TestCase):

    @patch("leia.ontosem.syntax.results.Syntax.parse_lisp_results")
    def test_from_lisp_string(self, mock_parse_syntax: MagicMock):
        mock_parse_syntax.side_effect = lambda input: input

        lisp = "(mock-syntax-1 mock-syntax-2)"
        output = Syntax.from_lisp_string(lisp)

        self.assertEqual([
            "mock-syntax-1",
            "mock-syntax-2"
        ], output)

        mock_parse_syntax.assert_has_calls([call("mock-syntax-1"), call("mock-syntax-2")])

    @patch("leia.ontosem.syntax.results.Word.parse_lisp_results")
    @patch("leia.ontosem.syntax.results.SynMap.parse_lisp_results")
    @patch("leia.ontosem.syntax.results.Sense.parse_lisp")
    def test_parse_lisp_results(self, mock_parse_sense: MagicMock, mock_parse_synmap: MagicMock, mock_parse_word: MagicMock):
        mock_parse_sense.side_effect = lambda input: input
        mock_parse_synmap.side_effect = lambda input, words: input
        mock_parse_word.side_effect = lambda input: input

        word1 = ["Some mock word1 info here."]
        word2 = ["Some mock word2 info here."]

        basic_deps = [["ROOT", "-1", "0"], ["ART", "2", "1"]]
        enhanced_deps = [["ROOT", "-1", "0"], ["ART", "2", "1"]]
        parse = ["ROOT", ["S", ["VP", ["V", "Word1", "0"]]]]
        synmap = ["Some mock synmap info here."]

        sense1 = ["Some mock lex sense1 info here."]
        sense2 = ["Some mock lex sense2 info here."]

        lisp = [
            [
                "STANFORD",
                [
                    ["WORDS", word1, word2],
                    ["BASICDEPS", basic_deps],
                    ["ENHANCEDDEPS", enhanced_deps],
                    ["ORIGINALSENTENCE", "Word1 word2."],
                    ["SENTENCE", "Word1 word2."],
                    ["PARSE", parse],
                ]
            ],
            ["SYNMAP", synmap],
            ["LEX-SENSES", [sense1, sense2]]
        ]

        syntax = Syntax.parse_lisp_results(lisp)

        mock_parse_sense.assert_has_calls([call(sense1), call(sense2)])
        mock_parse_synmap.assert_called_once_with(synmap, [word1, word2])
        mock_parse_word.assert_has_calls([call(word1), call(word2)])

        self.assertEqual([word1, word2], syntax.words)
        self.assertEqual(basic_deps, syntax.basic_deps)
        self.assertEqual(enhanced_deps, syntax.enhanced_deps)
        self.assertEqual("Word1 word2.", syntax.original_sentence)
        self.assertEqual("Word1 word2.", syntax.sentence)
        self.assertEqual(parse, syntax.parse)
        self.assertEqual(synmap, syntax.synmap)
        self.assertEqual([sense1, sense2], syntax.lex_senses)

    @patch("leia.ontosem.syntax.results.Word.parse_lisp_results")
    @patch("leia.ontosem.syntax.results.SynMap.parse_lisp_results")
    def test_parse_lisp_results_nil_lex_senses(self, mock_parse_synmap: MagicMock, mock_parse_word: MagicMock):
        mock_parse_synmap.side_effect = lambda input, words: input
        mock_parse_word.side_effect = lambda input: input

        word1 = ["Some mock word1 info here."]
        word2 = ["Some mock word2 info here."]

        basic_deps = [["ROOT", "-1", "0"], ["ART", "2", "1"]]
        enhanced_deps = [["ROOT", "-1", "0"], ["ART", "2", "1"]]
        parse = ["ROOT", ["S", ["VP", ["V", "Word1", "0"]]]]
        synmap = ["Some mock synmap info here."]

        lisp = [
            [
                "STANFORD",
                [
                    ["WORDS", word1, word2],
                    ["BASICDEPS", basic_deps],
                    ["ENHANCEDDEPS", enhanced_deps],
                    ["ORIGINALSENTENCE", "Word1 word2."],
                    ["SENTENCE", "Word1 word2."],
                    ["PARSE", parse],
                ]
            ],
            ["SYNMAP", synmap],
            ["LEX-SENSES", "NIL"]
        ]

        syntax = Syntax.parse_lisp_results(lisp)

        mock_parse_synmap.assert_called_once_with(synmap, [word1, word2])
        mock_parse_word.assert_has_calls([call(word1), call(word2)])

        self.assertEqual([word1, word2], syntax.words)
        self.assertEqual(basic_deps, syntax.basic_deps)
        self.assertEqual(enhanced_deps, syntax.enhanced_deps)
        self.assertEqual("Word1 word2.", syntax.original_sentence)
        self.assertEqual("Word1 word2.", syntax.sentence)
        self.assertEqual(parse, syntax.parse)
        self.assertEqual(synmap, syntax.synmap)
        self.assertEqual([], syntax.lex_senses)


class SynMapTestCase(TestCase):

    def test_parse_lisp_results(self):
        lisp = [
            [
                ["THE-ART1", [["$VAR0", "0"], ["$VAR1", "1"]], ["PREFERENCE", "4"]]
            ],
            [
                ["CACHE-N1", [["$VAR0", "1"]], ["PREFERENCE", "3"]],
                ["STORE-N1", [["$VAR0", "1"]], ["PREFERENCE", "2"]]
            ]
        ]

        w1 = Word.basic(1)
        w2 = Word.basic(2)

        synmap = SynMap.parse_lisp_results(lisp, [w1, w2])
        self.assertEqual(2, len(synmap.words))
        self.assertEqual(1, len(synmap.words[0]))
        self.assertEqual(2, len(synmap.words[1]))
        self.assertEqual([SenseMap(w1, "THE-ART1", {"$VAR0": 0, "$VAR1": 1}, 4.0)], synmap.words[0])
        self.assertEqual([
            SenseMap(w2, "CACHE-N1", {"$VAR0": 1}, 3.0),
            SenseMap(w2, "STORE-N1", {"$VAR0": 1}, 2.0)
        ], synmap.words[1])


class SenseMapTestCase(TestCase):

    def test_parse_lisp_results(self):
        lisp = ["THE-ART1", [["$VAR0", "0"], ["$VAR1", "NIL"]], ["PREFERENCE", "4"]]
        word = Word.basic(0)
        sense_map = SenseMap.parse_lisp_results(lisp, word)

        self.assertEqual(word, sense_map.word)
        self.assertEqual("THE-ART1", sense_map.sense)
        self.assertEqual(2, len(sense_map.bindings))
        self.assertEqual(0, sense_map.bindings["$VAR0"])
        self.assertEqual(None, sense_map.bindings["$VAR1"])
        self.assertEqual(4.0, sense_map.preference)

    def test_parse_lisp_results_with_quotes_on_sense_name(self):
        lisp = ['"THE-ART1"', [["$VAR0", "0"], ["$VAR1", "NIL"]], ["PREFERENCE", "4"]]
        word = Word.basic(0)
        sense_map = SenseMap.parse_lisp_results(lisp, word)

        self.assertEqual(word, sense_map.word)
        self.assertEqual("THE-ART1", sense_map.sense)
        self.assertEqual(2, len(sense_map.bindings))
        self.assertEqual(0, sense_map.bindings["$VAR0"])
        self.assertEqual(None, sense_map.bindings["$VAR1"])
        self.assertEqual(4.0, sense_map.preference)


class WordTestCase(TestCase):

    def test_parse_lisp_results(self):
        lisp = [["ID", "0"], ["COREF", "NIL"], ["LEMMA", "KICK"], ["NER", "O"], ["OFFSET", ["0", "4"]], ["POS", ["V", "INFINITIVE"]], ["TOKEN", "Kick"]]
        word = Word.parse_lisp_results(lisp)

        self.assertEqual(0, word.index)
        self.assertEqual([], word.coref)
        self.assertEqual("KICK", word.lemma)
        self.assertEqual(Word.Ner.NONE, word.ner)
        self.assertEqual(0, word.char_start)
        self.assertEqual(4, word.char_end)
        self.assertEqual(["V", "INFINITIVE"], word.pos)
        self.assertEqual("Kick", word.token)

    def test_parse_lisp_results_with_coref(self):
        lisp = [
            ["ID", "0"],
            ["COREF", [
                ["", "", "", "1.0", "", ["0", "0"], "", ""],
                ["", "", "", "0.7", "", ["3", "2"], "", ""]
            ]],
            ["LEMMA", "KICK"],
            ["NER", "O"],
            ["OFFSET", ["0", "4"]],
            ["POS", ["V", "INFINITIVE"]],
            ["TOKEN", "Kick"]
        ]

        word = Word.parse_lisp_results(lisp)

        self.assertEqual([
            WordCoreference(0, 0, 1.0),
            WordCoreference(3, 2, 0.7),
        ], word.coref)


class WordCoreferenceTestCase(TestCase):

    def test_parse_lisp_results(self):
        lisp = ["", "", "", "0.5", "", ["2", "1"], "", ""]
        coreference = WordCoreference.parse_lisp_results(lisp)

        self.assertEqual(2, coreference.sentence)
        self.assertEqual(1, coreference.word)
        self.assertEqual(0.5, coreference.confidence)


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