from ontomem.lexicon import Lexicon, Sense, Word
from ontomem.memory import Memory
from unittest import TestCase
from unittest.mock import call, MagicMock, mock_open, patch

import json


class LexiconTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_word_uses_cache_first(self):
        test_word = Word(self.m, "test-word", contents={"name": "test-word", "senses": []})

        lex = Lexicon(self.m, "")
        lex.cache["test-word"] = test_word

        lex.load_word = MagicMock()
        lex.create_word = MagicMock()

        self.assertEqual(test_word, lex.word("test-word"))
        lex.load_word.assert_not_called()
        lex.create_word.assert_not_called()

    def test_word_lazy_loads_second(self):
        test_word = Word(self.m, "test-word", contents={"name": "test-word", "senses": []})

        lex = Lexicon(self.m, "")

        lex.load_word = MagicMock(return_value=test_word)
        lex.create_word = MagicMock()

        self.assertEqual(test_word, lex.word("test-word"))
        lex.load_word.assert_called_once_with("test-word")
        lex.create_word.assert_not_called()

    def test_word_creates_new_third(self):
        test_word = Word(self.m, "test-word", contents={"name": "test-word", "senses": []})

        lex = Lexicon(self.m, "")

        lex.load_word = MagicMock(return_value=None)
        lex.create_word = MagicMock(return_value=test_word)

        self.assertEqual(test_word, lex.word("test-word"))
        lex.load_word.assert_called_once_with("test-word")
        lex.create_word.assert_called_once_with("test-word")

    def test_load_word(self):
        test_word = Word(self.m, "test-word", contents={"name": "test-word", "senses": []})

        contents_dir = "some/contents/dir"
        lex = Lexicon(self.m, contents_dir)

        with patch("builtins.open", mock_open(read_data=json.dumps(test_word.contents))) as mo:
            value = lex.load_word("test-word")
            self.assertEqual(test_word, value)

            mo.assert_has_calls([
                call("%s/%s" % (contents_dir, "test-word.word"), "r"),
                call().__enter__(),
                call().read(),
                call().__exit__(None, None, None)
            ])

    def test_create_word(self):
        lex = Lexicon(self.m, "")

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


        lex = Lexicon(self.m, "")

        with self.assertRaises(Exception):
            lex.sense("MAN-N1")

        lex.cache["MAN"] = Word(self.m, "MAN", contents={
            "name": "MAN",
            "senses": {
                "MAN-N1": sense_contents
            }
        })

        self.assertEqual(Sense(self.m, "MAN-N1", contents=sense_contents), lex.sense("MAN-N1"))