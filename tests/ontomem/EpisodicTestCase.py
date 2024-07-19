from ontomem.ontology import Concept
from ontomem.episodic import EpisodicMemory, Filler, Frame
from ontomem.memory import Memory
from unittest import TestCase
from unittest.mock import MagicMock, patch


class EpisodicMemoryTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_next_index_for(self):
        c1 = Concept(self.m, "C1")
        c2 = Concept(self.m, "C2")

        em = EpisodicMemory(self.m)

        self.assertEqual(1, em._next_index_for(c1))
        self.assertEqual(2, em._next_index_for(c1))
        self.assertEqual(3, em._next_index_for(c1))
        self.assertEqual(1, em._next_index_for(c2))
        self.assertEqual(2, em._next_index_for(c2))
        self.assertEqual(3, em._next_index_for(c2))
        self.assertEqual(4, em._next_index_for(c1))

    def test_new_instance(self):
        c = Concept(self.m, "C1")
        em = EpisodicMemory(self.m)
        em._next_index_for = MagicMock(return_value=1234)

        self.assertIsNone(em.instance("C1.1234"))

        instance = em.new_instance(c)
        self.assertEqual(c, instance.concept)
        self.assertEqual(1234, instance.index)
        self.assertEqual(self.m, instance.memory)

        em._next_index_for.assert_called_once()

        self.assertIsNotNone(em.instance("C1.1234"))


class FrameTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    @patch("ontomem.episodic.time.time")
    def test_fillers(self, mock_time: MagicMock):

        c = Concept(self.m, "C1")
        f = Frame(self.m, c, 1)

        self.assertEqual([], f.fillers("S1"))
        self.assertEqual([], f.fillers("S2"))

        mock_time.return_value = 1234
        f.add_filler("S1", "ABC")

        self.assertEqual([Filler("ABC", 1234)], f.fillers("S1"))
        self.assertEqual([], f.fillers("S2"))

        mock_time.return_value = 5678
        f.add_filler("S1", "DEF")

        self.assertEqual([Filler("ABC", 1234), Filler("DEF", 5678)], f.fillers("S1"))
        self.assertEqual([], f.fillers("S2"))

        mock_time.return_value = 9012
        f.add_filler("S2", "GHI")

        self.assertEqual([Filler("ABC", 1234), Filler("DEF", 5678)], f.fillers("S1"))
        self.assertEqual([Filler("GHI", 9012)], f.fillers("S2"))

        x = f.add_filler("S2", "JKL", timestamp=3456)

        self.assertEqual([Filler("ABC", 1234), Filler("DEF", 5678)], f.fillers("S1"))
        self.assertEqual([Filler("GHI", 9012), Filler("JKL", 3456)], f.fillers("S2"))
        self.assertEqual(x, f)