from collections import OrderedDict
from typing import List, Union
from unittest import TestCase
from unittest.mock import MagicMock
from leia.utils.formatting import FormatFromLISP, FormatToLISP


class FormatToLISPTestCase(TestCase):

    def setUp(self) -> None:
        self.sense_template = "({sense} {cat} {d} {ex} {com} {tmr} {syn} {sem} {out} {mp} {exbind} {exdep} {synonyms} {hyponyms} {types} {usewithtypes})"
        self.default_values = {
            "d": '(DEF "")',
            "ex": '(EX "")',
            "com": '(COMMENTS "")',
            "tmr": "(TMR-HEAD NIL)",
            "syn": "(SYN-STRUC ((X 1)))",
            "sem": "(SEM-STRUC (ALL))",
            "out": "(OUTPUT-SYNTAX NIL)",
            "mp": "(MEANING-PROCEDURES NIL)",
            "exbind": "(EXAMPLE-BINDINGS NIL)",
            "exdep": "(EXAMPLE-DEPS NIL)",
            "synonyms": "(SYNONYMS NIL)",
            "hyponyms": "(HYPONYMS NIL)",
            "types": "(TYPES NIL)",
            "usewithtypes": "(USE-WITH-TYPES NIL)",
        }

    def mockSense(
        self,
        sense: str,
        definition: str = "",
        example: str = "",
        comments: str = "",
        tmrhead: str = "NIL",
        synstruc: Union[OrderedDict, str] = "",
        semstruc: Union[OrderedDict, str] = "",
        outputsyntax: str = "NIL",
        meaningprocedures: Union[str, List[List[Union[str, List[str]]]]] = "NIL",
        examplebindings: str = "NIL",
        exampledeps: str = "NIL",
        synonyms: str = "NIL",
        hyponyms: str = "NIL",
        types: List[str] = None,
        use_with_types: List[str] = None,
        **kwargs
    ) -> OrderedDict:

        word = sense.split("-")[0]
        cat = "".join(i for i in sense.split("-")[1] if not i.isdigit())

        if isinstance(synstruc, str):
            if synstruc == "":
                synstruc = OrderedDict()

        if isinstance(semstruc, str):
            if semstruc == "":
                semstruc = OrderedDict()

        if types is None:
            types = []

        if use_with_types is None:
            use_with_types = []

        entry = OrderedDict(
            [
                ("SENSE", sense),
                ("WORD", word),
                ("CAT", cat),
                ("DEF", definition),
                ("EX", example),
                ("COMMENTS", comments),
                ("TMR-HEAD", tmrhead),
                ("SYN-STRUC", synstruc),
                ("SEM-STRUC", semstruc),
                ("OUTPUT-SYNTAX", outputsyntax),
                ("MEANING-PROCEDURES", meaningprocedures),
                ("EXAMPLE-BINDINGS", examplebindings),
                ("EXAMPLE-DEPS", exampledeps),
                ("SYNONYMS", synonyms),
                ("HYPONYMS", hyponyms),
                ("TYPES", types),
                ("USE-WITH-TYPES", use_with_types),
            ]
        )

        for key, value in kwargs.items():
            entry[key] = value

        return entry

    def test_word_to_lisp(self):
        word = "XYZ"
        senses = {
            "XYZ-N1": {"SENSE": "XYZ-N1"},
            "XYZ-N2": {"SENSE": "XYZ-N2"},
            "XYZ-N3": {"SENSE": "XYZ-N3"},
        }

        # The word and each sense are newline delimited
        formatter = FormatToLISP()
        formatter.sense_to_lisp = MagicMock(
            side_effect=lambda x: "%s-lisp" % x["SENSE"]
        )
        self.assertEqual(
            "(XYZ\nXYZ-N1-lisp\nXYZ-N2-lisp\nXYZ-N3-lisp)",
            formatter.word_to_lisp(word, senses),
        )

        # Some words must be quoted if they contain non-alpha non-underscore characters
        self.assertEqual('("XYZ123")', FormatToLISP().word_to_lisp("XYZ123", {}))

    def test_sense_to_lisp(self):
        # Simple case
        sense = self.mockSense(
            "TEST-N1",
            save=False,
            definition="Some definition",
            example="Some example",
            comments="Some comments",
            synstruc=OrderedDict({"X": 1}),
            semstruc="CONCEPT",
        )

        lisp = FormatToLISP().sense_to_lisp(sense)

        content = dict(self.default_values)
        content.update(
            {
                "sense": "TEST-N1",
                "cat": "(CAT N)",
                "d": '(DEF "%s")' % "Some definition",
                "ex": '(EX "%s")' % "Some example",
                "com": '(COMMENTS "%s")' % "Some comments",
                "syn": "(SYN-STRUC ((X 1)))",
                "sem": "(SEM-STRUC (CONCEPT))",
            }
        )

        expected = self.sense_template.format(**content)
        self.assertEqual(expected, lisp)

    def test_sense_to_lisp_with_quoted_name(self):
        sense = self.mockSense(
            "TEST!!!-N1",
            save=False,
            definition="Some definition",
            example="Some example",
            comments="Some comments",
            synstruc=OrderedDict({"X": 1}),
            semstruc="CONCEPT",
        )

        lisp = FormatToLISP().sense_to_lisp(sense)

        content = dict(self.default_values)
        content.update(
            {
                "sense": '"TEST!!!-N1"',
                "cat": "(CAT N)",
                "d": '(DEF "%s")' % "Some definition",
                "ex": '(EX "%s")' % "Some example",
                "com": '(COMMENTS "%s")' % "Some comments",
                "syn": "(SYN-STRUC ((X 1)))",
                "sem": "(SEM-STRUC (CONCEPT))",
            }
        )

        expected = self.sense_template.format(**content)
        self.assertEqual(expected, lisp)

    def test_cat_to_lisp(self):
        # There are two valid shapes to a CAT entry: a string, or a list of strings.

        self.assertEqual("(CAT N)", FormatToLISP().cat_to_lisp("N"))
        self.assertEqual("(CAT (N V))", FormatToLISP().cat_to_lisp(["N", "V"]))

    def test_tmr_head_to_lisp(self):
        # There are three valid shapes to a TMR-HEAD entry: NIL, an EMPTY string, or a VARIABLE.

        self.assertEqual("(TMR-HEAD NIL)", FormatToLISP().tmr_head_to_lisp(""))
        self.assertEqual("(TMR-HEAD NIL)", FormatToLISP().tmr_head_to_lisp("NIL"))
        self.assertEqual("(TMR-HEAD ^$VAR2)", FormatToLISP().tmr_head_to_lisp("^$VAR2"))

    def test_synstruc_to_lisp(self):
        # Syn-strucs have a recursive shape.  They are always a dictionary whose keys are strings, and whose values
        # are either: strings, numbers, lists, or another recursive dictionary.

        self.assertEqual(
            "(SYN-STRUC ((KEY VALUE)))",
            FormatToLISP().synstruc_to_lisp(OrderedDict({"KEY": "VALUE"})),
        )
        self.assertEqual(
            "(SYN-STRUC ((KEY VALUE) (OTHER 123)))",
            FormatToLISP().synstruc_to_lisp(
                OrderedDict({"KEY": "VALUE", "OTHER": 123})
            ),
        )
        self.assertEqual(
            "(SYN-STRUC ((KEY (V1 V2))))",
            FormatToLISP().synstruc_to_lisp(OrderedDict({"KEY": ["V1", "V2"]})),
        )
        self.assertEqual(
            "(SYN-STRUC ((KEY ((INNER1 ((INNER2A VALUE) (INNER2B 123)))))))",
            FormatToLISP().synstruc_to_lisp(
                OrderedDict({"KEY": {"INNER1": {"INNER2A": "VALUE", "INNER2B": 123}}})
            ),
        )

        # Special consideration: the database uses a -# moniker for repeating keys; these should be stripped.

        self.assertEqual(
            "(SYN-STRUC ((KEY V1) (KEY V2)))",
            FormatToLISP().synstruc_to_lisp(OrderedDict({"KEY": "V1", "KEY-1": "V2"})),
        )

        # Special consideration: the database records the extra ROOT field as ROOT-WORD; the "-WORD" should be stripped.

        self.assertEqual(
            "(SYN-STRUC ((ROOT ABC) (ROOT DEF)))",
            FormatToLISP().synstruc_to_lisp(
                OrderedDict({"ROOT": "ABC", "ROOT-WORD": "DEF"})
            ),
        )

    def test_semstruc_to_lisp(self):
        # Sem-strucs have a recursive shape.  They are either NIL, a single concept, or a dictionary whose keys are
        # strings, and whose values are either: strings, numbers, lists, or another recursive dictionary.  Sem-strucs
        # whose elements are lists will only have strings, numbers or further lists inside of them.
        # We also handle the unexpected input: empty string.

        self.assertEqual("(SEM-STRUC NIL)", FormatToLISP().semstruc_to_lisp(""))
        self.assertEqual("(SEM-STRUC NIL)", FormatToLISP().semstruc_to_lisp("NIL"))
        self.assertEqual(
            "(SEM-STRUC (CONCEPT))", FormatToLISP().semstruc_to_lisp("CONCEPT")
        )
        self.assertEqual(
            "(SEM-STRUC (CONCEPT (ABC DEF) (XYZ 123)))",
            FormatToLISP().semstruc_to_lisp({"CONCEPT": {"ABC": "DEF", "XYZ": 123}}),
        )
        self.assertEqual(
            "(SEM-STRUC (CONCEPT (ABC (VALUE ^$VAR1))))",
            FormatToLISP().semstruc_to_lisp({"CONCEPT": {"ABC": {"VALUE": "^$VAR1"}}}),
        )
        self.assertEqual(
            "(SEM-STRUC (CONCEPT1 (ABC 1)) (CONCEPT2 (ABC 2)))",
            FormatToLISP().semstruc_to_lisp(
                {"CONCEPT1": {"ABC": 1}, "CONCEPT2": {"ABC": 2}}
            ),
        )
        self.assertEqual(
            "(SEM-STRUC (CONCEPT (ABC (1 2 3))))",
            FormatToLISP().semstruc_to_lisp({"CONCEPT": {"ABC": [1, 2, 3]}}),
        )

        # Special consideration: the database uses a -# moniker for repeating keys; these should be stripped.

        self.assertEqual(
            "(SEM-STRUC (CONCEPT (ABC 1) (ABC 2)))",
            FormatToLISP().semstruc_to_lisp({"CONCEPT": {"ABC": 1, "ABC-1": 2}}),
        )

        # Special consideration: the database wraps top-level comparators in a CONSTRAINT field that must be removed.

        self.assertEqual(
            "(SEM-STRUC (> (VALUE REFSEM1.X) (VALUE REFSEM2.X)))",
            FormatToLISP().semstruc_to_lisp(
                {"CONSTRAINT": [">", ["VALUE", "REFSEM1.X"], ["VALUE", "REFSEM2.X"]]}
            ),
        )

    def test_output_syntax_to_lisp(self):
        # There are four valid shapes to an OUTPUT-SYNTAX entry: NIL, an EMPTY string, a part of speech string, or
        # a list of part of speech strings.

        self.assertEqual(
            "(OUTPUT-SYNTAX NIL)", FormatToLISP().output_syntax_to_lisp("")
        )
        self.assertEqual(
            "(OUTPUT-SYNTAX NIL)", FormatToLISP().output_syntax_to_lisp("NIL")
        )
        self.assertEqual(
            "(OUTPUT-SYNTAX INF-CL)", FormatToLISP().output_syntax_to_lisp("INF-CL")
        )
        self.assertEqual(
            "(OUTPUT-SYNTAX (INF-CL N))",
            FormatToLISP().output_syntax_to_lisp(["INF-CL", "N"]),
        )

    def test_meaning_procedures_to_lisp(self):
        # There are two valid shapes to a MEANING-PROCEDURE entry: NIL, and a LIST.  Each LIST entry is another LIST,
        # whose contents are atoms (strings or numbers) or recursive lists.  We handle EMTPY strings and EMPTY lists
        # as well (treated as NIL).  Any mention of a VARIABLE or REFSEM at any point is wrapped in additional
        # VALUE expression.

        self.assertEqual(
            "(MEANING-PROCEDURES NIL)", FormatToLISP().meaning_procedures_to_lisp("")
        )
        self.assertEqual(
            "(MEANING-PROCEDURES NIL)", FormatToLISP().meaning_procedures_to_lisp("NIL")
        )
        self.assertEqual(
            "(MEANING-PROCEDURES NIL)", FormatToLISP().meaning_procedures_to_lisp([])
        )
        self.assertEqual(
            "(MEANING-PROCEDURES (MPNAME))",
            FormatToLISP().meaning_procedures_to_lisp([["MPNAME"]]),
        )
        self.assertEqual(
            "(MEANING-PROCEDURES (MPNAME ARG1 2))",
            FormatToLISP().meaning_procedures_to_lisp([["MPNAME", "ARG1", 2]]),
        )
        self.assertEqual(
            "(MEANING-PROCEDURES (MPNAME ARG1 (REC1 2)))",
            FormatToLISP().meaning_procedures_to_lisp(
                [["MPNAME", "ARG1", ["REC1", 2]]]
            ),
        )
        self.assertEqual(
            "(MEANING-PROCEDURES (MPNAME ARG1) (MP2 ARG2))",
            FormatToLISP().meaning_procedures_to_lisp(
                [["MPNAME", "ARG1"], ["MP2", "ARG2"]]
            ),
        )
        self.assertEqual(
            "(MEANING-PROCEDURES (MPNAME (VALUE ^$VAR0)))",
            FormatToLISP().meaning_procedures_to_lisp([["MPNAME", "^$VAR0"]]),
        )
        self.assertEqual(
            "(MEANING-PROCEDURES (MPNAME (REC1 (VALUE REFSEM4))))",
            FormatToLISP().meaning_procedures_to_lisp(
                [["MPNAME", ["REC1", "REFSEM4"]]]
            ),
        )

    def test_example_bindings_to_lisp(self):
        # There are two valid shapes to EXAMPLE-BINDINGS: NIL, a list of strings or a list of lists of strings.
        # We also handle unexpected values.

        self.assertEqual(
            "(EXAMPLE-BINDINGS NIL)", FormatToLISP().example_bindings_to_lisp("")
        )
        self.assertEqual(
            "(EXAMPLE-BINDINGS NIL)", FormatToLISP().example_bindings_to_lisp("NIL")
        )
        self.assertEqual(
            "(EXAMPLE-BINDINGS NIL)", FormatToLISP().example_bindings_to_lisp([])
        )
        self.assertEqual(
            "(EXAMPLE-BINDINGS (A B 1 2))",
            FormatToLISP().example_bindings_to_lisp(["A", "B", 1, 2]),
        )
        self.assertEqual(
            "(EXAMPLE-BINDINGS (A B 1 2) (C D 3 4))",
            FormatToLISP().example_bindings_to_lisp(
                [["A", "B", 1, 2], ["C", "D", 3, 4]]
            ),
        )

    def test_example_deps_to_lisp(self):
        # There are two valid shapes to EXAMPLE-DEPS: NIL and a list of deps, each of which are a triple of strings
        # in a list format.  We also handle unexpected values.

        self.assertEqual("(EXAMPLE-DEPS NIL)", FormatToLISP().example_deps_to_lisp(""))
        self.assertEqual(
            "(EXAMPLE-DEPS NIL)", FormatToLISP().example_deps_to_lisp("NIL")
        )
        self.assertEqual("(EXAMPLE-DEPS NIL)", FormatToLISP().example_deps_to_lisp([]))
        self.assertEqual(
            "(EXAMPLE-DEPS ((TYPE A B) (XYZ 1 2)))",
            FormatToLISP().example_deps_to_lisp([["TYPE", "A", "B"], ["XYZ", 1, 2]]),
        )

    def test_synonyms_to_lisp(self):
        # There are two valid shapes to a SYNONYMS entry: NIL and a list.  Here we handle additional unexpected
        # values, an EMPTY string, a non-NIL string, and an EMPTY list.  Synonyms can be a number.

        self.assertEqual("(SYNONYMS NIL)", FormatToLISP().synonyms_to_lisp(""))
        self.assertEqual("(SYNONYMS NIL)", FormatToLISP().synonyms_to_lisp("NIL"))
        self.assertEqual("(SYNONYMS NIL)", FormatToLISP().synonyms_to_lisp([]))
        self.assertEqual("(SYNONYMS (WORDA))", FormatToLISP().synonyms_to_lisp("WORDA"))
        self.assertEqual(
            "(SYNONYMS (WORDA))", FormatToLISP().synonyms_to_lisp(["WORDA"])
        )
        self.assertEqual(
            "(SYNONYMS (WORDA WORDB))",
            FormatToLISP().synonyms_to_lisp(["WORDA", "WORDB"]),
        )
        self.assertEqual("(SYNONYMS (123))", FormatToLISP().synonyms_to_lisp([123]))

        # Special consideration: synonym entries must be escaped if they contain non-alpha, non-underscore characters.

        self.assertEqual(
            '(SYNONYMS ("X123"))', FormatToLISP().synonyms_to_lisp(["X123"])
        )

    def test_hyponyms_to_lisp(self):
        # There are two valid shapes to a HYPONYMS entry: NIL and a list.  Here we handle additional unexpected
        # values, an EMPTY string, a non-NIL string, and an EMPTY list.  Hyponyms can be a number.

        self.assertEqual("(HYPONYMS NIL)", FormatToLISP().hyponyms_to_lisp(""))
        self.assertEqual("(HYPONYMS NIL)", FormatToLISP().hyponyms_to_lisp("NIL"))
        self.assertEqual("(HYPONYMS NIL)", FormatToLISP().hyponyms_to_lisp([]))
        self.assertEqual("(HYPONYMS (WORDA))", FormatToLISP().hyponyms_to_lisp("WORDA"))
        self.assertEqual(
            "(HYPONYMS (WORDA))", FormatToLISP().hyponyms_to_lisp(["WORDA"])
        )
        self.assertEqual(
            "(HYPONYMS (WORDA WORDB))",
            FormatToLISP().hyponyms_to_lisp(["WORDA", "WORDB"]),
        )
        self.assertEqual("(HYPONYMS (123))", FormatToLISP().hyponyms_to_lisp([123]))

        # Special consideration: hyponym entries must be escaped if they contain non-alpha, non-underscore characters.

        self.assertEqual(
            '(HYPONYMS ("X123"))', FormatToLISP().hyponyms_to_lisp(["X123"])
        )

    def test_types_to_lisp(self):
        # There is one valid shape to a TYPES entry: a list (0 or more elements).  We also handle additional unexpected
        # values such as an EMPTY string and a NIL string.

        self.assertEqual("(TYPES NIL)", FormatToLISP().types_to_lisp(""))
        self.assertEqual("(TYPES NIL)", FormatToLISP().types_to_lisp("NIL"))
        self.assertEqual("(TYPES NIL)", FormatToLISP().types_to_lisp([]))
        self.assertEqual("(TYPES (T1))", FormatToLISP().types_to_lisp(["T1"]))
        self.assertEqual("(TYPES (T1 T2))", FormatToLISP().types_to_lisp(["T1", "T2"]))

    def test_use_with_types_to_lisp(self):
        # There is one valid shape to a USE-WITH-TYPES entry: a list (0 or more elements).  We also handle additional
        # unexpected values such as an EMPTY string and a NIL string.

        self.assertEqual(
            "(USE-WITH-TYPES NIL)", FormatToLISP().use_with_types_to_lisp("")
        )
        self.assertEqual(
            "(USE-WITH-TYPES NIL)", FormatToLISP().use_with_types_to_lisp("NIL")
        )
        self.assertEqual(
            "(USE-WITH-TYPES NIL)", FormatToLISP().use_with_types_to_lisp([])
        )
        self.assertEqual(
            "(USE-WITH-TYPES (T1))", FormatToLISP().use_with_types_to_lisp(["T1"])
        )
        self.assertEqual(
            "(USE-WITH-TYPES (T1 T2))",
            FormatToLISP().use_with_types_to_lisp(["T1", "T2"]),
        )


