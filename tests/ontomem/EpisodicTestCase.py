from ontomem.ontology import Concept
from ontomem.episodic import EpisodicMemory, Filler, Frame, Space
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

        self.assertEqual(1, em._next_instance_for_concept(c1))
        self.assertEqual(2, em._next_instance_for_concept(c1))
        self.assertEqual(3, em._next_instance_for_concept(c1))
        self.assertEqual(1, em._next_instance_for_concept(c2))
        self.assertEqual(2, em._next_instance_for_concept(c2))
        self.assertEqual(3, em._next_instance_for_concept(c2))
        self.assertEqual(4, em._next_instance_for_concept(c1))

    def test_new_instance(self):
        c = Concept(self.m, "C1")
        em = EpisodicMemory(self.m)
        em._next_instance_for_concept = MagicMock(return_value=1234)

        self.assertIsNone(em.instance("C1.1234"))

        instance = em.new_instance(c)
        self.assertEqual(c, instance.concept)
        self.assertEqual(1234, instance.index)
        self.assertEqual(self.m, instance.memory)

        em._next_instance_for_concept.assert_called_once()

        self.assertIsNotNone(em.instance("C1.1234"))

    def test_remove_instance(self):
        c = Concept(self.m, "C")

        space = self.m.episodic.space("TEST")
        f = space.new_instance(c)

        self.assertEqual(f, self.m.episodic.instance(f.id()))
        self.assertIn(f.id(), space.instances)

        self.m.episodic.remove_instance(f)

        # The instance is removed from memory, and all spaces that contain it
        self.assertIsNone(self.m.episodic.instance(f.id()))
        self.assertNotIn(f.id(), space.instances)


class SpaceTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_new_instance(self):
        c1 = Concept(self.m, "C1")
        c2 = Concept(self.m, "C2")

        space = Space(self.m, "TEST")

        f1 = space.new_instance(c1)
        f2 = space.new_instance(c1)
        f3 = space.new_instance(c2)

        self.assertEqual("C1.1", f1.id())
        self.assertEqual("C1.2", f2.id())
        self.assertEqual("C2.1", f3.id())

        self.assertEqual(f1, space.instances[f1.id()])
        self.assertEqual(f2, space.instances[f2.id()])
        self.assertEqual(f3, space.instances[f3.id()])

    def test_remove_instance(self):
        c = Concept(self.m, "C")

        space = self.m.episodic.space("TEST")
        f = space.new_instance(c)

        self.assertEqual(f, self.m.episodic.instance(f.id()))
        self.assertIn(f.id(), space.instances)

        space.remove_instance(f)

        # The instance is still in memory, but no longer indexed in the space
        self.assertEqual(f, self.m.episodic.instance(f.id()))
        self.assertNotIn(f.id(), space.instances)


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

    def test_values(self):

        c = Concept(self.m, "C1")
        f = Frame(self.m, c, 1)

        self.assertEqual([], f.values("S1"))
        self.assertEqual([], f.values("S2"))

        f.add_filler("S1", "ABC")

        self.assertEqual(["ABC"], f.values("S1"))
        self.assertEqual([], f.fillers("S2"))

        f.add_filler("S1", "DEF")

        self.assertEqual(["ABC", "DEF"], f.fillers("S1"))
        self.assertEqual([], f.fillers("S2"))

        f.add_filler("S2", "GHI")

        self.assertEqual(["ABC", "DEF"], f.fillers("S1"))
        self.assertEqual(["GHI"], f.fillers("S2"))

        x = f.add_filler("S2", "JKL", timestamp=3456)

        self.assertEqual(["ABC", "DEF"], f.fillers("S1"))
        self.assertEqual(["GHI", "JKL"], f.fillers("S2"))
        self.assertEqual(x, f)

    def test_remove_filler(self):

        c = Concept(self.m, "C1")
        frame = Frame(self.m, c, 1)

        frame.remove_filler("AGENT", "a")   # Nothing happens (no errors are thrown)

        frame.add_filler("AGENT", "a")
        frame.add_filler("AGENT", "b")
        frame.add_filler("XYZ", "c")

        self.assertEqual(["a", "b"], frame.values("AGENT"))
        self.assertEqual(["c"], frame.values("XYZ"))

        frame.remove_filler("AGENT", "a")

        self.assertEqual(["b"], frame.values("AGENT"))
        self.assertEqual(["c"], frame.values("XYZ"))

        frame.remove_filler("AGENT", "b")

        self.assertEqual([], frame.values("AGENT"))
        self.assertNotIn("AGENT", frame.properties.keys())
        self.assertEqual(["c"], frame.values("XYZ"))