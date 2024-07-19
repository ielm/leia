from leia.ontomem.lexicon import SemStruc, Sense, SynStruc
from leia.ontosem.analysis import Analysis, WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.analyzer import Preprocessor, SpacyAnalyzer, WMLexiconLoader
from leia.ontosem.syntax.results import ConstituencyNode, Syntax, Word
from leia.tests.LEIATestCase import LEIATestCase
from typing import List
from unittest import TestCase
from unittest.mock import call, MagicMock, patch

import sys


class PreprocessorTestCase(TestCase):

    def test_analyze(self):
        text = "He can't do it."
        self.assertEqual("He can not do it.", Preprocessor(Analysis()).run(text))


class SpacyAnalyzerTestCase(TestCase):

    @patch("leia.ontosem.syntax.analyzer.Syntax")
    def test_run(self, mock_syntax: Syntax):
        # Spacy is an external general purpose syntactic analyzer; it should produce the following:
        #   tokenization, sentence splitting, lemmatization, part of speech tagging, morphology
        #   dependency parsing, constituency parsing, named entity recognition, and coreference resolution
        # Tests to validate the actual output will be part of the overall throughput / integration testing.
        # Here we want to verify that spacy is being called properly, and that its output is being passed
        # into the Syntax object.

        # Start by mocking all of the spacy imports; we don't need or want to import them here as the entire
        # pipeline will be mocked.  Mocking them here prevents them from being loaded (they are large and slow
        # to load).
        sys.modules["benepar"] = MagicMock()
        sys.modules["coreferee"] = MagicMock()
        sys.modules["en_core_web_lg"] = MagicMock()
        sys.modules["spacy"] = MagicMock()

        # Declare two additional mocks - one for the nlp interface, and one for the produced doc object.
        nlp = MagicMock()
        doc = MagicMock()

        nlp.add_pipe = MagicMock()
        nlp.return_value = doc

        sys.modules["en_core_web_lg"].load = MagicMock(return_value=nlp)

        doc.sents = ["sent1", "sent2", "sent3"]

        # Mock the Syntax object's classmethod that is responsible for parsing spacy output
        mock_syntax.from_spacy = MagicMock(
            side_effect=lambda input: "syntax-%s" % input
        )

        # Run the analyzer
        analyzer = SpacyAnalyzer(Analysis())
        results = analyzer.run("Test text.")

        # The benepar and coreferee plugins should have been added to the nlp pipeline
        nlp.add_pipe.assert_has_calls(
            [
                call("benepar", config={"model": "benepar_en3"}),
                call("coreferee"),
            ]
        )

        # The nlp pipeline should have been called with the input text
        nlp.assert_called_once_with("Test text.")

        # Syntax objects should be created for all sentences found in the resulting document
        mock_syntax.from_spacy.assert_has_calls(
            [
                call("sent1"),
                call("sent2"),
                call("sent3"),
            ]
        )

        # All of the syntax objects should be returned
        self.assertEqual(["syntax-sent1", "syntax-sent2", "syntax-sent3"], results)


