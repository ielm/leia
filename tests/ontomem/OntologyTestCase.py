from ontomem.memory import Memory
from ontomem.ontology import Concept
from unittest import TestCase


class OntologyTestCase(TestCase):

    pass


class ConceptTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "")

    def test_parse_basic_fields(self):
        concept = Concept(self.m, "test", contents={
            "name": "@test",
            "isa": ["@parent1", "@parent2"],
            "def": "test definition",
            "local": [],
            "block": [],
            "private": {}
        })

        parent1 = self.m.ontology.concept("parent1")
        parent2 = self.m.ontology.concept("parent2")

        self.assertEqual("test", concept.name)
        self.assertEqual({parent1, parent2}, concept._parents)
        self.assertEqual({}, concept.local)
        self.assertEqual({}, concept.block)
        self.assertEqual({}, concept.private)

    def test_parse_local_properties(self):

        # First, test that multiple slots, facets, and fillers are parsed
        # Verify that meta data is also attached
        concept = Concept(self.m, "test", contents={
            "isa": [],
            "local": [
                {"slot": "a", "facet": "sem", "filler": "ABC"},
                {"slot": "a", "facet": "sem", "filler": "DEF"},
                {"slot": "b", "facet": "sem", "filler": "GHI"},
                {"slot": "b", "facet": "relaxable-to", "filler": "JKL"},
                {"slot": "c", "facet": "sem", "filler": "MNO", "meta": {"measured-in": "something"}},
            ],
            "block": [],
            "private": {}
        })

        self.assertEqual([
            {"value": "ABC"},
            {"value": "DEF"}
        ], concept.local["a"]["sem"])

        self.assertEqual([
            {"value": "GHI"},
        ], concept.local["b"]["sem"])

        self.assertEqual([
            {"value": "JKL"},
        ], concept.local["b"]["relaxable-to"])

        self.assertEqual([
            {"value": "MNO", "measured-in": "something"},
        ], concept.local["c"]["sem"])

        # Now, test that various types are properly connected
        other = self.m.ontology.concept("other")
        prop = self.m.properties.get_property("prop")

        concept = Concept(self.m, "test", contents={
            "isa": [],
            "local": [
                {"slot": "a", "facet": "sem", "filler": "ABC"},
                {"slot": "b", "facet": "sem", "filler": "@other"},
                {"slot": "c", "facet": "sem", "filler": "$prop"},
            ],
            "block": [],
            "private": {}
        })

        self.assertEqual([
            {"value": "ABC"},
        ], concept.local["a"]["sem"])

        self.assertEqual([
            {"value": other},
        ], concept.local["b"]["sem"])

        self.assertEqual([
            {"value": prop},
        ], concept.local["c"]["sem"])

    def test_parse_block_properties(self):
        # First, test that multiple slots, facets, and fillers are parsed
        # Verify that meta data is also attached
        concept = Concept(self.m, "test", contents={
            "isa": [],
            "local": [],
            "block": [
                {"slot": "a", "facet": "sem", "filler": "ABC"},
                {"slot": "a", "facet": "sem", "filler": "DEF"},
                {"slot": "b", "facet": "sem", "filler": "GHI"},
                {"slot": "b", "facet": "relaxable-to", "filler": "JKL"},
                {"slot": "c", "facet": "sem", "filler": "MNO", "meta": {"measured-in": "something"}},
            ],
            "private": {}
        })

        self.assertEqual([
            {"value": "ABC"},
            {"value": "DEF"}
        ], concept.block["a"]["sem"])

        self.assertEqual([
            {"value": "GHI"},
        ], concept.block["b"]["sem"])

        self.assertEqual([
            {"value": "JKL"},
        ], concept.block["b"]["relaxable-to"])

        self.assertEqual([
            {"value": "MNO", "measured-in": "something"},
        ], concept.block["c"]["sem"])

        # Now, test that various types are properly connected
        other = self.m.ontology.concept("other")
        prop = self.m.properties.get_property("prop")

        concept = Concept(self.m, "test", contents={
            "isa": [],
            "local": [],
            "block": [
                {"slot": "a", "facet": "sem", "filler": "ABC"},
                {"slot": "b", "facet": "sem", "filler": "@other"},
                {"slot": "c", "facet": "sem", "filler": "$prop"},
            ],
            "private": {}
        })

        self.assertEqual([
            {"value": "ABC"},
        ], concept.block["a"]["sem"])

        self.assertEqual([
            {"value": other},
        ], concept.block["b"]["sem"])

        self.assertEqual([
            {"value": prop},
        ], concept.block["c"]["sem"])

    def test_parse_private_frames(self):
        fail()

    def test_parents(self):
        parent1 = Concept(self.m, "parent1")
        parent2 = Concept(self.m, "parent2")
        parent3 = Concept(self.m, "parent3")
        concept = Concept(self.m, "concept")

        # Naturally empty set
        self.assertEqual(set(), concept.parents())

        # Can add a parent
        concept.add_parent(parent1)
        self.assertEqual({parent1}, concept.parents())

        # Adding the same parent twice has no effect
        concept.add_parent(parent1)
        self.assertEqual({parent1}, concept.parents())

        # Can add more parents
        concept.add_parent(parent2)
        self.assertEqual({parent1, parent2}, concept.parents())

        # Can remove parents
        concept.remove_parent(parent2)
        self.assertEqual({parent1}, concept.parents())

        # Removing a parent that isn't defined has no effect
        concept.remove_parent(parent3)
        self.assertEqual({parent1}, concept.parents())

        # All parents can be removed
        concept.remove_parent(parent1)
        self.assertEqual(set(), concept.parents())

    def test_ancestors(self):
        grandparent1 = Concept(self.m, "gp1")
        grandparent2 = Concept(self.m, "gp2")
        grandparent3 = Concept(self.m, "gp3")
        parent1 = Concept(self.m, "p1")
        parent2 = Concept(self.m, "p2")
        concept = Concept(self.m, "concept")

        self.assertEqual(set(), concept.ancestors())
        self.assertEqual(set(), parent1.ancestors())
        self.assertEqual(set(), parent2.ancestors())
        self.assertEqual(set(), grandparent1.ancestors())
        self.assertEqual(set(), grandparent2.ancestors())
        self.assertEqual(set(), grandparent3.ancestors())

        concept.add_parent(parent1)
        concept.add_parent(parent2)
        parent1.add_parent(grandparent1)
        parent1.add_parent(grandparent2)
        parent2.add_parent(grandparent3)

        self.assertEqual({parent1, parent2, grandparent1, grandparent2, grandparent3}, concept.ancestors())
        self.assertEqual({grandparent1, grandparent2}, parent1.ancestors())
        self.assertEqual({grandparent3}, parent2.ancestors())
        self.assertEqual(set(), grandparent1.ancestors())
        self.assertEqual(set(), grandparent2.ancestors())
        self.assertEqual(set(), grandparent3.ancestors())

    def test_children(self):
        grandparent = Concept(self.m, "grandparent")
        parent = Concept(self.m, "parent")
        child1 = Concept(self.m, "child1")
        child2 = Concept(self.m, "child2")

        # They must be in memory to be looked up
        self.m.ontology.cache[grandparent.name] = grandparent
        self.m.ontology.cache[parent.name] = parent
        self.m.ontology.cache[child1.name] = child1
        self.m.ontology.cache[child2.name] = child2

        self.assertEqual(set(), grandparent.children())
        self.assertEqual(set(), parent.children())
        self.assertEqual(set(), child1.children())
        self.assertEqual(set(), child2.children())

        child1.add_parent(parent)
        child2.add_parent(parent)
        parent.add_parent(grandparent)

        self.assertEqual({parent}, grandparent.children())
        self.assertEqual({child1, child2}, parent.children())
        self.assertEqual(set(), child1.children())
        self.assertEqual(set(), child2.children())

    def test_descendants(self):
        grandparent = Concept(self.m, "grandparent")
        parent1 = Concept(self.m, "parent1")
        parent2 = Concept(self.m, "parent2")
        child1 = Concept(self.m, "child1")
        child2 = Concept(self.m, "child2")
        child3 = Concept(self.m, "child3")

        # They must be in memory to be looked up
        self.m.ontology.cache[grandparent.name] = grandparent
        self.m.ontology.cache[parent1.name] = parent1
        self.m.ontology.cache[parent2.name] = parent2
        self.m.ontology.cache[child1.name] = child1
        self.m.ontology.cache[child2.name] = child2
        self.m.ontology.cache[child3.name] = child3

        self.assertEqual(set(), grandparent.descendants())
        self.assertEqual(set(), parent1.descendants())
        self.assertEqual(set(), parent2.descendants())
        self.assertEqual(set(), child1.descendants())
        self.assertEqual(set(), child2.descendants())
        self.assertEqual(set(), child3.descendants())

        child1.add_parent(parent1)
        child2.add_parent(parent1)
        child3.add_parent(parent2)
        parent1.add_parent(grandparent)
        parent2.add_parent(grandparent)

        self.assertEqual({parent1, parent2, child1, child2, child3}, grandparent.descendants())
        self.assertEqual({child1, child2}, parent1.descendants())
        self.assertEqual({child3}, parent2.descendants())
        self.assertEqual(set(), child1.descendants())
        self.assertEqual(set(), child2.descendants())

    def test_siblings(self):
        parent1 = Concept(self.m, "parent1")
        parent2 = Concept(self.m, "parent2")
        child1 = Concept(self.m, "child1")
        child2 = Concept(self.m, "child2")
        child3 = Concept(self.m, "child3")

        # They must be in memory to be looked up
        self.m.ontology.cache[parent1.name] = parent1
        self.m.ontology.cache[parent2.name] = parent2
        self.m.ontology.cache[child1.name] = child1
        self.m.ontology.cache[child2.name] = child2
        self.m.ontology.cache[child3.name] = child3

        self.assertEqual(set(), parent1.siblings())
        self.assertEqual(set(), parent2.siblings())
        self.assertEqual(set(), child1.siblings())
        self.assertEqual(set(), child2.siblings())
        self.assertEqual(set(), child3.siblings())

        child1.add_parent(parent1)
        child2.add_parent(parent1)
        child3.add_parent(parent2)

        self.assertEqual(set(), parent1.siblings())
        self.assertEqual(set(), parent2.siblings())
        self.assertEqual({child2}, child1.siblings())
        self.assertEqual({child1}, child2.siblings())
        self.assertEqual(set(), child3.siblings())

    def test_isa(self):
        grandparent = Concept(self.m, "grandparent")
        parent = Concept(self.m, "parent")
        concept = Concept(self.m, "concept")
        other = Concept(self.m, "other")

        concept.add_parent(parent)
        parent.add_parent(grandparent)

        self.assertTrue(concept.isa(concept))
        self.assertTrue(concept.isa(parent))
        self.assertTrue(concept.isa(grandparent))
        self.assertFalse(concept.isa(other))

    def test_rows_includes_local(self):
        concept = Concept(self.m, "concept")

        self.assertEqual([], concept.rows())

        concept.add_local("color", "sem", ["red", "green", "blue"])

        self.assertEqual([
            Concept.LocalRow(concept, "color", "sem", ["red", "green", "blue"], dict())
        ], concept.rows())

        concept.add_local("height", "sem", [">", 0], measured_in="inches")

        self.assertEqual([
            Concept.LocalRow(concept, "color", "sem", ["red", "green", "blue"], dict()),
            Concept.LocalRow(concept, "height", "sem", [">", 0], {"measured-in": "inches"}),
        ], concept.rows())

        concept.remove_local("height", "sem", [">", 0])

        self.assertEqual([
            Concept.LocalRow(concept, "color", "sem", ["red", "green", "blue"], dict())
        ], concept.rows())

    def test_rows_includes_inherited(self):
        grandparent = Concept(self.m, "grandparent")
        parent = Concept(self.m, "parent")
        concept = Concept(self.m, "concept")

        concept.add_parent(parent)
        parent.add_parent(grandparent)

        self.assertEqual([], concept.rows())

        concept.add_local("color", "sem", ["red", "green"])

        self.assertEqual([
            Concept.LocalRow(concept, "color", "sem", ["red", "green"], dict())
        ], concept.rows())

        parent.add_local("color", "sem", ["blue", "yellow"])
        parent.add_local("height", "sem", [">", 0], measured_in="inches")
        grandparent.add_local("width", "sem", [">", 0], measured_in="inches")

        self.assertEqual([
            Concept.LocalRow(concept, "color", "sem", ["red", "green"], dict()),
            Concept.LocalRow(parent, "color", "sem", ["blue", "yellow"], dict()),
            Concept.LocalRow(parent, "height", "sem", [">", 0], {"measured-in": "inches"}),
            Concept.LocalRow(grandparent, "width", "sem", [">", 0], {"measured-in": "inches"}),
        ], concept.rows())

    def test_rows_includes_blocked(self):
        concept = Concept(self.m, "concept")

        self.assertEqual([], concept.rows())

        concept.add_block("color", "sem", ["red", "green"])

        self.assertEqual([
            Concept.BlockedRow(concept, "color", "sem", ["red", "green"])
        ], concept.rows())

        concept.add_block("color", "sem", ["blue", "yellow"])

        self.assertEqual([
            Concept.BlockedRow(concept, "color", "sem", ["red", "green"]),
            Concept.BlockedRow(concept, "color", "sem", ["blue", "yellow"])
        ], concept.rows())

        concept.remove_block("color", "sem", ["blue", "yellow"])

        self.assertEqual([
            Concept.BlockedRow(concept, "color", "sem", ["red", "green"])
        ], concept.rows())

    def test_rows_respects_blocking(self):
        grandparent = Concept(self.m, "grandparent")
        parent = Concept(self.m, "parent")
        concept = Concept(self.m, "concept")

        concept.add_parent(parent)
        parent.add_parent(grandparent)

        self.assertEqual([], concept.rows())

        grandparent.add_local("prop", "sem", ["a"])
        parent.add_local("prop", "sem", ["b"])
        concept.add_local("prop", "sem", ["c"])

        self.assertEqual([
            Concept.LocalRow(concept, "prop", "sem", ["c"], dict()),
            Concept.LocalRow(parent, "prop", "sem", ["b"], dict()),
            Concept.LocalRow(grandparent, "prop", "sem", ["a"], dict()),
        ], concept.rows())

        concept.add_block("prop", "sem", ["b"])

        self.assertEqual([
            Concept.LocalRow(concept, "prop", "sem", ["c"], dict()),
            Concept.BlockedRow(concept, "prop", "sem", ["b"]),
            Concept.LocalRow(grandparent, "prop", "sem", ["a"], dict()),
        ], concept.rows())

        parent.add_block("prop", "sem", ["a"])

        self.assertEqual([
            Concept.LocalRow(concept, "prop", "sem", ["c"], dict()),
            Concept.BlockedRow(concept, "prop", "sem", ["b"]),
        ], concept.rows())

    def test_rows_respects_blocking_wildcard(self):
        grandparent = Concept(self.m, "grandparent")
        parent = Concept(self.m, "parent")
        concept = Concept(self.m, "concept")

        concept.add_parent(parent)
        parent.add_parent(grandparent)

        self.assertEqual([], concept.rows())

        grandparent.add_local("prop", "sem", ["a"])
        parent.add_local("prop", "sem", ["b"])
        concept.add_local("prop", "sem", ["c"])

        self.assertEqual([
            Concept.LocalRow(concept, "prop", "sem", ["c"], dict()),
            Concept.LocalRow(parent, "prop", "sem", ["b"], dict()),
            Concept.LocalRow(grandparent, "prop", "sem", ["a"], dict()),
        ], concept.rows())

        concept.add_block("prop", "sem", "*")

        self.assertEqual([
            Concept.LocalRow(concept, "prop", "sem", ["c"], dict()),
            Concept.BlockedRow(concept, "prop", "sem", "*"),
        ], concept.rows())

    def test_fillers(self):
        grandparent = Concept(self.m, "grandparent")
        parent = Concept(self.m, "parent")
        concept = Concept(self.m, "concept")

        concept.add_parent(parent)
        parent.add_parent(grandparent)

        self.assertEqual([], concept.rows())

        grandparent.add_local("prop", "sem", "a")
        parent.add_local("prop", "sem", "b")
        concept.add_local("prop", "sem", "c")
        concept.add_local("other", "sem", "d")
        concept.add_local("prop", "relaxable-to", "e")

        concept.add_block("prop", "sem", "b")

        self.assertEqual({
            "a",
            "c"
        }, set(concept.fillers("prop", "sem")))

    def test_private_frames(self):
        # Add to parsing above as well (local/block)
        fail()

    def test_sets(self):
        # Add to parsing above as well (local/block)
        fail()

    def test_evaluate(self):
        fail()

    def test_allowed(self):
        fail()

    def test_validate(self):
        fail()