class ExampleTestCase(TestCase):

    def test_specific_examples(self):

        # YTTRIUM-N1
        self.assertEqual(
            "(SEM-STRUC (YTTRIUM))", FormatToLISP().semstruc_to_lisp("YTTRIUM")
        )
        # WORSEN-V3
        self.assertEqual(
            "(MEANING-PROCEDURES (FIX-CASE-ROLE (VALUE ^$VAR1) (VALUE ^$VAR0)))",
            FormatToLISP().meaning_procedures_to_lisp(
                [["FIX-CASE-ROLE", "^$VAR1", "^$VAR0"]]
            ),
        )
        # YOURSELVES-N2
        self.assertEqual(
            "(SEM-STRUC (MODALITY (TYPE SALIENCY) (VALUE 1) (SCOPE (VALUE ^$VAR1))))",
            FormatToLISP().semstruc_to_lisp(
                {
                    "MODALITY": {
                        "TYPE": "SALIENCY",
                        "VALUE": 1,
                        "SCOPE": {"VALUE": "^$VAR1"},
                    }
                }
            ),
        )
        # WRINKLE-V2
        self.assertEqual(
            "(SEM-STRUC (CHANGE-EVENT (THEME (VALUE ^$VAR1) (SEM (PAPER SEWING-MATERIAL))) (PRECONDITION (VALUE REFSEM1)) (EFFECT (VALUE REFSEM2))) (REFSEM1 (SMOOTHNESS (DOMAIN (VALUE ^$VAR1)))) (REFSEM2 (SMOOTHNESS (DOMAIN (VALUE ^$VAR1)))) (> (VALUE REFSEM1.RANGE) (VALUE REFSEM2.RANGE)))",
            FormatToLISP().semstruc_to_lisp(
                {
                    "CHANGE-EVENT": {
                        "THEME": {
                            "VALUE": "^$VAR1",
                            "SEM": ["PAPER", "SEWING-MATERIAL"],
                        },
                        "PRECONDITION": {"VALUE": "REFSEM1"},
                        "EFFECT": {"VALUE": "REFSEM2"},
                    },
                    "REFSEM1": {"SMOOTHNESS": {"DOMAIN": {"VALUE": "^$VAR1"}}},
                    "REFSEM2": {"SMOOTHNESS": {"DOMAIN": {"VALUE": "^$VAR1"}}},
                    "CONSTRAINT": [
                        ">",
                        ["VALUE", "REFSEM1.RANGE"],
                        ["VALUE", "REFSEM2.RANGE"],
                    ],
                }
            ),
        )
        # YOURSELF-N2
        self.assertEqual(
            "(SYN-STRUC ((N ((ROOT $VAR1) (CAT N) (ROOT YOU))) (N ((ROOT $VAR0) (CAT N) (TYPE REFL-PRO)))))",
            FormatToLISP().synstruc_to_lisp(
                OrderedDict(
                    {
                        "N": {"ROOT": "$VAR1", "CAT": "N", "ROOT-WORD": "YOU"},
                        "N-1": {"ROOT": "$VAR0", "CAT": "N", "TYPE": "REFL-PRO"},
                    }
                )
            ),
        )
        # BABY'S_ROOM-N1
        self.assertEqual(
            "(SEM-STRUC (BEDROOM (LOCATION-OF CRIB) (LOCATION-OF (VALUE REFSEM1))) (REFSEM1 (SLEEP (EXPERIENCER (VALUE REFSEM2)))) (REFSEM2 (HUMAN (AGE (< 3)))))",
            FormatToLISP().semstruc_to_lisp(
                {
                    "BEDROOM": {
                        "LOCATION-OF": "CRIB",
                        "LOCATION-OF-1": {"VALUE": "REFSEM1"},
                    },
                    "REFSEM1": {"SLEEP": {"EXPERIENCER": {"VALUE": "REFSEM2"}}},
                    "REFSEM2": {"HUMAN": {"AGE": ["<", 3]}},
                }
            ),
        )
        # ABOUT-PREP4
        self.assertEqual(
            "(SYN-STRUC ((ROOT $VAR1) (CAT (V N)) (PP ((ROOT $VAR0) (CAT PREP) (OBJ ((ROOT $VAR2) (CAT NP)))))))",
            FormatToLISP().synstruc_to_lisp(
                OrderedDict(
                    {
                        "ROOT": "$VAR1",
                        "CAT": ["V", "N"],
                        "PP": {
                            "ROOT": "$VAR0",
                            "CAT": "PREP",
                            "OBJ": {"ROOT": "$VAR2", "CAT": "NP"},
                        },
                    }
                )
            ),
        )
        # AND-CONJ20
        self.assertEqual(
            "(OUTPUT-SYNTAX (N V))", FormatToLISP().output_syntax_to_lisp(["N", "V"])
        )
        # FOR_EXAMPLE-CONJ1
        self.assertEqual(
            "(EXAMPLE-BINDINGS (THE OBJECT-1 *COMMA*-3 FOR_EXAMPLE-0 *COMMA*-4 THE EVENT-2 *COMMA*-5))",
            FormatToLISP().example_bindings_to_lisp(
                [
                    "THE",
                    "OBJECT-1",
                    "*COMMA*-3",
                    "FOR_EXAMPLE-0",
                    "*COMMA*-4",
                    "THE",
                    "EVENT-2",
                    "*COMMA*-5",
                ]
            ),
        )
        # VALENTINE'S_DAY-N1
        self.assertEqual(
            '(SYNONYMS ("SAINT_VALENTINE\'S_DAY" "ST._VALENTINE\'S_DAY"))',
            FormatToLISP().synonyms_to_lisp(
                ["SAINT_VALENTINE'S_DAY", "ST._VALENTINE'S_DAY"]
            ),
        )
        # THUNDER-V1
        self.assertEqual(
            "(SEM-STRUC (THUNDER) (^$VAR1 (NULL-SEM +)))",
            FormatToLISP().semstruc_to_lisp(
                {"THUNDER": {}, "^$VAR1": {"NULL-SEM": "+"}}
            ),
        )
        # *COLON*-PUNCT1
        self.assertEqual("(SEM-STRUC NIL)", FormatToLISP().semstruc_to_lisp(""))
        # *PERIOD*-PUNCT1
        self.assertEqual(
            "*PERIOD*-PUNCT1", FormatToLISP()._escape_sense_name("*PERIOD*-PUNCT1")
        )
        # 16_INCH_GUN-N1
        self.assertEqual(
            '"16_INCH_GUN-N1"', FormatToLISP()._escape_sense_name("16_INCH_GUN-N1")
        )