class WMLexiconLoaderTestCase(LEIATestCase):

    def test_get_senses_for_word(self):
        analysis = Analysis()
        sense1 = Sense(
            analysis.config.memory(), "TEST-N1", contents=self.mockSense("TEST-N1")
        )
        sense2 = Sense(
            analysis.config.memory(), "TEST-N2", contents=self.mockSense("TEST-N2")
        )

        word = analysis.config.lexicon().word("TEST")
        word.senses = MagicMock(return_value=[sense1, sense2])

        loader = WMLexiconLoader(analysis)

        # Normally, the loader retrieves all senses returned
        self.assertEqual(
            [sense1, sense2], loader.get_senses_for_word(self.mockWord(0, "TEST", "N"))
        )

        # The loader also ignores case
        self.assertEqual(
            [sense1, sense2], loader.get_senses_for_word(self.mockWord(0, "test", "N"))
        )

        # If there are no defined senses for the word, the loader returns the result of a generated (default) word
        word.senses = MagicMock(return_value=[])
        loader.generate_sense_for_word = MagicMock(return_value=1234)

        input = self.mockWord(0, "TEST", "N")
        self.assertEqual([1234], loader.get_senses_for_word(input))
        loader.generate_sense_for_word.assert_called_once_with(input)

    def test_run(self):
        # Run should find all senses of every word in each sentence, and add them to the WMLexicon (which
        # is responsible for making copies).

        # First, make a lexicon (mock add_sense so we can detect it was called)
        analysis = Analysis()
        analysis.lexicon.add_sense = MagicMock()

        # Next, make a multi-sentence syntactic input
        word1 = self.mockWord(1, "A", "N")
        word2 = self.mockWord(2, "B", "N")
        word3 = self.mockWord(3, "C", "N")
        word4 = self.mockWord(4, "D", "N")

        syntax = [
            Syntax([word1, word2], "", "", ConstituencyNode(""), []),
            Syntax([word3, word4], "", "", ConstituencyNode(""), []),
        ]

        # Next, make a loader (mock get_senses_for_word so we can confirm the senses retrieved from the source lexicon)
        loader = WMLexiconLoader(analysis)

        an1 = Sense(analysis.config.memory(), "A-N1")
        an2 = Sense(analysis.config.memory(), "A-N2")
        bn1 = Sense(analysis.config.memory(), "B-N1")
        cn1 = Sense(analysis.config.memory(), "C-N1")
        dn1 = Sense(analysis.config.memory(), "D-N1")
        en1 = Sense(analysis.config.memory(), "D-N1")  # Should not be loaded

        def _get_senses(word: Word) -> List[Sense]:
            return {
                "A": [an1, an2],
                "B": [bn1],
                "C": [cn1],
                "D": [dn1],
                "E": [en1],
            }[word.lemma]

        loader.get_senses_for_word = MagicMock(side_effect=_get_senses)

        # Run the loader, and confirm each sense was loaded properly
        loader.run(syntax)

        analysis.lexicon.add_sense.assert_has_calls(
            [
                call(word1, an1),
                call(word1, an2),
                call(word2, bn1),
                call(word3, cn1),
                call(word4, dn1),
            ]
        )

    def test_generate_sense_for_word(self):

        loader = WMLexiconLoader(Analysis())

        # Generate sense should create a basic (nearly empty) sense with appropriate word/POS/and generated sense id.
        sense = loader.generate_sense_for_word(self.mockWord(0, "WORD", "NOUN"))
        self.assertEqual("WORD", sense.word.name)
        self.assertEqual(["NOUN"], sense.pos)
        self.assertEqual("WORD-NOUN1?", sense.id)
        self.assertEqual(SynStruc(contents=[{"type": "root"}]), sense.synstruc)

        # Generated senses will increment their index
        self.assertEqual(
            "WORD-NOUN2?",
            loader.generate_sense_for_word(self.mockWord(0, "WORD", "NOUN")).id,
        )
        self.assertEqual(
            "WORD-VERB1?",
            loader.generate_sense_for_word(self.mockWord(0, "WORD", "VERB")).id,
        )
        self.assertEqual(
            "TEST-NOUN1?",
            loader.generate_sense_for_word(self.mockWord(0, "TEST", "NOUN")).id,
        )

        # Generated senses will switch their semstruc based on POS type
        self.assertEqual(
            SemStruc("OBJECT"),
            loader.generate_sense_for_word(self.mockWord(0, "WORD", "NOUN")).semstruc,
        )
        self.assertEqual(
            SemStruc("EVENT"),
            loader.generate_sense_for_word(self.mockWord(0, "WORD", "VERB")).semstruc,
        )
        self.assertEqual(
            SemStruc("PROPERTY"),
            loader.generate_sense_for_word(self.mockWord(0, "WORD", "ADJ")).semstruc,
        )
        self.assertEqual(
            SemStruc("PROPERTY"),
            loader.generate_sense_for_word(self.mockWord(0, "WORD", "ADV")).semstruc,
        )

        # In the event of an unknown or unspecified POS, the semstruc is anchored in ALL
        self.assertEqual(
            SemStruc("ALL"),
            loader.generate_sense_for_word(self.mockWord(0, "WORD", "???")).semstruc,
        )
