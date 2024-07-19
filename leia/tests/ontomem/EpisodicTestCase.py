from leia.ontomem.ontology import Concept
from leia.ontomem.episodic import Address, Filler, Instance, Space, XMR
from leia.ontomem.memory import Memory
from unittest import TestCase
from unittest.mock import MagicMock, patch


class SpaceTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

    def test_instance(self):
        # None is returned if the instance is unknown
        self.assertIsNone(self.m.episodic.instance("C.1"))
        self.assertFalse(self.m.episodic.has_instance("C.1"))

        # A new instance can be added and returned by id
        instance1 = self.m.episodic.new_instance("C")
        self.assertEqual(instance1, self.m.episodic.instance("C.1"))
        self.assertTrue(self.m.episodic.has_instance("C.1"))

        # A new space does not see other space's instances
        space = self.m.episodic.new_space("TEST")
        self.assertIsNone(space.instance("C.1"))
        self.assertFalse(space.has_instance("C.1"))

        # A new instance added to a new space gets a local and global id
        instance2 = space.new_instance("C")
        self.assertEqual(instance2, space.instance("C.1"))
        self.assertTrue(space.has_instance("C.1"))
        self.assertEqual(instance2, self.m.episodic.instance("C.2"))
        self.assertTrue(self.m.episodic.has_instance("C.2"))

        # An existing instance can be registered into a space
        space.register_instance(instance1)
        self.assertEqual(instance1, space.instance("C.2"))
        self.assertTrue(space.has_instance("C.2"))

        # All instances can be returned
        self.assertEqual([instance2, instance1], space.instances())

    def test_spaces(self):
        space = Space(self.m, "TEST")

        # An empty list is returned
        self.assertEqual([], space.spaces())

        # New spaces have a link to their parent
        space1 = space.new_space("1")
        space2 = space.new_space("2")
        self.assertIsNone(space.parent())
        self.assertEqual(space, space1.parent())
        self.assertEqual(space, space2.parent())

        # Returns all known spaces
        self.assertEqual(
            {space1.name(), space2.name()}, set(map(lambda s: s.name(), space.spaces()))
        )

        # Private spaces are not returned by default
        space3 = space.new_space("3", private=True)
        self.assertEqual(
            {space1.name(), space2.name()}, set(map(lambda s: s.name(), space.spaces()))
        )

        # Private spaces can be included optionally
        self.assertEqual(
            {space1.name(), space2.name(), space3.name()},
            set(map(lambda s: s.name(), space.spaces(include_private=True))),
        )

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
        self.assertEqual(1234, instance.index(space=em))
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

        self.assertEqual(
            [f1, f2, f3], self.m.episodic.instances_of(c1, include_descendants=True)
        )
        self.assertEqual(
            [f4, f5], self.m.episodic.instances_of(c2, include_descendants=True)
        )

    def test_address(self):
        self.assertEqual(Address(self.m, self.m.episodic), self.m.episodic.address())

        space1 = self.m.episodic.new_space("TEST1")
        space2 = self.m.episodic.new_space("TEST2")
        space3 = space1.new_space("TEST3")
        space4 = space1.new_space("TEST4")
        space5 = space3.new_space("TEST5")

        self.assertEqual(Address(self.m, self.m.episodic, space1), space1.address())
        self.assertEqual(Address(self.m, self.m.episodic, space2), space2.address())
        self.assertEqual(
            Address(self.m, self.m.episodic, space1, space3), space3.address()
        )
        self.assertEqual(
            Address(self.m, self.m.episodic, space1, space4), space4.address()
        )
        self.assertEqual(
            Address(self.m, self.m.episodic, space1, space3, space5), space5.address()
        )


class XMRTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

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
        self.m = Memory()

    def test_id(self):
        c = Concept(self.m, "C1")
        f = Instance(self.m, c, 1)

        self.assertEqual("C1.1", f.id())

        f = Space(self.m, "TEST", private=True).new_instance("C1")

        self.assertEqual("C1.1", f.id())

    def test_address(self):
        f = self.m.episodic.new_instance("C")
        self.assertEqual(Address(self.m, self.m.episodic, f), f.address())

        s = self.m.episodic.new_space("TEST")
        s.register_instance(f)
        self.assertEqual(Address(self.m, self.m.episodic, s, f), f.address(space=s))

        x = self.m.episodic.new_space("XYZ")
        self.assertIsNone(f.address(space=x))

        self.assertEqual(
            [
                Address(self.m, self.m.episodic, f),
                Address(self.m, self.m.episodic, s, f),
            ],
            f.addresses(),
        )

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

        frame.remove_filler("AGENT", "a")  # Nothing happens (no errors are thrown)

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


class AddressTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

    def test_resolve(self):
        # By default, addresses resolve to the episodic root
        self.assertEqual(self.m.episodic, Address(self.m).resolve())

        # An address can resolve to any sub space
        space1 = self.m.episodic.new_space("TEST1")
        space2 = self.m.episodic.new_space("TEST2")
        space3 = space1.new_space("TEST3")

        self.assertEqual(space1, Address(self.m, self.m.episodic, space1).resolve())
        self.assertEqual(space2, Address(self.m, self.m.episodic, space2).resolve())
        self.assertEqual(
            space3, Address(self.m, self.m.episodic, space1, space3).resolve()
        )

        # An address can resolve to any instance within a space
        instance = space3.new_instance("C")

        self.assertEqual(
            instance,
            Address(self.m, self.m.episodic, space1, space3, instance).resolve(),
        )

        # An address can resolve to a property on an instance
        # If no value is present, the VALUE facet of the instance's concept will be used (or None if undefined)
        # If a value is present, it will be returned
        # If multiple values are present, an error is raised
        size = self.m.properties.get_property("SIZE")
        self.assertIsNone(
            Address(self.m, self.m.episodic, space1, space3, instance, size).resolve()
        )

        concept = self.m.ontology.concept("C")
        concept.add_local("SIZE", "SEM", 0.0)
        self.assertIsNone(
            Address(self.m, self.m.episodic, space1, space3, instance, size).resolve()
        )

        concept.add_local("SIZE", "VALUE", 1.0)
        self.assertEqual(
            1.0,
            Address(self.m, self.m.episodic, space1, space3, instance, size).resolve(),
        )

        instance.add_filler("SIZE", 2.0)
        self.assertEqual(
            2.0,
            Address(self.m, self.m.episodic, space1, space3, instance, size).resolve(),
        )

        instance.add_filler("SIZE", 3.0)
        with self.assertRaises(Exception):
            Address(self.m, self.m.episodic, space1, space3, instance, size).resolve()
