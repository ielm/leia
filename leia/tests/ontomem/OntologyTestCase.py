from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Concept, Ontology, OSet
from leia.ontomem.properties import COMPARATOR, WILDCARD
from unittest import skip, TestCase
from unittest.mock import MagicMock


class OntologyTestCase(TestCase):

    def test_common_ancestors(self):
        ontology = Memory("", "", "").ontology

        gp = ontology.concept("GRANDPARENT")
        p1 = ontology.concept("PARENT1").add_parent(gp)
        p2 = ontology.concept("PARENT2").add_parent(gp)
        c1 = ontology.concept("CHILD1").add_parent(p1)
        c2 = ontology.concept("CHILD2").add_parent(p1)
        c3 = ontology.concept("CHILD3").add_parent(p2)

        self.assertEqual({"GRANDPARENT", "PARENT1"}, ontology.common_ancestors("CHILD1", "CHILD2"))
        self.assertEqual({"GRANDPARENT"}, ontology.common_ancestors("CHILD1", "CHILD3"))
        self.assertEqual({"GRANDPARENT"}, ontology.common_ancestors("PARENT1", "PARENT2"))

    def test_distance_to_ancestor(self):
        ontology = Memory("", "", "").ontology

        gp = ontology.concept("GRANDPARENT")
        p1 = ontology.concept("PARENT1").add_parent(gp)
        p2 = ontology.concept("PARENT2").add_parent(gp)
        c1 = ontology.concept("CHILD1").add_parent(p1)
        c2 = ontology.concept("CHILD2").add_parent(p1)
        c3 = ontology.concept("CHILD3").add_parent(p2)

        self.assertEqual(0, ontology.distance_to_ancestor(gp.name, gp.name))
        self.assertEqual(1, ontology.distance_to_ancestor(p1.name, gp.name))
        self.assertEqual(1, ontology.distance_to_ancestor(p2.name, gp.name))
        self.assertEqual(2, ontology.distance_to_ancestor(c1.name, gp.name))
        self.assertEqual(2, ontology.distance_to_ancestor(c2.name, gp.name))
        self.assertEqual(2, ontology.distance_to_ancestor(c3.name, gp.name))
        self.assertEqual(1, ontology.distance_to_ancestor(c1.name, p1.name))
        self.assertEqual(1, ontology.distance_to_ancestor(c2.name, p1.name))
        self.assertEqual(1, ontology.distance_to_ancestor(c3.name, p2.name))

        self.assertIsNone(ontology.distance_to_ancestor(c1.name, c2.name))


class ConceptTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

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

        # Now, test for various wildcards in properties

        concept = Concept(self.m, "test", contents={
            "isa": [],
            "local": [
                {"slot": "a", "facet": "sem", "filler": "!AnyLit"},
                {"slot": "b", "facet": "sem", "filler": "^"},
            ],
            "block": [],
            "private": {}
        })

        self.assertEqual([
            {"value": WILDCARD.ANYLIT}
        ], concept.local["a"]["sem"])

        self.assertEqual([
            {"value": Concept.INHFLAG}
        ], concept.local["b"]["sem"])

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
        # Private frames that are found in the concept dictionary are parsed as normal
        # They are connected to any relations that attach to them
        # Their name overrides any matching public names (as it relates to attaching relations)
        # They can refer to each other

        # Declare two public concepts with the names "p1" and "p2"; these will "conflict" with the private
        # frames of the same name.
        public_p1 = self.m.ontology.concept("p1")
        public_p2 = self.m.ontology.concept("p2")

        # Declare some other frame to act as a parent.
        other = self.m.ontology.concept("other")

        # Parse a concept; it has two private frames "p1" and "p2"; it has a local property that refers to
        # p1 (which must choose to refer to the private frame over the public one), and p1 itself has a local
        # frame that refers to p2 (again, private is preferred).  The private frames do not have a private field
        # themselves, but are otherwise the same.
        concept = Concept(self.m, "test", contents={
            "name": "@test",
            "isa": [],
            "def": "test definition",
            "local": [{"slot": "a", "facet": "sem", "filler": "@p1"}],
            "block": [],
            "private": {
                "@p1": {
                    "name": "@p1",
                    "isa": ["@other"],
                    "def": "private concept 1",
                    "local": [{"slot": "a", "facet": "sem", "filler": "@p2"}],
                    "block": [],
                },
                "@p2": {
                    "name": "@p2",
                    "isa": ["@other"],
                    "def": "private concept 1",
                    "local": [{"slot": "a", "facet": "sem", "filler": "ABC"}],
                    "block": [],
                }
            }
        })

        self.assertEqual(2, len(concept.private))

        private_p1 = concept.private["p1"]
        private_p2 = concept.private["p2"]

        # Verify the isa field was parsed correctly
        self.assertTrue(private_p1.isa(other))
        self.assertTrue(private_p2.isa(other))

        # Verify that the concepts are not the same as the public ones
        self.assertNotEqual(public_p1, private_p1)
        self.assertNotEqual(public_p2, private_p2)

        # Even though they share the same name...
        self.assertEqual(public_p1.name, private_p1.name)
        self.assertEqual(public_p2.name, private_p2.name)

        # Verify the concept's relation points to the private frame
        self.assertEqual([private_p1], concept.fillers("a", "sem"))

        # Verify the private concept's relation points to the other private frame
        self.assertEqual([private_p2], private_p1.fillers("a", "sem"))

    def test_parse_sets(self):
        # Sets are special elements contained entirely within frames (they are not accessible from the ontology).
        # Unlike private concepts, which have the same behavior as other concepts, sets have a very limited behavior
        # encapsulated in four fields.
        # Sets essentially define either an AND (conjunctive) or OR (disjunctive) relationship between one or more
        # ontological elements (concepts, private concepts, other sets, and properties), and may define a required
        # cardinality.

        # A set can be used to say:
        #   A or B or C
        #   A and B and C
        #   3 of A or B or C
        #   3 each of A and B and C

        # Declare a global p1 concept (for a namespace collision), a global p2 concept, and a global prop1 property.
        p1 = self.m.ontology.concept("p1")
        p2 = self.m.ontology.concept("p2")
        prop1 = self.m.properties.get_property("prop1")

        # Parse a concept; it contains two sets, and a private concept.  One of the sets references the other, as well
        # as the private concept.  The set also references public concepts, and there is a namespace collision.
        concept = Concept(self.m, "test", contents={
            "name": "@test",
            "isa": [],
            "def": "test definition",
            "local": [{"slot": "a", "facet": "sem", "filler": "&s1"}],
            "block": [],
            "private": {
                "&s1": {
                    "name": "&s1",
                    "type": "conjunctive",
                    "cardinality": 4,
                    "members": ["@p1", "@p2", "&s2", "$prop1"]
                },
                "&s2": {
                    "name": "&s2",
                    "type": "disjunctive",
                    "cardinality": 1,
                    "members": []
                },
                "@p1": {
                    "name": "@p1",
                    "isa": ["@other"],
                    "def": "private concept 1",
                    "local": [{"slot": "a", "facet": "sem", "filler": "&s2"}],
                    "block": [],
                },
            }
        })

        # There should be three private elements (s1, s2, and p1)
        self.assertEqual(3, len(concept.private))

        # Verify their types
        self.assertIsInstance(concept.private["s1"], OSet)
        self.assertIsInstance(concept.private["s2"], OSet)
        self.assertIsInstance(concept.private["p1"], Concept)

        # Extract the private content
        s1: OSet = concept.private["s1"]
        s2: OSet = concept.private["s2"]
        private_p1: Concept = concept.private["p1"]

        # Verify s1 was parsed correctly
        self.assertEqual(OSet.Type.CONJUNCTIVE, s1.type())
        self.assertEqual(4, s1.cardinality())
        self.assertEqual([private_p1, p2, s2, prop1], s1.members())     # Note that @p1 uses the private concept

        # Verify s2 was parsed correctly
        self.assertEqual(OSet.Type.DISJUNCTIVE, s2.type())
        self.assertEqual(1, s2.cardinality())
        self.assertEqual([], s2.members())

        # Verify private_p1 references s2
        self.assertEqual([s2], private_p1.fillers("a", "sem"))

        # Verify concept references s1
        self.assertEqual([s1], concept.fillers("a", "sem"))

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
        grandparent = self.m.ontology.concept("grandparent")
        parent = self.m.ontology.concept("parent")
        child1 = self.m.ontology.concept("child1")
        child2 = self.m.ontology.concept("child2")

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
        grandparent = self.m.ontology.concept("grandparent")
        parent1 = self.m.ontology.concept("parent1")
        parent2 = self.m.ontology.concept("parent2")
        child1 = self.m.ontology.concept("child1")
        child2 = self.m.ontology.concept("child2")
        child3 = self.m.ontology.concept("child3")

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
        parent1 = self.m.ontology.concept("parent1")
        parent2 = self.m.ontology.concept("parent2")
        child1 = self.m.ontology.concept("child1")
        child2 = self.m.ontology.concept("child2")
        child3 = self.m.ontology.concept("child3")

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

    def test_rows_inherits_from_property(self):
        property = self.m.properties.get_property("property")
        property.set_contents({
            "name": "$property",
            "def": "",
            "type": "literal",
            "range": ["a", "b", "c"]
        })

        concept = self.m.ontology.concept("concept")
        concept.add_local("property", "sem", Concept.INHFLAG)

        rows = concept.rows()
        self.assertEqual(3, len(rows))
        self.assertIn(Concept.LocalRow(concept, "property", "sem", "a", dict()), rows)
        self.assertIn(Concept.LocalRow(concept, "property", "sem", "b", dict()), rows)
        self.assertIn(Concept.LocalRow(concept, "property", "sem", "c", dict()), rows)

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
        # Private frames are not registered in the ontology directly; they are only accessible from inside the
        # root frame that owns them.  Otherwise, they function normally.

        root = self.m.ontology.concept("ROOT")
        private = Concept(self.m, "PRIVATE")
        root.private["PRIVATE"] = private

        self.assertIn("ROOT", self.m.ontology.names())
        self.assertNotIn("PRIVATE", self.m.ontology.names())
        self.assertIn("PRIVATE", root.private)

        # The namespace for private frames is separate from public frames

        public = self.m.ontology.concept("PRIVATE")     # Same literal name as the private frame
        self.assertNotEqual(public, private)            # But they are different frames

    def test_sets(self):
        # Sets are not registered in the ontology directly; they are only accessible from inside the root frame
        # that owns them.  They are not complete frames, having only a handful of specialized fields.

        root = self.m.ontology.concept("ROOT")
        set = OSet(self.m, "SET")
        root.private["SET"] = set

        self.assertIn("ROOT", self.m.ontology.names())
        self.assertNotIn("SET", self.m.ontology.names())
        self.assertIn("SET", root.private)

        # The namespace for private frames is separate from public frames

        public = self.m.ontology.concept("SET")     # Same literal name as the private frame
        self.assertNotEqual(public, set)            # But they are different frames

    def test_allowed(self):
        # A filler is allowed if it evaluates to > 0

        concept = self.m.ontology.concept("concept")
        concept.evaluate = MagicMock()

        concept.evaluate.return_value = 0.5
        self.assertTrue(concept.allowed("slot", 123))

        concept.evaluate.return_value = 0.0
        self.assertFalse(concept.allowed("slot", 123))

    @skip("To be implemented later.")
    def test_validate(self):
        fail()


