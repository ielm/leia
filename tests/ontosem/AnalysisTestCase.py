from ontosem.analysis import Analysis, Sentence
from ontosem.config import OntoSemConfig
from ontosem.semantics.candidate import Candidate
from ontosem.syntax.results import SynMap, Syntax
from unittest import TestCase
from unittest.mock import MagicMock


class AnalysisToMemoryTestCase(TestCase):

    def test_to_memory(self):
        sentence1 = Sentence("S1")
        sentence2 = Sentence("S2")
        config = OntoSemConfig()

        sentence1.to_memory = MagicMock(return_value="S1 FRAME")
        sentence2.to_memory = MagicMock(return_value="S2 FRAME")

        analysis = Analysis(config)
        analysis.sentences = [sentence1, sentence2]

        frame = analysis.to_memory(speaker="@SPEAKER.1", listener="@LISTENER.1")

        self.assertEqual(config.to_dict(), frame["CONFIG"].singleton())
        self.assertEqual(["S1 FRAME", "S2 FRAME"], frame["HAS-SENTENCES"].values())

        sentence1.to_memory.assert_called_once_with(speaker="@SPEAKER.1", listener="@LISTENER.1")
        sentence2.to_memory.assert_called_once_with(speaker="@SPEAKER.1", listener="@LISTENER.1")


class SentenceToMemoryTestCase(TestCase):

    def test_to_memory(self):
        candidate1 = Candidate()
        candidate2 = Candidate()
        syntax = Syntax([], SynMap([]), [], "", "", [], [], [])

        candidate1.to_memory = MagicMock(return_value="TEST CANDIDATE 1")
        candidate2.to_memory = MagicMock(return_value="TEST CANDIDATE 2")
        syntax.to_dict = MagicMock(return_value={"syntax": "to_dict"})

        sentence = Sentence("The man hit the building.")
        sentence.syntax = syntax
        sentence.semantics = [candidate1, candidate2]

        frame = sentence.to_memory(speaker="@SPEAKER.1", listener="@LISTENER.1")

        self.assertEqual("The man hit the building.", frame["TEXT"].singleton())
        self.assertEqual({"syntax": "to_dict"}, frame["HAS-SYNTAX"].singleton())
        self.assertEqual(["TEST CANDIDATE 1", "TEST CANDIDATE 2"], frame["HAS-CANDIDATES"].values())

        candidate1.to_memory.assert_called_once_with("The man hit the building.", speaker="@SPEAKER.1", listener="@LISTENER.1")
        candidate2.to_memory.assert_called_once_with("The man hit the building.", speaker="@SPEAKER.1", listener="@LISTENER.1")