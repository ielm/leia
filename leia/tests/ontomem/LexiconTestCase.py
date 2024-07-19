from collections import OrderedDict
from leia.ontomem.lexicon import Lexicon, MeaningProcedure, SemStruc, Sense, SynStruc, Word
from leia.ontomem.memory import Memory
from leia.tests.LEIATestCase import LEIATestCase
from unittest import skip, TestCase
from unittest.mock import MagicMock


class LexiconTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

    def test_word_uses_cache_first(self):
        test_word = Word(self.m, "test-word", contents={"name": "test-word", "senses": {}})

        lex = Lexicon(self.m, "", load_now=False)
        lex.cache["test-word"] = test_word

        lex.load_word = MagicMock()
        lex.create_word = MagicMock()

        self.assertEqual(test_word, lex.word("test-word"))
        lex.load_word.assert_not_called()
        lex.create_word.assert_not_called()

    def test_word_creates_new_second(self):
        test_word = Word(self.m, "test-word", contents={"name": "test-word", "senses": {}})

        lex = Lexicon(self.m, "", load_now=False)

        lex.create_word = MagicMock(return_value=test_word)

        self.assertEqual(test_word, lex.word("test-word"))
        lex.create_word.assert_called_once_with("test-word")

    def test_create_word(self):
        lex = Lexicon(self.m, "", load_now=False)

        self.assertEqual(Word(self.m, "test-word", contents={
            "name": "test-word",
            "senses": {}
        }), lex.create_word("test-word"))

    def test_sense(self):
        sense_contents = {
            "SENSE": "MAN-N1",
            "WORD": "MAN",
            "CAT": "N",
            "DEF": "male human being",
            "EX": "...",
            "COMMENTS": "...",
            "SYNONYMS": ["X", "Y", "Z"],
            "HYPONYMS": ["A", "B", "C"],
            "SYN-STRUC": [
                {"type": "root"}
            ],
            "SEM-STRUC": {
                "HUMAN": {
                    "GENDER": "MALE"
                }
            },
            "TMR-HEAD": None,
            "MEANING-PROCEDURES": [],
            "OUTPUT-SYNTAX": [],
            "EXAMPLE-DEPS": [],
            "EXAMPLE-BINDINGS": [],
            "TYPES": [],
            "USE-WITH-TYPES": []
        }


        lex = Lexicon(self.m, "", load_now=False)

        with self.assertRaises(Exception):
            lex.sense("MAN-N1")

        lex.cache["MAN"] = Word(self.m, "MAN", contents={
            "name": "MAN",
            "senses": {
                "MAN-N1": sense_contents
            }
        })

        self.assertEqual(Sense(self.m, "MAN-N1", contents=sense_contents), lex.sense("MAN-N1"))


class WordTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory()

    def test_senses(self):
        word = self.m.lexicon.word("test")
        self.assertEqual([], word.senses())

        s1 = Sense(self.m, "s1", contents=self.mockSense("s1"))
        s2 = Sense(self.m, "s2", contents=self.mockSense("s2"))

        word.add_sense(s1)
        self.assertEqual([s1], word.senses())

        word.add_sense(s2)
        self.assertEqual([s1, s2], word.senses())

    def test_senses_with_synonyms(self):
        word = self.m.lexicon.word("test")
        self.assertEqual([], word.senses())

        # Sanity check, senses locally defined will also be included
        local_sense = Sense(self.m, "localsense", contents=self.mockSense("localsense"))
        word.add_sense(local_sense)
        self.assertEqual([local_sense], word.senses())

        # Now add a sense to another word; it will not be included
        self.m.lexicon.word("other").add_sense(Sense(self.m, "notincluded", contents=self.mockSense("notincluded")))
        self.assertEqual([local_sense], word.senses())

        # Now add a sense to another word with "test" as a synonym; it will be included
        another = self.m.lexicon.word("another")
        syn_sense = Sense(self.m, "synsense", contents=self.mockSense("synsense", synonyms=["test"]))
        another.add_sense(syn_sense)
        self.assertEqual([local_sense, syn_sense], word.senses())

        # Synonyms can be filtered out
        self.assertEqual([local_sense], word.senses(include_synonyms=False))


class SenseTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

    def sample_sense_dict(self) -> dict:
        return {
            "SENSE": "MAN-N1",
            "WORD": "MAN",
            "CAT": "N",
            "DEF": "male human being",
            "EX": "...",
            "COMMENTS": "...",
            "SYNONYMS": ["X", "Y", "Z"],
            "HYPONYMS": ["A", "B", "C"],
            "SYN-STRUC": [
                {"type": "root"}
            ],
            "SEM-STRUC": {
                "HUMAN": {
                    "GENDER": "MALE"
                }
            },
            "TMR-HEAD": None,
            "MEANING-PROCEDURES": [["TEST-MP", "$VAR0", "$VAR1"]],
            "OUTPUT-SYNTAX": [],
            "EXAMPLE-DEPS": [],
            "EXAMPLE-BINDINGS": [],
            "TYPES": [],
            "USE-WITH-TYPES": []
        }

    def test_index_word(self):
        sense = Sense(self.m, "MAN-N1", contents=self.sample_sense_dict())
        self.assertEqual(self.m.lexicon.word("MAN"), sense.word)

    def test_index_pos(self):
        sense = Sense(self.m, "MAN-N1", contents=self.sample_sense_dict())
        self.assertEqual("N", sense.pos)

    def test_index_syn_struc(self):
        sense = Sense(self.m, "MAN-N1", contents=self.sample_sense_dict())
        self.assertEqual(SynStruc(contents=[{"type": "root"}]), sense.synstruc)

    def test_index_sem_struc(self):
        sense = Sense(self.m, "MAN-N1", contents=self.sample_sense_dict())
        self.assertEqual(SemStruc({
            "HUMAN": {
                "GENDER": "MALE"
            }
        }), sense.semstruc)

    def test_index_meaning_procedures(self):
        sense = Sense(self.m, "MAN-N1", contents=self.sample_sense_dict())
        self.assertEqual([MeaningProcedure(["TEST-MP", "$VAR0", "$VAR1"])], sense.meaning_procedures)

    @skip("To be removed; this relates to the LISP code exporting senses in the old format, which will no longer be used.")
    def test_parse_lisp(self):
        lisp = [
            "KICK--IMPERATIVE-V1",
            ["CAT", "V"],
            ["SYN-STRUC", [["ROOT", "$VAR0"], ["CAT", "V"], ["DIRECTOBJECT", [["ROOT", "$VAR2"], ["CAT", "N"]]]]],
            [
                "SEM-STRUC",
                ["KICK", ["THEME", ["VALUE", "^$VAR2"]], ["AGENT", "*HEARER*"]],
                ["REQUEST-ACTION", ["AGENT", "*SPEAKER*"], ["THEME", ["VALUE", "^$VAR0"]]],
                ["REFSEM1", ["APPLE"]],
                ["REFSEM2", ["APPLE", ["THEME", "SOMETHING"]]]
            ],
            [
                "MEANING-PROCEDURES",
                ["FIX-CASE-ROLE", ["VALUE", "^$VAR1"], ["VALUE", "^$VAR2"]]
            ]
        ]

        sense = Sense.parse_lisp(self.m, lisp)
        self.assertEqual("KICK--IMPERATIVE-V1", sense.id)
        self.assertEqual("V", sense.pos)
        self.assertEqual(SynStruc(OrderedDict([
            ("ROOT", "$VAR0"),
            ("CAT", "V"),
            ("DIRECTOBJECT", OrderedDict([
                ("ROOT", "$VAR2"),
                ("CAT", "N")
            ]))
        ])), sense.synstruc)
        self.assertEqual(SemStruc({
            "KICK": {
                "THEME": {
                    "VALUE": "^$VAR2",
                },
                "AGENT": "*HEARER*"
            },
            "REQUEST-ACTION": {
                "AGENT": "*SPEAKER*",
                "THEME": {
                    "VALUE": "^$VAR0"
                }
            },
            "REFSEM1": ["APPLE"],
            "REFSEM2": {
                "APPLE": {
                    "THEME": "SOMETHING"
                }
            }
        }), sense.semstruc)
        self.assertEqual([
            MeaningProcedure(["FIX-CASE-ROLE", ["VALUE", "^$VAR1"], ["VALUE", "^$VAR2"]])
        ], sense.meaning_procedures)

    def test_parse_lisp_missing_fields(self):
        # Lex senses that come directly from the syntax output (generated) may not have a
        # synstruc or meaning procedures field attached.

        lisp = [
            "KICK--IMPERATIVE-V1",
            ["CAT", "V"],
            [
                "SEM-STRUC",
                ["KICK", ["THEME", ["VALUE", "^$VAR2"]], ["AGENT", "*HEARER*"]],
                ["REQUEST-ACTION", ["AGENT", "*SPEAKER*"], ["THEME", ["VALUE", "^$VAR0"]]]
            ]
        ]

        sense = Sense.parse_lisp(self.m, lisp)
        self.assertEqual("KICK--IMPERATIVE-V1", sense.id)
        self.assertEqual("V", sense.pos)
        self.assertEqual(SynStruc(OrderedDict()), sense.synstruc)
        self.assertEqual(SemStruc({
            "KICK": {
                "THEME": {
                    "VALUE": "^$VAR2",
                },
                "AGENT": "*HEARER*"
            },
            "REQUEST-ACTION": {
                "AGENT": "*SPEAKER*",
                "THEME": {
                    "VALUE": "^$VAR0"
                }
            }
        }), sense.semstruc)
        self.assertEqual([], sense.meaning_procedures)


class SynStrucTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

    def test_index_root(self):
        # Root elements have no parameters
        synstruc = SynStruc(contents=[
            {"type": "root"}
        ])

        self.assertEqual([SynStruc.RootElement()], synstruc.elements)

    def test_index_token(self):
        # Token elements must define a lemma (set) and/or POS; they can have any arbitrary morphology fields.
        # No POS is represented by a None.
        synstruc = SynStruc(contents=[
            {"type": "token", "lemma": ["A", "B"], "pos": None, "morph": {"a": 1, "b": 2}}
        ])

        self.assertEqual([SynStruc.TokenElement({"A", "B"}, None, {"a": 1, "b": 2}, None, False)], synstruc.elements)

        # No lemmas is represented with an empty list.
        synstruc = SynStruc(contents=[
            {"type": "token", "lemma": [], "pos": "N", "morph": {}}
        ])

        self.assertEqual([SynStruc.TokenElement(set(), "N", {}, None, False)], synstruc.elements)

        # Both lemmas and POS can be present.
        synstruc = SynStruc(contents=[
            {"type": "token", "lemma": ["A", "B"], "pos": "N", "morph": {}}
        ])

        self.assertEqual([SynStruc.TokenElement({"A", "B"}, "N", {}, None, False)], synstruc.elements)

        # Variables and optionality flags can be present but don't need to be.
        synstruc = SynStruc(contents=[
            {"type": "token", "lemma": ["A"], "pos": None, "morph": {}, "var": 3, "opt": True}
        ])

        self.assertEqual([SynStruc.TokenElement({"A"}, None, {}, 3, True)], synstruc.elements)

    def test_index_dependency(self):
        # Dependencies must have a type.
        synstruc = SynStruc(contents=[
            {"type": "dependency", "deptype": "subject"}
        ])

        self.assertEqual([SynStruc.DependencyElement("subject", None, None, None, False)], synstruc.elements)

        # Dependencies can specify a governor or dependent.
        synstruc = SynStruc(contents=[
            {"type": "dependency", "deptype": "subject", "gov": 1, "dep": 2}
        ])

        self.assertEqual([SynStruc.DependencyElement("subject", 1, 2, None, False)], synstruc.elements)

        # Dependencies can specify a variable or optionality flag.
        synstruc = SynStruc(contents=[
            {"type": "dependency", "deptype": "subject", "var": 3, "opt": True}
        ])

        self.assertEqual([SynStruc.DependencyElement("subject", None, None, 3, True)], synstruc.elements)

    def test_index_constituency(self):
        # Constituencies must have a type; they can have no children.
        synstruc = SynStruc(contents=[
            {"type": "constituency", "contype": "VP", "children": []}
        ])

        self.assertEqual([SynStruc.ConstituencyElement("VP", [], None, False)], synstruc.elements)

        # Constituencies may have a variable or optionality flag.
        synstruc = SynStruc(contents=[
            {"type": "constituency", "contype": "VP", "children": [], "var": 3, "opt": True}
        ])

        self.assertEqual([SynStruc.ConstituencyElement("VP", [], 3, True)], synstruc.elements)

        # Constituencies can have other constituencies as children.
        synstruc = SynStruc(contents=[
            {"type": "constituency", "contype": "VP", "children": [
                {"type": "constituency", "contype": "NP", "children": []}
            ]}
        ])

        self.assertEqual([SynStruc.ConstituencyElement("VP", [
            SynStruc.ConstituencyElement("NP", [], None, False)
        ], None, False)], synstruc.elements)

        # Constituencies as children can be recursive.
        synstruc = SynStruc(contents=[
            {"type": "constituency", "contype": "VP", "children": [
                {"type": "constituency", "contype": "NP", "children": [
                    {"type": "constituency", "contype": "N", "children": []}
                ]}
            ]}
        ])

        self.assertEqual([SynStruc.ConstituencyElement("VP", [
            SynStruc.ConstituencyElement("NP", [
                SynStruc.ConstituencyElement("N", [], None, False)
            ], None, False)
        ], None, False)], synstruc.elements)

        # Constituencies can have tokens as children.
        synstruc = SynStruc(contents=[
            {"type": "constituency", "contype": "VP", "children": [
                {"type": "token", "lemma": {"BE"}, "pos": None, "morph": {}}
            ]}
        ])

        self.assertEqual([SynStruc.ConstituencyElement("VP", [
            SynStruc.TokenElement({"BE"}, None, {}, None, False)
        ], None, False)], synstruc.elements)

        # Constituencies can have multiple children.
        synstruc = SynStruc(contents=[
            {"type": "constituency", "contype": "VP", "children": [
                {"type": "token", "lemma": {"BE"}, "pos": None, "morph": {}},
                {"type": "token", "lemma": {"AT"}, "pos": None, "morph": {}},
            ]}
        ])

        self.assertEqual([SynStruc.ConstituencyElement("VP", [
            SynStruc.TokenElement({"BE"}, None, {}, None, False),
            SynStruc.TokenElement({"AT"}, None, {}, None, False),
        ], None, False)], synstruc.elements)

    def test_index_multiple(self):
        synstruc = SynStruc(contents=[
            {"type": "token", "lemma": ["A"], "pos": None, "morph": {}},
            {"type": "token", "lemma": ["B"], "pos": None, "morph": {}},
        ])

        self.assertEqual([
            SynStruc.TokenElement({"A"}, None, {}, None, False),
            SynStruc.TokenElement({"B"}, None, {}, None, False),
        ], synstruc.elements)

    def test_element_for_variable(self):
        # No match returns None
        synstruc = SynStruc()
        self.assertIsNone(synstruc.element_for_variable(1))

        # Root elements are always variable 0
        synstruc = SynStruc(contents=[
            {"type": "root"}
        ])
        self.assertEqual(synstruc.elements[0], synstruc.element_for_variable(0))

        # Token elements can contain a variable
        synstruc = SynStruc(contents=[
            {"type": "root"},
            {"type": "token", "lemma": ["A"], "pos": "N", "morph": {}, "var": 3}
        ])
        self.assertEqual(synstruc.elements[1], synstruc.element_for_variable(3))

        # Dependency elements can contain a variable
        synstruc = SynStruc(contents=[
            {"type": "root"},
            {"type": "dependency", "deptype": "NSUBJ", "var": 3}
        ])
        self.assertEqual(synstruc.elements[1], synstruc.element_for_variable(3))

        # Constituency elements can contain a variable
        synstruc = SynStruc(contents=[
            {"type": "root"},
            {"type": "constituency", "contype": "NP", "children": [], "var": 3}
        ])
        self.assertEqual(synstruc.elements[1], synstruc.element_for_variable(3))

        # Constituency elements can recursively contain other elements with variables
        synstruc = SynStruc(contents=[
            {"type": "root"},
            {"type": "constituency", "contype": "VP", "children": [
                {"type": "constituency", "contype": "NP", "children": [
                    {"type": "token", "lemma": ["A"], "pos": "N", "morph": {}, "var": 4}
                ], "var": 2},
                {"type": "token", "lemma": ["A"], "pos": "N", "morph": {}, "var": 6}
            ]}
        ])
        self.assertEqual(synstruc.elements[1].children[0], synstruc.element_for_variable(2))
        self.assertEqual(synstruc.elements[1].children[0].children[0], synstruc.element_for_variable(4))
        self.assertEqual(synstruc.elements[1].children[1], synstruc.element_for_variable(6))