class ConceptEvaluateTestCase(TestCase):

    # Evaluate calculates a 0-1 result for a given value against a concept's defined property.
    # In other words, evaluate determines the "correctness" of a value for a concept's property.
    # Evaluate utilizes inheritance if local fillers are not defined.
    # Evaluate considers: hierarchy, sets, and flat values when making its determination.

    def setUp(self):
        self.m = Memory("", "", "")

    def test_simple_literal(self):
        concept = self.m.ontology.concept("concept")
        concept.add_local("literal1", "sem", "A")
        concept.add_local("literal1", "sem", "B")
        concept.add_local("literal1", "sem", "C")
        concept.add_local("literal2", "sem", WILDCARD.ANYLIT)

        self.assertEqual(0.9, concept.evaluate("literal1", "A"))     # The value is part of the local definition
        self.assertEqual(0.0, concept.evaluate("literal1", "D"))     # The value is not part of the local definition

        self.assertEqual(0.9, concept.evaluate("literal2", "A"))     # literal2 is a wildcard for any str
        self.assertEqual(0.9, concept.evaluate("literal2", "D"))     # literal2 is a wildcard for any str

    def test_simple_number(self):
        concept = self.m.ontology.concept("concept")
        concept.add_local("number1", "sem", (COMPARATOR.GT, 0))
        concept.add_local("number2", "sem", (COMPARATOR.GTE, 0))
        concept.add_local("number3", "sem", (COMPARATOR.LT, 0))
        concept.add_local("number4", "sem", (COMPARATOR.LTE, 0))
        concept.add_local("number5", "sem", (COMPARATOR.BETWEEN, 0, 2))
        concept.add_local("number6", "sem", (COMPARATOR.INCLUDE, 0, 2))
        concept.add_local("number7", "sem", WILDCARD.ANYNUM)

        self.assertEqual(0.9, concept.evaluate("number1", 1))
        self.assertEqual(0.0, concept.evaluate("number1", 0))

        self.assertEqual(0.9, concept.evaluate("number2", 1))
        self.assertEqual(0.9, concept.evaluate("number2", 0))
        self.assertEqual(0.0, concept.evaluate("number2", -1))

        self.assertEqual(0.9, concept.evaluate("number3", -1))
        self.assertEqual(0.0, concept.evaluate("number3", 0))

        self.assertEqual(0.9, concept.evaluate("number4", -1))
        self.assertEqual(0.9, concept.evaluate("number4", 0))
        self.assertEqual(0.0, concept.evaluate("number4", 1))

        self.assertEqual(0.9, concept.evaluate("number5", 1))
        self.assertEqual(0.0, concept.evaluate("number5", 0))
        self.assertEqual(0.0, concept.evaluate("number5", 2))
        self.assertEqual(0.0, concept.evaluate("number5", -1))

        self.assertEqual(0.9, concept.evaluate("number6", 1))
        self.assertEqual(0.9, concept.evaluate("number6", 0))
        self.assertEqual(0.9, concept.evaluate("number6", 2))
        self.assertEqual(0.0, concept.evaluate("number6", -1))

        self.assertEqual(0.9, concept.evaluate("number7", 1))

    def test_simple_boolean(self):
        concept = self.m.ontology.concept("concept")
        concept.add_local("boolean", "sem", WILDCARD.ANYBOOL)

        self.assertEqual(0.9, concept.evaluate("boolean", True))
        self.assertEqual(0.9, concept.evaluate("boolean", False))
        self.assertEqual(0.0, concept.evaluate("boolean", "xyz"))

    def test_simple_concept(self):
        other = self.m.ontology.concept("other")
        unused = self.m.ontology.concept("unused")

        concept = self.m.ontology.concept("concept")
        concept.add_local("concept1", "sem", other)
        concept.add_local("concept2", "sem", WILDCARD.ANYTYPE)

        self.assertEqual(0.9, concept.evaluate("concept1", other))
        self.assertEqual(0.0, concept.evaluate("concept1", unused))

        self.assertEqual(0.9, concept.evaluate("concept2", other))
        self.assertEqual(0.9, concept.evaluate("concept2", unused))

    def test_concept_with_inheritance(self):
        grandparent = self.m.ontology.concept("grandparent")
        parent = self.m.ontology.concept("parent")
        child = self.m.ontology.concept("child")

        child.add_parent(parent)
        parent.add_parent(grandparent)

        concept = self.m.ontology.concept("concept")
        concept.add_local("concept1", "sem", grandparent)

        # Currently no penalty for descendants
        self.assertEqual(0.9, concept.evaluate("concept1", grandparent))
        self.assertEqual(0.9, concept.evaluate("concept1", parent))
        self.assertEqual(0.9, concept.evaluate("concept1", child))

    def test_inherit_from_property(self):
        property = self.m.properties.get_property("property")
        property.set_contents({
            "name": "$property",
            "def": "",
            "type": "literal",
            "range": ["A", "B", "C"]
        })

        concept = self.m.ontology.concept("concept")
        concept.add_local("property", "sem", Concept.INHFLAG)

        self.assertEqual(0.9, concept.evaluate("property", "A"))
        self.assertEqual(0.9, concept.evaluate("property", "B"))
        self.assertEqual(0.9, concept.evaluate("property", "C"))
        self.assertEqual(0.0, concept.evaluate("property", "D"))

    def test_inherit_from_ancestors(self):
        # Sanity check; calculation of filler definitions is tested extensively in ConceptTestCase

        grandparent = self.m.ontology.concept("grandparent")
        parent = self.m.ontology.concept("parent")
        child = self.m.ontology.concept("child")

        child.add_parent(parent)
        parent.add_parent(grandparent)

        grandparent.add_local("literal", "sem", "A")
        grandparent.add_local("literal", "sem", "B")
        grandparent.add_local("literal", "sem", "C")

        self.assertEqual(0.9, child.evaluate("literal", "A"))
        self.assertEqual(0.9, child.evaluate("literal", "B"))
        self.assertEqual(0.9, child.evaluate("literal", "C"))
        self.assertEqual(0.0, child.evaluate("literal", "D"))

    def test_value_facet_overrides_all_others(self):
        # The value facet essentially blanks all other facets, including inherited ones.

        parent = self.m.ontology.concept("parent")
        child = self.m.ontology.concept("child")

        child.add_parent(parent)

        parent.add_local("literal", "sem", "A")
        parent.add_local("literal", "sem", "B")
        parent.add_local("literal", "sem", "C")
        child.add_local("literal", "relaxable-to", "D")
        child.add_local("literal", "relaxable-to", "E")
        child.add_local("literal", "value", "Z")

        self.assertEqual(1.0, child.evaluate("literal", "Z"))
        self.assertEqual(0.0, child.evaluate("literal", "A"))
        self.assertEqual(0.0, child.evaluate("literal", "B"))
        self.assertEqual(0.0, child.evaluate("literal", "C"))
        self.assertEqual(0.0, child.evaluate("literal", "D"))
        self.assertEqual(0.0, child.evaluate("literal", "E"))

    def test_facet_modifications_to_values(self):
        # The facet in which the value is declared will impact the final result

        concept = self.m.ontology.concept("concept")
        concept.add_local("literal", "default", "Z")
        concept.add_local("literal", "sem", "A")
        concept.add_local("literal", "sem", "B")
        concept.add_local("literal", "relaxable-to", "C")
        concept.add_local("literal", "relaxable-to", "D")
        concept.add_local("literal", "not", "E")
        concept.add_local("literal", "not", "F")

        self.assertEqual(1.0, concept.evaluate("literal", "Z"))
        self.assertEqual(0.9, concept.evaluate("literal", "A"))
        self.assertEqual(0.9, concept.evaluate("literal", "B"))
        self.assertEqual(0.25, concept.evaluate("literal", "C"))
        self.assertEqual(0.25, concept.evaluate("literal", "D"))
        self.assertEqual(0.0, concept.evaluate("literal", "E"))
        self.assertEqual(0.0, concept.evaluate("literal", "F"))

    def test_multiple_values_are_ord(self):
        # If multiple values are defined, they are OR'd together

        concept = self.m.ontology.concept("concept")
        concept.add_local("literal", "sem", "A")
        concept.add_local("literal", "sem", "B")
        concept.add_local("literal", "sem", "C")
        concept.add_local("literal", "sem", "D")

        self.assertEqual(0.9, concept.evaluate("literal", "A"))
        self.assertEqual(0.9, concept.evaluate("literal", "B"))
        self.assertEqual(0.9, concept.evaluate("literal", "C"))
        self.assertEqual(0.9, concept.evaluate("literal", "D"))

    @skip("Skip this for now; requires SETs to be defined in the episodic memory to properly evaluate.")
    def test_set_evaluations(self):
        # If the value defined is a set, evaluate against it's contents.
        # DISJUNCTIVE / CONJUNCTIVE must be considered.
        # If any members are also sets, the process must be recursive.
        # The input can also be a set, in which case the evaluation must consider unions / intersections, and cardinality.

        fail()