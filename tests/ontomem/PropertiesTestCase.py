from ontomem.memory import Memory
from ontomem.properties import Property
from unittest import TestCase


class PropertyInventoryTestCase(TestCase):

    def test_properties_with_type(self):
        memory = Memory("", "", "")
        memory.properties.add_property(Property(memory, "P1", {"type": "relation"}))
        memory.properties.add_property(Property(memory, "P2", {"type": "relation"}))
        memory.properties.add_property(Property(memory, "P3", {"type": "literal"}))
        memory.properties.add_property(Property(memory, "P4", {"type": "literal"}))
        memory.properties.add_property(Property(memory, "P5", {"type": "boolean"}))
        memory.properties.add_property(Property(memory, "P6", {"type": "boolean"}))

        self.assertEqual({"P1", "P2"}, set(map(lambda p: p.name, memory.properties.properties_with_type(Property.TYPE.RELATION))))
        self.assertEqual({"P3", "P4"}, set(map(lambda p: p.name, memory.properties.properties_with_type(Property.TYPE.LITERAL))))
        self.assertEqual({"P5", "P6"}, set(map(lambda p: p.name, memory.properties.properties_with_type(Property.TYPE.BOOLEAN))))

    def test_inverses(self):
        memory = Memory("", "", "")
        memory.properties.add_property(Property(memory, "RELATION", {"type": "relation"}))
        memory.properties.add_property(Property(memory, "R1", {"type": "relation", "inverse": "@R1-OF"}))
        memory.properties.add_property(Property(memory, "R2", {"type": "relation", "inverse": "@R2-OF"}))
        memory.properties.add_property(Property(memory, "R3", {"type": "relation"}))
        memory.properties.add_property(Property(memory, "OTHER", {"type": "literal"}))

        self.assertEqual({
            "R1-OF": "R1",
            "R2-OF": "R2",
            "R3-INVERSE": "R3",
            "RELATION-INVERSE": "RELATION",
        }, memory.properties.inverses())