class FormatFromLISPTestCase(TestCase):

    def test_lisp_to_sense(self):
        formatter = FormatFromLISP()
        formatter.list_to_sense = MagicMock()

        formatter.lisp_to_sense("((A (B C)) (D E) F)")
        formatter.list_to_sense.assert_called_once_with(
            [["A", ["B", "C"]], ["D", "E"], "F"]
        )

    def test_list_to_sense(self):
        formatter = FormatFromLISP()

        formatter.parse_cat = MagicMock(side_effect=lambda x: "CAT-PARSED-%s" % x[1])
        formatter.parse_def = MagicMock(side_effect=lambda x: "DEF-PARSED-%s" % x[1])
        formatter.parse_ex = MagicMock(side_effect=lambda x: "EX-PARSED-%s" % x[1])
        formatter.parse_comments = MagicMock(
            side_effect=lambda x: "COMMENTS-PARSED-%s" % x[1]
        )
        formatter.parse_tmr_head = MagicMock(
            side_effect=lambda x: "TMR-HEAD-PARSED-%s" % x[1]
        )
        formatter.parse_syn_struc = MagicMock(
            side_effect=lambda x: "SYN-STRUC-PARSED-%s" % x[1]
        )
        formatter.parse_sem_struc = MagicMock(
            side_effect=lambda x: "SEM-STRUC-PARSED-%s" % x[1]
        )
        formatter.parse_output_syntax = MagicMock(
            side_effect=lambda x: "OUTPUT-SYNTAX-PARSED-%s" % x[1]
        )
        formatter.parse_meaning_procedures = MagicMock(
            side_effect=lambda x: "MEANING-PROCEDURES-PARSED-%s" % x[1]
        )
        formatter.parse_example_bindings = MagicMock(
            side_effect=lambda x: "EXAMPLE-BINDINGS-PARSED-%s" % x[1]
        )
        formatter.parse_example_deps = MagicMock(
            side_effect=lambda x: "EXAMPLE-DEPS-PARSED-%s" % x[1]
        )
        formatter.parse_synonyms = MagicMock(
            side_effect=lambda x: "SYNONYMS-PARSED-%s" % x[1]
        )
        formatter.parse_hyponyms = MagicMock(
            side_effect=lambda x: "HYPONYMS-PARSED-%s" % x[1]
        )
        formatter.parse_types = MagicMock(
            side_effect=lambda x: "TYPES-PARSED-%s" % x[1]
        )
        formatter.parse_use_with_types = MagicMock(
            side_effect=lambda x: "USE-WITH-TYPES-PARSED-%s" % x[1]
        )

        input = [
            "SENSE-N1",
            ["CAT", "TEST-CAT"],
            ["DEF", "TEST-DEF"],
            ["EX", "TEST-EX"],
            ["COMMENTS", "TEST-COMMENTS"],
            ["TMR-HEAD", "TEST-TMR-HEAD"],
            ["SYN-STRUC", "TEST-SYN-STRUC"],
            ["SEM-STRUC", "TEST-SEM-STRUC"],
            ["OUTPUT-SYNTAX", "TEST-OUTPUT-SYNTAX"],
            ["MEANING-PROCEDURES", "TEST-MEANING-PROCEDURES"],
            ["EXAMPLE-BINDINGS", "TEST-EXAMPLE-BINDINGS"],
            ["EXAMPLE-DEPS", "TEST-EXAMPLE-DEPS"],
            ["SYNONYMS", "TEST-SYNONYMS"],
            ["HYPONYMS", "TEST-HYPONYMS"],
            ["TYPES", "TEST-TYPES"],
            ["USE-WITH-TYPES", "TEST-USE-WITH-TYPES"],
        ]

        results = formatter.list_to_sense(input)
        self.assertEqual(
            {
                "SENSE": "SENSE-N1",
                "WORD": "SENSE",
                "CAT": "CAT-PARSED-TEST-CAT",
                "DEF": "DEF-PARSED-TEST-DEF",
                "EX": "EX-PARSED-TEST-EX",
                "COMMENTS": "COMMENTS-PARSED-TEST-COMMENTS",
                "TMR-HEAD": "TMR-HEAD-PARSED-TEST-TMR-HEAD",
                "SYN-STRUC": "SYN-STRUC-PARSED-TEST-SYN-STRUC",
                "SEM-STRUC": "SEM-STRUC-PARSED-TEST-SEM-STRUC",
                "OUTPUT-SYNTAX": "OUTPUT-SYNTAX-PARSED-TEST-OUTPUT-SYNTAX",
                "MEANING-PROCEDURES": "MEANING-PROCEDURES-PARSED-TEST-MEANING-PROCEDURES",
                "EXAMPLE-BINDINGS": "EXAMPLE-BINDINGS-PARSED-TEST-EXAMPLE-BINDINGS",
                "EXAMPLE-DEPS": "EXAMPLE-DEPS-PARSED-TEST-EXAMPLE-DEPS",
                "SYNONYMS": "SYNONYMS-PARSED-TEST-SYNONYMS",
                "HYPONYMS": "HYPONYMS-PARSED-TEST-HYPONYMS",
                "TYPES": "TYPES-PARSED-TEST-TYPES",
                "USE-WITH-TYPES": "USE-WITH-TYPES-PARSED-TEST-USE-WITH-TYPES",
            },
            results,
        )

        # Produce default values for any fields missing
        input = [
            "SENSE-N1",
        ]

        results = formatter.list_to_sense(input)
        self.assertEqual(
            {
                "SENSE": "SENSE-N1",
                "WORD": "SENSE",
                "CAT": "CAT-PARSED-",
                "DEF": "DEF-PARSED-",
                "EX": "EX-PARSED-",
                "COMMENTS": "COMMENTS-PARSED-",
                "TMR-HEAD": "TMR-HEAD-PARSED-NIL",
                "SYN-STRUC": "SYN-STRUC-PARSED-[]",
                "SEM-STRUC": "SEM-STRUC-PARSED-ALL",
                "OUTPUT-SYNTAX": "OUTPUT-SYNTAX-PARSED-NIL",
                "MEANING-PROCEDURES": "MEANING-PROCEDURES-PARSED-NIL",
                "EXAMPLE-BINDINGS": "EXAMPLE-BINDINGS-PARSED-NIL",
                "EXAMPLE-DEPS": "EXAMPLE-DEPS-PARSED-NIL",
                "SYNONYMS": "SYNONYMS-PARSED-NIL",
                "HYPONYMS": "HYPONYMS-PARSED-NIL",
                "TYPES": "TYPES-PARSED-[]",
                "USE-WITH-TYPES": "USE-WITH-TYPES-PARSED-[]",
            },
            results,
        )

    def test_list_key_to_value(self):
        formatter = FormatFromLISP()

        input = [["A", "B"], ["C", ["D", "E"]]]
        self.assertEqual(["A", "B"], formatter.list_key_to_value(input, "A"))
        self.assertEqual(["C", ["D", "E"]], formatter.list_key_to_value(input, "C"))
        self.assertEqual(["F", None], formatter.list_key_to_value(input, "F"))
        self.assertEqual(
            ["F", "DEFAULT"], formatter.list_key_to_value(input, "F", "DEFAULT")
        )

    def test_parse_cat(self):
        # CAT can be either a single string, or a list of strings

        self.assertEqual("N", FormatFromLISP().parse_cat(["CAT", "N"]))
        self.assertEqual(
            ["N", "PREP"], FormatFromLISP().parse_cat(["CAT", ["N", "PREP"]])
        )

    def test_parse_def(self):
        # DEF can only be a single string

        self.assertEqual(
            "A definition.", FormatFromLISP().parse_def(["DEF", "A definition."])
        )

    def test_parse_ex(self):
        # EX can only be a single string

        self.assertEqual(
            "An example.", FormatFromLISP().parse_def(["EX", "An example."])
        )

    def test_parse_comments(self):
        # COMMENTS can only be a single string

        self.assertEqual(
            "Some comments.", FormatFromLISP().parse_def(["COMMENTS", "Some comments."])
        )

    def test_parse_tmr_head(self):
        # TMR-HEAD can either be the NIL string or a single variable string

        self.assertEqual("NIL", FormatFromLISP().parse_tmr_head(["TMR-HEAD", "NIL"]))
        self.assertEqual(
            "$VAR1", FormatFromLISP().parse_tmr_head(["TMR-HEAD", "$VAR1"])
        )

    def test_parse_syn_struc(self):
        # SYN-STRUC must always a list (often recursive) that must be parsed into a dictionary.

        self.assertEqual(
            {"ROOT": "$VAR0", "CAT": "V"},
            FormatFromLISP().parse_syn_struc(
                ["SYN-STRUC", [["ROOT", "$VAR0"], ["CAT", "V"]]]
            ),
        )

        self.assertEqual(
            {"SUBJECT": {"ROOT": "$VAR2", "CAT": "NP"}},
            FormatFromLISP().parse_syn_struc(
                ["SYN-STRUC", [["SUBJECT", [["ROOT", "$VAR2"], ["CAT", "NP"]]]]]
            ),
        )

        # Certain fields can be a list, and in those cases, are not recursively parsed; e.g., CAT
        self.assertEqual(
            {"SUBJECT": {"ROOT": {"X": "ABC"}, "CAT": ["D", "E", "F"]}},
            FormatFromLISP().parse_syn_struc(
                [
                    "SYN-STRUC",
                    [["SUBJECT", [["ROOT", [["X", "ABC"]]], ["CAT", ["D", "E", "F"]]]]],
                ]
            ),
        )

    def test_parse_sem_struc(self):
        # SEM-STRUC a recursive list of strings.

        # (SEM-STRUC (OBJECT))
        self.assertEqual(
            "OBJECT", FormatFromLISP().parse_sem_struc(["SEM-STRUC", ["OBJECT"]])
        )

        # (SEM-STRUC (REFSEM1 (OBJECT)))
        self.assertEqual(
            {"REFSEM1": ["OBJECT"]},
            FormatFromLISP().parse_sem_struc(["SEM-STRUC", ["REFSEM1", ["OBJECT"]]]),
        )

        # (SEM-STRUC (ACQUIRE (AGENT (VALUE ^$VAR2)) (THEME (VALUE ^$VAR3))))
        self.assertEqual(
            {"ACQUIRE": {"AGENT": {"VALUE": "^$VAR2"}, "THEME": {"VALUE": "^$VAR3"}}},
            FormatFromLISP().parse_sem_struc(
                [
                    "SEM-STRUC",
                    [
                        "ACQUIRE",
                        ["AGENT", ["VALUE", "^$VAR2"]],
                        ["THEME", ["VALUE", "^$VAR3"]],
                    ],
                ]
            ),
        )

        # (SEM-STRUC (HUMAN (AGENT-OF (VALUE REFSEM1))) (REFSEM1 (ACQUIRE (THEME (VALUE ^$VAR2))))
        self.assertEqual(
            {
                "HUMAN": {"AGENT-OF": {"VALUE": "REFSEM1"}},
                "REFSEM1": {"ACQUIRE": {"THEME": {"VALUE": "^$VAR2"}}},
            },
            FormatFromLISP().parse_sem_struc(
                [
                    "SEM-STRUC",
                    ["HUMAN", ["AGENT-OF", ["VALUE", "REFSEM1"]]],
                    ["REFSEM1", ["ACQUIRE", ["THEME", ["VALUE", "^$VAR2"]]]],
                ]
            ),
        )

        # Certain content is presented as a list, and should stay that way; such as comparators
        # (SEM-STRUC (HUMAN (NOVELTY (> 0.7))))
        self.assertEqual(
            {"HUMAN": {"NOVELTY": [">", "0.7"]}},
            FormatFromLISP().parse_sem_struc(
                ["SEM-STRUC", ["HUMAN", ["NOVELTY", [">", "0.7"]]]]
            ),
        )

        # Some lex senses from the syntax will have multiple heads, of which one may be a concept
        # with no properties.
        # (SEM-STRUC (DOG) (^$VAR0 (RELATION (VALUE ^$VAR100))))

        self.assertEqual(
            {"DOG": {}, "^$VAR0": {"RELATION": {"VALUE": "^$VAR100"}}},
            FormatFromLISP().parse_sem_struc(
                ["SEM-STRUC", ["DOG"], ["^$VAR0", ["RELATION", ["VALUE", "^$VAR100"]]]]
            ),
        )

    def test_parse_output_syntax(self):
        # OUTPUT-SYNTAX can either be the NIL string, a single part of speech, or a list of strings; we also
        # handle an empty list.

        self.assertEqual(
            "NIL", FormatFromLISP().parse_output_syntax(["OUTPUT-SYNTAX", "NIL"])
        )
        self.assertEqual(
            "INF-CL", FormatFromLISP().parse_output_syntax(["OUTPUT-SYNTAX", "INF-CL"])
        )
        self.assertEqual(
            ["N", "V"],
            FormatFromLISP().parse_output_syntax(["OUTPUT-SYNTAX", ["N", "V"]]),
        )
        self.assertEqual(
            "NIL", FormatFromLISP().parse_output_syntax(["OUTPUT-SYNTAX", []])
        )

    def test_parse_meaning_procedures(self):
        # MEANING-PROCEDURES can either be the NIL string, or a list of list of strings; we also handle an empty list.

        self.assertEqual(
            "NIL",
            FormatFromLISP().parse_meaning_procedures(["MEANING-PROCEDURES", "NIL"]),
        )
        self.assertEqual(
            "NIL", FormatFromLISP().parse_meaning_procedures(["MEANING-PROCEDURES", []])
        )
        self.assertEqual(
            [["APPLY-MEANING", "^$VAR1", "^$VAR2"]],
            FormatFromLISP().parse_meaning_procedures(
                ["MEANING-PROCEDURES", ["APPLY-MEANING", "^$VAR1", "^$VAR2"]]
            ),
        )

    def test_parse_example_bindings(self):
        # EXAMPLE-BINDINGS can either be the NIL string, or a list of strings; we also handle an empty list.

        self.assertEqual(
            "NIL", FormatFromLISP().parse_example_bindings(["EXAMPLE-BINDINGS", "NIL"])
        )
        self.assertEqual(
            "NIL", FormatFromLISP().parse_example_bindings(["EXAMPLE-BINDINGS", []])
        )
        self.assertEqual(
            ["THE", "MAN", "HIT-1"],
            FormatFromLISP().parse_example_bindings(
                ["EXAMPLE-BINDINGS", ["THE", "MAN", "HIT-1"]]
            ),
        )

    def test_parse_example_deps(self):
        # EXAMPLE-DEPS can either be the NIL string, or a list of list of strings; we also handle an empty list.

        self.assertEqual(
            "NIL", FormatFromLISP().parse_example_deps(["EXAMPLE-DEPS", "NIL"])
        )
        self.assertEqual(
            "NIL", FormatFromLISP().parse_example_deps(["EXAMPLE-DEPS", []])
        )
        self.assertEqual(
            [["NSUBJ", "$VAR0", "$VAR1"], ["PREP", "$VAR0", "$VAR3"]],
            FormatFromLISP().parse_example_deps(
                [
                    "EXAMPLE-DEPS",
                    [["NSUBJ", "$VAR0", "$VAR1"], ["PREP", "$VAR0", "$VAR3"]],
                ]
            ),
        )

    def test_parse_synonyms(self):
        # SYNONYMS is either NIL or a list of strings; we also handle an empty list

        self.assertEqual("NIL", FormatFromLISP().parse_synonyms(["SYNONYMS", []]))
        self.assertEqual("NIL", FormatFromLISP().parse_synonyms(["SYNONYMS", "NIL"]))
        self.assertEqual(
            ["A", "B"], FormatFromLISP().parse_synonyms(["SYNONYMS", ["A", "B"]])
        )

    def test_parse_hyponyms(self):
        # HYPONYMS is either NIL or a list of strings; we also handle an empty list

        self.assertEqual("NIL", FormatFromLISP().parse_hyponyms(["HYPONYMS", []]))
        self.assertEqual("NIL", FormatFromLISP().parse_hyponyms(["HYPONYMS", "NIL"]))
        self.assertEqual(
            ["A", "B"], FormatFromLISP().parse_hyponyms(["HYPONYMS", ["A", "B"]])
        )

    def test_parse_types(self):
        # TYPES is either NIL or a list of type strings; we also handle an empty list

        self.assertEqual([], FormatFromLISP().parse_types(["TYPES", []]))
        self.assertEqual([], FormatFromLISP().parse_types(["TYPES", "NIL"]))
        self.assertEqual(
            ["A", "B"], FormatFromLISP().parse_types(["TYPES", ["A", "B"]])
        )

    def test_parse_use_with_types(self):
        # USE-WITH-TYPES is either NIL or a list of type strings; we also handle an empty list

        self.assertEqual(
            [], FormatFromLISP().parse_use_with_types(["USE-WITH-TYPES", []])
        )
        self.assertEqual(
            [], FormatFromLISP().parse_use_with_types(["USE-WITH-TYPES", "NIL"])
        )
        self.assertEqual(
            ["A", "B"],
            FormatFromLISP().parse_use_with_types(["USE-WITH-TYPES", ["A", "B"]]),
        )
