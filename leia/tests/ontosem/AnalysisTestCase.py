from leia.ontomem.lexicon import Sense
from leia.ontomem.memory import Memory
from leia.ontosem.analysis import WMLexicon
from leia.ontosem.syntax.results import Word
from leia.tests.LEIATestCase import LEIATestCase


class WMLexiconTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory()

    def test_senses(self):
        lexicon = WMLexicon()

        word1 = Word(1, "man", ["N"], "man", 0, 2, Word.Ner.NONE, [], {})
        word2 = Word(2, "man", ["N"], "man", 3, 5, Word.Ner.NONE, [], {})

        s1 = Sense(self.m, "man-n1", contents=self.mockSense("man-n1"))
        s2 = Sense(self.m, "man-n2", contents=self.mockSense("man-n2"))

        # There are no senses currently defined for either word
        self.assertIsNone(lexicon.sense(word1, "man-n1"))
        self.assertIsNone(lexicon.sense(word1, "man-n2"))
        self.assertIsNone(lexicon.sense(word2, "man-n1"))
        self.assertIsNone(lexicon.sense(word2, "man-n2"))
        self.assertEqual([], lexicon.senses(word1))
        self.assertEqual([], lexicon.senses(word2))

        # Now add some senses; they should be retrievable
        lexicon.add_sense(word1, s1)
        lexicon.add_sense(word1, s2)
        lexicon.add_sense(word2, s1)

        self.assertEqual(s1, lexicon.sense(word1, "man-n1"))
        self.assertEqual(s2, lexicon.sense(word1, "man-n2"))
        self.assertEqual(s1, lexicon.sense(word2, "man-n1"))
        self.assertIsNone(lexicon.sense(word2, "man-n2"))
        self.assertEqual([s1, s2], lexicon.senses(word1))
        self.assertEqual([s1], lexicon.senses(word2))

        # Senses can be removed
        lexicon.remove_sense(word1, "man-n1")
        self.assertEqual([s2], lexicon.senses(word1))
        self.assertEqual([s1], lexicon.senses(word2))

        # Even though the senses are marked as equal, they are actually copies of each other
        self.assertEqual(s2, lexicon.sense(word1, "man-n2"))
        self.assertNotEqual(id(s2), id(lexicon.sense(word1, "man-n2")))

        s2.meaning_procedures = 123
        self.assertNotEqual(123, lexicon.sense(word1, "man-n2").meaning_procedures)
