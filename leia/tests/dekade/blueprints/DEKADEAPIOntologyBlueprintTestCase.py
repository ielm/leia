from leia.dekade.blueprints.ontology import DEKADEAPIOntologyBlueprint
from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Concept, OSet
from leia.ontomem.properties import COMPARATOR, WILDCARD
from unittest import TestCase
from unittest.mock import MagicMock


class DEKADEAPIOntologyBlueprintTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_cast_filler(self):
        app = MagicMock()
        app.static_folder = ""
        app.template_folder = ""
        bp = DEKADEAPIOntologyBlueprint(app)
        concept = self.m.ontology.concept("TEST")

        self.assertEqual(("@OBJECT", "concept"), bp._cast_filler(concept, self.m.ontology.concept("OBJECT")))
        self.assertEqual(("$RELATION", "property"), bp._cast_filler(concept, self.m.properties.get_property("RELATION")))
        self.assertEqual(("BLAH", "text"), bp._cast_filler(concept, "BLAH"))
        self.assertEqual(((">=", 1.0), "comparator"), bp._cast_filler(concept, (COMPARATOR.GTE, 1.0)))
        self.assertEqual((("=>=<", 1.0, 2.0), "comparator"), bp._cast_filler(concept, (COMPARATOR.INCLUDE, 1.0, 2.0)))
        self.assertEqual(("!AnyBool", "wildcard"), bp._cast_filler(concept, WILDCARD.ANYBOOL))
        self.assertEqual(("@SET.1", "set"), bp._cast_filler(concept, OSet(self.m, "SET.1")))
        self.assertEqual((1.0, "number"), bp._cast_filler(concept, 1.0))
        self.assertEqual((123, "number"), bp._cast_filler(concept, 123))

    def test_parse_filler(self):
        app = MagicMock()
        app.static_folder = ""
        app.template_folder = ""
        app.agent = MagicMock()
        app.agent.memory = self.m
        bp = DEKADEAPIOntologyBlueprint(app)
        concept = self.m.ontology.concept("TEST")

        # Concepts (with or without the identifier signal)
        self.assertEqual(self.m.ontology.concept("OBJECT"), bp._parse_filler(concept, "@OBJECT", "concept"))
        self.assertEqual(self.m.ontology.concept("OBJECT"), bp._parse_filler(concept, "OBJECT", "concept"))

        # Private concepts take precedence
        concept.private["OBJECT"] = Concept(self.m, "OBJECT", root=concept)
        self.assertEqual(concept.private["OBJECT"], bp._parse_filler(concept, "@OBJECT", "concept"))
        self.assertEqual(concept.private["OBJECT"], bp._parse_filler(concept, "OBJECT", "concept"))

        # Properties (with or without the identifier signal)
        self.assertEqual(self.m.properties.get_property("RELATION"), bp._parse_filler(concept, "$RELATION", "property"))
        self.assertEqual(self.m.properties.get_property("RELATION"), bp._parse_filler(concept, "RELATION", "property"))

        # Text
        self.assertEqual("TEST", bp._parse_filler(concept, "TEST", "text"))

        # Comparators (floats and ints, 2 or 3 length)
        self.assertEqual((COMPARATOR.GTE, 1.0), bp._parse_filler(concept, ">=,1.0", "comparator"))
        self.assertEqual((COMPARATOR.GTE, 123), bp._parse_filler(concept, ">=,123", "comparator"))
        self.assertEqual((COMPARATOR.INCLUDE, 1.0, 2.0), bp._parse_filler(concept, "=>=<,1.0,2.0", "comparator"))
        self.assertEqual((COMPARATOR.INCLUDE, 123, 456), bp._parse_filler(concept, "=>=<,123,456", "comparator"))

        # Wildcards
        self.assertEqual(WILDCARD.ANYBOOL, bp._parse_filler(concept, "!AnyBool", "wildcard"))

        # Sets (must be private; with or without identifier signal)
        concept.private["SET.1"] = OSet(self.m, "SET.1", root=concept)
        self.assertEqual(concept.private["SET.1"], bp._parse_filler(concept, "@SET.1", "set"))
        self.assertEqual(concept.private["SET.1"], bp._parse_filler(concept, "SET.1", "set"))

        # Numbers (floats and ints)
        self.assertEqual(1.0, bp._parse_filler(concept, "1.0", "number"))
        self.assertEqual(123, bp._parse_filler(concept, "123", "number"))

    def test_guess_filler(self):
        app = MagicMock()
        app.static_folder = ""
        app.template_folder = ""
        app.agent = MagicMock()
        app.agent.memory = self.m
        bp = DEKADEAPIOntologyBlueprint(app)
        concept = self.m.ontology.concept("TEST")

        # Concepts are guessed by the presence of the @ symbol
        self.assertEqual(self.m.ontology.concept("OBJECT"), bp._guess_filler(concept, "THEME", "@OBJECT"))

        # Private concepts take precedence
        concept.private["OBJECT"] = Concept(self.m, "OBJECT", root=concept)
        self.assertEqual(concept.private["OBJECT"], bp._guess_filler(concept, "THEME", "@OBJECT"))

        # Properties are guessed by the presence of the $ symbol
        self.assertEqual(self.m.properties.get_property("RELATION"), bp._guess_filler(concept, "THEME", "$RELATION"))

        # Wildcards are guessed by the presence of the ! symbol
        self.assertEqual(WILDCARD.ANYBOOL, bp._guess_filler(concept, "ATTRIBUTE", "!AnyBool"))

        # Sets also use the @ symbol
        concept.private["SET.1"] = OSet(self.m, "SET.1", root=concept)
        self.assertEqual(concept.private["SET.1"], bp._guess_filler(concept, "THEME", "@SET.1"))

        # Comparators start with a comparator symbol pattern, and are comma separated (two or three elements)
        self.assertEqual((COMPARATOR.GTE, 1.0), bp._guess_filler(concept, "ATTRIBUTE", ">=,1.0"))
        self.assertEqual((COMPARATOR.GTE, 123), bp._guess_filler(concept, "ATTRIBUTE", ">=,123"))
        self.assertEqual((COMPARATOR.INCLUDE, 1.0, 2.0), bp._guess_filler(concept, "ATTRIBUTE", "=>=<,1.0,2.0"))
        self.assertEqual((COMPARATOR.INCLUDE, 123, 456), bp._guess_filler(concept, "ATTRIBUTE", "=>=<,123,456"))

        # Numbers are parsed if discovered
        self.assertEqual(1.0, bp._guess_filler(concept, "ATTRIBUTE", "1.0"))
        self.assertEqual(123, bp._guess_filler(concept, "ATTRIBUTE", "123"))

        # All other text is deemed to be a string
        self.assertEqual("TEST", bp._guess_filler(concept, "ATTRIBUTE", "TEST"))

