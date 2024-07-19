from leia.ontomem.ontology import Concept
from leia.ontomem.episodic import EpisodicMemory, Filler, Instance, Space, XMR
from leia.ontomem.memory import Memory
from unittest import TestCase
from unittest.mock import MagicMock, patch


class EpisodicMemoryTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_space(self):
        # If the space does not exist, it is created, registered, and returned
        space1 = self.m.episodic.space("TEST")
        self.assertEqual("TEST", space1.name)
        self.assertFalse(space1.is_private())

        # If the space already exists, it is returned
        space2 = self.m.episodic.space("TEST")
        self.assertEqual(space1, space2)

        # The space can even be returned if it was privately registered, so long as the name is known
        spaceP = Space(self.m, "PRIVATE", private=True)
        self.assertEqual(spaceP, self.m.episodic.space("PRIVATE"))

    def test_spaces(self):
        # An empty list is returned
        self.assertEqual([], self.m.episodic.spaces())

        # Returns all known spaces
        space1 = Space(self.m, "1")
        space2 = Space(self.m, "2")
        self.assertEqual({space1.name, space2.name}, set(map(lambda s: s.name, self.m.episodic.spaces())))

        # Private spaces are not returned by default
        space3 = Space(self.m, "3", private=True)
        self.assertEqual({space1.name, space2.name}, set(map(lambda s: s.name, self.m.episodic.spaces())))

        # Private spaces can be included optionally
        self.assertEqual({space1.name, space2.name, space3.name}, set(map(lambda s: s.name, self.m.episodic.spaces(include_private=True))))

    def test_next_index_for_concept(self):
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


class SpaceTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_init_registers(self):
        space = Space(self.m, "TEST")

        self.assertTrue(space.name in self.m.episodic._spaces)
        self.assertEqual(space, self.m.episodic.space(space.name))

    def test_next_private_index(self):
        c1 = Concept(self.m, "C1")
        c2 = Concept(self.m, "C2")

        space = Space(self.m, "SPACE", private=True)

        self.assertEqual(1, space._next_private_index(c1))
        self.assertEqual(2, space._next_private_index(c1))
        self.assertEqual(3, space._next_private_index(c1))
        self.assertEqual(1, space._next_private_index(c2))
        self.assertEqual(2, space._next_private_index(c2))
        self.assertEqual(3, space._next_private_index(c2))
        self.assertEqual(4, space._next_private_index(c1))

        # Confirm that another private space has its own index

        other = Space(self.m, "OTHER", private=True)

        self.assertEqual(1, other._next_private_index(c1))
        self.assertEqual(2, other._next_private_index(c1))
        self.assertEqual(3, other._next_private_index(c1))
        self.assertEqual(1, other._next_private_index(c2))
        self.assertEqual(2, other._next_private_index(c2))
        self.assertEqual(3, other._next_private_index(c2))
        self.assertEqual(4, other._next_private_index(c1))

        # And finally, neither have impacted memory's indexes

        self.assertEqual(1, self.m.episodic._next_instance_for_concept(c1))
        self.assertEqual(2, self.m.episodic._next_instance_for_concept(c1))
        self.assertEqual(3, self.m.episodic._next_instance_for_concept(c1))
        self.assertEqual(1, self.m.episodic._next_instance_for_concept(c2))
        self.assertEqual(2, self.m.episodic._next_instance_for_concept(c2))
        self.assertEqual(3, self.m.episodic._next_instance_for_concept(c2))
        self.assertEqual(4, self.m.episodic._next_instance_for_concept(c1))

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

        self.assertIsNone(f1.private_to())
        self.assertIsNone(f2.private_to())
        self.assertIsNone(f3.private_to())

        self.assertEqual(f1, space.instances[f1.id()])
        self.assertEqual(f2, space.instances[f2.id()])
        self.assertEqual(f3, space.instances[f3.id()])

        self.assertEqual(f1, self.m.episodic.instance(f1.id()))
        self.assertEqual(f2, self.m.episodic.instance(f2.id()))
        self.assertEqual(f3, self.m.episodic.instance(f3.id()))

    def test_new_instance_in_private_space(self):
        c1 = Concept(self.m, "C1")
        c2 = Concept(self.m, "C2")

        space = Space(self.m, "TEST", private=True)

        f1 = space.new_instance(c1)
        f2 = space.new_instance(c1)
        f3 = space.new_instance(c2)

        self.assertEqual("TEST:C1.1", f1.id())
        self.assertEqual("TEST:C1.2", f2.id())
        self.assertEqual("TEST:C2.1", f3.id())

        self.assertEqual(space, f1.private_to())
        self.assertEqual(space, f2.private_to())
        self.assertEqual(space, f3.private_to())

        self.assertEqual(f1, space.instances[f1.id()])
        self.assertEqual(f2, space.instances[f2.id()])
        self.assertEqual(f3, space.instances[f3.id()])

        self.assertIsNone(self.m.episodic.instance(f1.id()))
        self.assertIsNone(self.m.episodic.instance(f2.id()))
        self.assertIsNone(self.m.episodic.instance(f3.id()))

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

    def test_remove_instance_in_private_space(self):
        c = Concept(self.m, "C")

        space = Space(self.m, "TEST", private=True)
        f = space.new_instance(c)

        self.assertIsNone(self.m.episodic.instance(f.id()))
        self.assertIn(f.id(), space.instances)

        space.remove_instance(f)

        # Memory is not affected (it was not there to begin with); no errors are thrown
        self.assertIsNone(self.m.episodic.instance(f.id()))
        self.assertNotIn(f.id(), space.instances)

    def test_go_public(self):
        # This method has no effect at all on currently public spaces.
        # For private spaces, the private toggle is switched (meaning it will show up in EpisodicMemory.spaces() by default).
        # Further, all instances inside it (which are private_to this space) will no longer have that flag, will have their
        # ids all updated to the global id space, and will be registered into memory.

        # Make a new concept, and add a few global instances (to take up IDs)
        concept = Concept(self.m, "C")
        i1 = self.m.episodic.new_instance(concept)
        i2 = self.m.episodic.new_instance(concept)
        i3 = self.m.episodic.new_instance(concept)

        # Make a private space, and add private instances to it
        space = Space(self.m, "TEST", private=True)
        f1 = space.new_instance(concept)
        f2 = space.new_instance(concept)
        f3 = space.new_instance(concept)

        # Sanity check that everything is currently private
        self.assertTrue(space.is_private())
        self.assertEqual(space, f1.private_to())
        self.assertEqual(space, f2.private_to())
        self.assertEqual(space, f3.private_to())
        self.assertEqual("TEST:C.1", f1.id())
        self.assertEqual("TEST:C.2", f2.id())
        self.assertEqual("TEST:C.3", f3.id())

        self.assertEqual([], self.m.episodic.spaces())
        self.assertEqual([i1, i2, i3], self.m.episodic.instances_of(concept))
        self.assertIsNone(self.m.episodic.instance(f1.id()))
        self.assertIsNone(self.m.episodic.instance(f2.id()))
        self.assertIsNone(self.m.episodic.instance(f3.id()))

        # Go public
        space.go_public()

        # Now verify that the space is public
        self.assertFalse(space.is_private())
        self.assertEqual([space], self.m.episodic.spaces())

        # Now verify that the space's instances are public
        self.assertIsNone(f1.private_to())
        self.assertIsNone(f2.private_to())
        self.assertIsNone(f3.private_to())
        self.assertEqual([i1, i2, i3, f1, f2, f3], self.m.episodic.instances_of(concept))
        self.assertIsNotNone(self.m.episodic.instance(f1.id()))
        self.assertIsNotNone(self.m.episodic.instance(f2.id()))
        self.assertIsNotNone(self.m.episodic.instance(f3.id()))

        # And verify that the space's instances have updated IDs
        self.assertEqual("C.4", f1.id())
        self.assertEqual("C.5", f2.id())
        self.assertEqual("C.6", f3.id())
        self.assertEqual(f1, space.instances[f1.id()])
        self.assertEqual(f2, space.instances[f2.id()])
        self.assertEqual(f3, space.instances[f3.id()])


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

        self.assertEqual("TEST:C1.1", f.id())

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