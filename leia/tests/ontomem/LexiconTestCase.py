from collections import OrderedDict
from leia.ontomem.lexicon import Lexicon, MeaningProcedure, SemStruc, Sense, SynStruc, Word
from leia.ontomem.memory import Memory
from unittest import TestCase
from unittest.mock import call, MagicMock, mock_open, patch

import json


class LexiconTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_word_uses_cache_first(self):
        test_word = Word(self.m, "test-word", contents={"name": "test-word", "senses": []})

        lex = Lexicon(self.m, "", load_now=False)
        lex.cache["test-word"] = test_word

        lex.load_word = MagicMock()
        lex.create_word = MagicMock()

        self.assertEqual(test_word, lex.word("test-word"))
        lex.load_word.assert_not_called()
        lex.create_word.assert_not_called()

    def test_word_creates_new_second(self):
        test_word = Word(self.m, "test-word", contents={"name": "test-word", "senses": []})

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
            "SYN-STRUC": {
                "ROOT": "$VAR0",
                "CAT": "N"
            },
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


class SenseTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

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
            "SYN-STRUC": {
                "ROOT": "$VAR0",
                "CAT": "N"
            },
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
        self.assertEqual(SynStruc(OrderedDict({
            "ROOT": "$VAR0",
            "CAT": "N"
        })), sense.synstruc)

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