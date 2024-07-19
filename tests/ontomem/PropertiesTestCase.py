from ontomem.memory import Memory
from ontomem.properties import Property
from unittest import TestCase


class PropertyInventoryTestCase(TestCase):

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