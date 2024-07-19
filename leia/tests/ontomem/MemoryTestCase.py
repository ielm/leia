from leia.ontomem.memory import Memory, OntoMemEditBuffer
from unittest import TestCase


class OntoMemEditBufferTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

    def test_note_edited(self):
        buffer = OntoMemEditBuffer(self.m)
        self.assertEqual(set(), buffer.edited())

        buffer.note_edited("OBJECT", "DEKADE")
        self.assertEqual({"OBJECT"}, buffer.edited())
        self.assertEqual({"OBJECT"}, buffer.edited("DEKADE"))
        self.assertEqual(set(), buffer.edited("OTHER"))

        buffer.note_edited("EVENT", "OTHER")
        self.assertEqual({"OBJECT", "EVENT"}, buffer.edited())
        self.assertEqual({"OBJECT"}, buffer.edited("DEKADE"))
        self.assertEqual({"EVENT"}, buffer.edited("OTHER"))
        self.assertEqual(set(), buffer.edited("XYZ"))

        buffer.clear(identifier="EVENT")
        self.assertEqual({"OBJECT"}, buffer.edited())
        self.assertEqual({"OBJECT"}, buffer.edited("DEKADE"))
        self.assertEqual(set(), buffer.edited("OTHER"))

        buffer.clear()
        self.assertEqual(set(), buffer.edited())