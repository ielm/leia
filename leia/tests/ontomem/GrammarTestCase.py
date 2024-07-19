from leia.ontomem.memory import Memory
from unittest import TestCase


class POSInventoryTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

    def test_get(self):
        # POS are lazy-created on get, if needed
        pos = self.m.parts_of_speech.get("N")
        self.assertEqual(["N"], pos.names)

        # Once retrieved, the same object is returned
        self.assertEqual(pos, self.m.parts_of_speech.get("N"))

    def test_get_multiple_names(self):
        # Parts of speech can have multiple names
        pos = self.m.parts_of_speech.get("N")
        pos.names.append("NOUN")

        self.assertEqual(pos, self.m.parts_of_speech.get("NOUN"))


class POSTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

    def test_isa(self):
        gp = self.m.parts_of_speech.get("GP")
        p1 = self.m.parts_of_speech.get("P1")
        p2 = self.m.parts_of_speech.get("P2")
        c = self.m.parts_of_speech.get("C")

        p1.parents = [gp]
        p2.parents = [gp]
        c.parents = [p1]

        # A POS isa itself
        self.assertTrue(c.isa("C"))
        self.assertTrue(c.isa(c))

        # A POS isa one of its parents
        self.assertTrue(c.isa(p1))
        self.assertFalse(c.isa(p2))

        # A POS isa one of its ancestors (recursive)
        self.assertTrue(c.isa(gp))

        # A POS isa one of its parents with multiple names
        p1.names = ["P1", "OTHER"]
        self.assertTrue(c.isa("OTHER"))