from leia.ontomem.ontology import Concept
from leia.ontomem.episodic import Filler, Instance, Space, XMR
from leia.ontomem.memory import Memory
from unittest import TestCase
from unittest.mock import MagicMock, patch


class SpaceTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_instance(self):
        space = Space(self.m, "TEST")

        # None is returned if the instance is unknown
        self.assertIsNone(space.instance("C.1"))
        self.assertFalse(space.has_instance("C.1"))

        # A new instance can be returned by id
        instance = space.new_instance("C")
        self.assertEqual(instance, space.instance("C.1"))
        self.assertTrue(space.has_instance("C.1"))

        # An instance can be assigned / overwritten
        overwrite = Instance(self.m, "C", 1)
        space.register_instance(overwrite)
        self.assertNotEqual(instance, space.instance("C.1"))

        # All instances can be returned
        self.assertEqual([overwrite], space.instances())

    def test_spaces(self):
        space = Space(self.m, "TEST")

        # An empty list is returned
        self.assertEqual([], space.spaces())

        # Returns all known spaces
        space1 = space.new_space("1")
        space2 = space.new_space("2")
        self.assertEqual({space1.name(), space2.name()}, set(map(lambda s: s.name(), space.spaces())))

        # Private spaces are not returned by default
        space3 = space.new_space("3", private=True)
        self.assertEqual({space1.name(), space2.name()}, set(map(lambda s: s.name(), space.spaces())))

        # Private spaces can be included optionally
        self.assertEqual({space1.name(), space2.name(), space3.name()}, set(map(lambda s: s.name(), space.spaces(include_private=True))))

    def test_next_index_for_concept(self):
        c1 = Concept(self.m, "C1")
        c2 = Concept(self.m, "C2")

        em = Space(self.m, "TEST")

        self.assertEqual(1, em._next_instance_for_concept(c1))
        self.assertEqual(2, em._next_instance_for_concept(c1))
        self.assertEqual(3, em._next_instance_for_concept(c1))
        self.assertEqual(1, em._next_instance_for_concept(c2))
        self.assertEqual(2, em._next_instance_for_concept(c2))
        self.assertEqual(3, em._next_instance_for_concept(c2))
        self.assertEqual(4, em._next_instance_for_concept(c1))

    def test_next_index_for_space(self):
        space = Space(self.m, "TEST")

        self.assertEqual("Space.1", space._next_id_for_space(Space))
        self.assertEqual("Space.2", space._next_id_for_space(Space))
        self.assertEqual("Space.3", space._next_id_for_space(Space))
        self.assertEqual("Space.4", space._next_id_for_space(Space))
        self.assertEqual("XMR.1", space._next_id_for_space(XMR))
        self.assertEqual("XMR.2", space._next_id_for_space(XMR))
        self.assertEqual("XMR.3", space._next_id_for_space(XMR))
        self.assertEqual("XMR.4", space._next_id_for_space(XMR))

    def test_new_instance(self):
        c = Concept(self.m, "C1")
        em = Space(self.m, "TEST")
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
        f = self.m.episodic.new_instance(c)

        space = self.m.episodic.new_space("TEST")
        space.register_instance(f)

        self.assertEqual(f, self.m.episodic.instance(f.id()))
        self.assertEqual(f, space.instance(f.id()))

        self.m.episodic.remove_instance(f)

        # The instance is removed from memory, and all spaces that contain it
        self.assertIsNone(self.m.episodic.instance(f.id()))
        self.assertIsNone(space.instance(f.id()))

    def test_instances_of(self):
        c1 = Concept(self.m, "C1")
        c2 = Concept(self.m, "C2")

        f1 = self.m.episodic.new_instance(c1)
        f2 = self.m.episodic.new_instance(c1)
        f3 = self.m.episodic.new_instance(c1)
        f4 = self.m.episodic.new_instance(c2)
        f5 = self.m.episodic.new_instance(c2)

        self.assertEqual([f1, f2, f3], self.m.episodic.instances_of(c1))
        self.assertEqual([f4, f5], self.m.episodic.instances_of(c2))

        c2.add_parent(c1)

        self.assertEqual([f1, f2, f3], self.m.episodic.instances_of(c1, include_descendants=True))
        self.assertEqual([f4, f5], self.m.episodic.instances_of(c2, include_descendants=True))


class XMRTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_root(self):
        # The root is considered the EVENT with the least incoming relations and most outgoing relations.  In the case
        # of a tie, the "first" is selected.
        # If no EVENTs exist, then OBJECTs, and finally PROPERTYs are chosen.
        # None is returned if no frames exist at all.
        # Relations to concepts (not instances) are ignored.

        PROPERTY = self.m.ontology.concept("PROPERTY")
        OBJECT = self.m.ontology.concept("OBJECT")
        EVENT = self.m.ontology.concept("EVENT")

        xmr = XMR(self.m)
        self.assertIsNone(xmr.root())

        # Property is chosen as there is no other choice
        prop1 = xmr.new_instance(PROPERTY)
        self.assertEqual(prop1, xmr.root())

        # Object is chosen over property
        object1 = xmr.new_instance(OBJECT)
        self.assertEqual(object1, xmr.root())

        # Event is chosen over object
        event1 = xmr.new_instance(EVENT)
        self.assertEqual(event1, xmr.root())

        # An event with more outgoing relations (tied for incoming) is chosen
        event2 = xmr.new_instance(EVENT)
        event2.add_filler("THEME", object1)
        self.assertEqual(event2, xmr.root())

        # The event with the least incoming is chosen when outgoing is tied
        event1.add_filler("THEME", event2)
        self.assertEqual(event1, xmr.root())

        # The first event is chosen in the case of a complete tie
        prop1.add_filler("SCOPE", event1)
        self.assertEqual(event1, xmr.root())

        # Relations to concepts are ignored.
        event2.add_filler("AGENT", OBJECT)
        self.assertEqual(event1, xmr.root())


class InstanceTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_id(self):
        c = Concept(self.m, "C1")
        f = Instance(self.m, c, 1)

        self.assertEqual("C1.1", f.id())

        f = Space(self.m, "TEST", private=True).new_instance("C1")

        self.assertEqual("C1.1", f.id())

    @patch("leia.ontomem.episodic.time.time")
    def test_fillers(self, mock_time: MagicMock):

        c = Concept(self.m, "C1")
        f = Instance(self.m, c, 1)

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
        f = Instance(self.m, c, 1)

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
        frame = Instance(self.m, c, 1)

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

    def test_set_filler(self):

        c = Concept(self.m, "C1")
        frame = Instance(self.m, c, 1)

        frame.set_filler("AGENT", "a")
        self.assertEqual(["a"], frame.values("AGENT"))

        frame.set_filler("AGENT", "b")
        self.assertEqual(["b"], frame.values("AGENT"))

        frame.set_filler("AGENT", ["c", "d"])
        self.assertEqual(["c", "d"], frame.values("AGENT"))

    def test_isa(self):

        c1 = Concept(self.m, "C1")
        c1.isa = MagicMock(return_value=True)

        c2 = Concept(self.m, "C2")

        instance = Instance(self.m, c1, 1)

        self.assertTrue(instance.isa(c2))

        c1.isa.assert_called_once_with(c2)