from leia.ontomem.lexicon import SemStruc, Sense, SynStruc
from leia.ontosem.analysis import WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.analyzer import Preprocessor, SyntacticAnalyzer, WMLexiconLoader
from leia.ontosem.syntax.results import ConstituencyNode, Syntax, Word
from leia.tests.LEIATestCase import LEIATestCase
from typing import List
from unittest import TestCase
from unittest.mock import call, MagicMock, patch


class PreprocessorTestCase(TestCase):

    def test_analyze(self):
        text = "He can't do it."
        self.assertEqual("He can not do it.", Preprocessor(OntoSemConfig()).run(text))


class SyntacticAnalyzerTestCase(TestCase):

    @patch("leia.ontosem.syntax.analyzer.subprocess")
    @patch("leia.ontosem.syntax.analyzer.Syntax")
    def test_analyze(self, mock_syntax: MagicMock, mock_subprocess: MagicMock):
        mock_subprocess.Popen = MagicMock()
        mock_process = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_process.communicate.return_value = b"[1]>\n(some lisp string)", b""
        mock_syntax.from_lisp_string.return_value = "some output"

        config = OntoSemConfig()

        text = "Some text input."
        analyzer = SyntacticAnalyzer(config)
        result = analyzer.run(text)

        self.assertEqual("some output", result)

        host = config.corenlp_host
        port = config.corenlp_port
        type = "default"
        lexicon = config.ontosyn_lexicon
        mem_file = config.ontosyn_mem

        lisp_exe = '(run-syntax \'%s \"%s\" \"%s\" \"%s\" %d)' % (type, lexicon, text, host, port)

        mock_subprocess.Popen.assert_called_once_with('clisp -q --silent -M %s' % mem_file, shell=True, stdin=mock_subprocess.PIPE, stderr=mock_subprocess.PIPE, stdout=mock_subprocess.PIPE)
        mock_process.communicate.assert_called_once_with(str.encode(lisp_exe))
        mock_syntax.from_lisp_string.assert_called_once_with("(some lisp string)")


class WMLexiconLoaderTestCase(LEIATestCase):

    def test_get_senses_for_word(self):
        config = OntoSemConfig()
        sense1 = Sense(config.memory(), "TEST-N1", contents=self.mockSense("TEST-N1"))
        sense2 = Sense(config.memory(), "TEST-N2", contents=self.mockSense("TEST-N2"))

        word = config.lexicon().word("TEST")
        word.senses = MagicMock(return_value=[sense1, sense2])

        loader = WMLexiconLoader(config)

        # Normally, the loader retrieves all senses returned
        self.assertEqual([sense1, sense2], loader.get_senses_for_word(self.mockWord(0, "TEST", "N")))

        # The loader also ignores case
        self.assertEqual([sense1, sense2], loader.get_senses_for_word(self.mockWord(0, "test", "N")))

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
        lexicon = WMLexicon()
        lexicon.add_sense = MagicMock()

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
        config = OntoSemConfig()
        loader = WMLexiconLoader(config)

        an1 = Sense(config.memory(), "A-N1")
        an2 = Sense(config.memory(), "A-N2")
        bn1 = Sense(config.memory(), "B-N1")
        cn1 = Sense(config.memory(), "C-N1")
        dn1 = Sense(config.memory(), "D-N1")
        en1 = Sense(config.memory(), "D-N1")    # Should not be loaded

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
        loader.run(lexicon, syntax)

        lexicon.add_sense.assert_has_calls([
            call(word1, an1),
            call(word1, an2),
            call(word2, bn1),
            call(word3, cn1),
            call(word4, dn1),
        ])

    def test_generate_sense_for_word(self):

        loader = WMLexiconLoader(OntoSemConfig())

        # Generate sense should create a basic (nearly empty) sense with appropriate word/POS/and generated sense id.
        sense = loader.generate_sense_for_word(self.mockWord(0, "WORD", "NOUN"))
        self.assertEqual("WORD", sense.word.name)
        self.assertEqual(["NOUN"], sense.pos)
        self.assertEqual("WORD-NOUN1?", sense.id)
        self.assertEqual(SynStruc(contents=[{"type": "root"}]), sense.synstruc)

        # Generated senses will increment their index
        self.assertEqual("WORD-NOUN2?", loader.generate_sense_for_word(self.mockWord(0, "WORD", "NOUN")).id)
        self.assertEqual("WORD-VERB1?", loader.generate_sense_for_word(self.mockWord(0, "WORD", "VERB")).id)
        self.assertEqual("TEST-NOUN1?", loader.generate_sense_for_word(self.mockWord(0, "TEST", "NOUN")).id)

        # Generated senses will switch their semstruc based on POS type
        self.assertEqual(SemStruc("OBJECT"), loader.generate_sense_for_word(self.mockWord(0, "WORD", "NOUN")).semstruc)
        self.assertEqual(SemStruc("EVENT"), loader.generate_sense_for_word(self.mockWord(0, "WORD", "VERB")).semstruc)
        self.assertEqual(SemStruc("PROPERTY"), loader.generate_sense_for_word(self.mockWord(0, "WORD", "ADJ")).semstruc)
        self.assertEqual(SemStruc("PROPERTY"), loader.generate_sense_for_word(self.mockWord(0, "WORD", "ADV")).semstruc)

        # In the event of an unknown or unspecified POS, the semstruc is anchored in ALL
        self.assertEqual(SemStruc("ALL"), loader.generate_sense_for_word(self.mockWord(0, "WORD", "???")).semstruc)