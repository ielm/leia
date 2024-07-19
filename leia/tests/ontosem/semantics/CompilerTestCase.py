from leia.ontomem.lexicon import Lexicon, SemStruc
from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Ontology
from leia.ontomem.properties import Property
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.semantics.candidate import Candidate, Constraint
from leia.ontosem.semantics.compiler import SemanticCompiler
from leia.ontosem.semantics.tmr import TMRInstance
from leia.ontosem.syntax.results import SenseMap, SynMap, Syntax, Word
from leia.tests.LEIATestCase import LEIATestCase
from unittest.mock import call, MagicMock


class SemanticCompilerTestCase(LEIATestCase):

    def setUp(self):
        self.config = OntoSemConfig()
        self.m = self.config.memory()

    def test_run(self):
        # Run should expand all candidates, process each, and yield the results.

        synmap = SynMap([])
        syntax = Syntax([], synmap, [], "", "", [], [], [])

        c1 = Candidate(self.m)
        c2 = Candidate(self.m)

        analyzer = SemanticCompiler(OntoSemConfig())

        analyzer.expand_candidates = MagicMock()
        analyzer.expand_candidates.return_value = iter([c1, c2])
        analyzer.process_candidate = MagicMock()

        results = list(analyzer.run(syntax))

        analyzer.expand_candidates.assert_called_once_with(synmap)
        analyzer.process_candidate.assert_has_calls([
            call(c1),
            call(c2),
        ])

        self.assertEqual([c1, c2], results)

    def test_expand_candidates(self):

        sm0_N1 = SenseMap(Word.basic(0), "S0-N1", {"$VAR0": 0}, 0.5)
        sm0_N2 = SenseMap(Word.basic(0), "S0-N2", {"$VAR0": 0}, 0.5)
        sm1_V1 = SenseMap(Word.basic(1), "S1-V1", {"$VAR0": 0}, 0.5)
        sm1_V2 = SenseMap(Word.basic(1), "S1-V2", {"$VAR0": 0}, 0.5)
        sm1_V3 = SenseMap(Word.basic(1), "S1-V3", {"$VAR0": 0}, 0.5)
        sm2_N1 = SenseMap(Word.basic(2), "S2-N1", {"$VAR0": 0}, 0.5)
        sm2_N2 = SenseMap(Word.basic(2), "S2-N2", {"$VAR0": 0}, 0.5)
        sm2_N3 = SenseMap(Word.basic(2), "S2-N3", {"$VAR0": 0}, 0.5)

        synmap = SynMap([
            [sm0_N1, sm0_N2],
            [sm1_V1, sm1_V2, sm1_V3],
            [sm2_N1, sm2_N2, sm2_N3],
        ])

        candidates = list(SemanticCompiler(self.config).expand_candidates(synmap))

        self.assertEqual([
            Candidate(self.m, sm0_N1, sm1_V1, sm2_N1),
            Candidate(self.m, sm0_N1, sm1_V1, sm2_N2),
            Candidate(self.m, sm0_N1, sm1_V1, sm2_N3),
            Candidate(self.m, sm0_N1, sm1_V2, sm2_N1),
            Candidate(self.m, sm0_N1, sm1_V2, sm2_N2),
            Candidate(self.m, sm0_N1, sm1_V2, sm2_N3),
            Candidate(self.m, sm0_N1, sm1_V3, sm2_N1),
            Candidate(self.m, sm0_N1, sm1_V3, sm2_N2),
            Candidate(self.m, sm0_N1, sm1_V3, sm2_N3),
            Candidate(self.m, sm0_N2, sm1_V1, sm2_N1),
            Candidate(self.m, sm0_N2, sm1_V1, sm2_N2),
            Candidate(self.m, sm0_N2, sm1_V1, sm2_N3),
            Candidate(self.m, sm0_N2, sm1_V2, sm2_N1),
            Candidate(self.m, sm0_N2, sm1_V2, sm2_N2),
            Candidate(self.m, sm0_N2, sm1_V2, sm2_N3),
            Candidate(self.m, sm0_N2, sm1_V3, sm2_N1),
            Candidate(self.m, sm0_N2, sm1_V3, sm2_N2),
            Candidate(self.m, sm0_N2, sm1_V3, sm2_N3),
        ], candidates)

    def test_process_candidate(self):
        # Check that the candidate is passed through the pipeline.

        candidate = Candidate(self.m)

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.generate_frames = MagicMock()
        analyzer.bind_variables = MagicMock()
        analyzer.populate_frames = MagicMock()
        analyzer.redirect_null_sem_relations = MagicMock()
        analyzer.remove_null_sems = MagicMock()
        analyzer.fix_inverses = MagicMock()
        analyzer.build_mp_frames = MagicMock()

        analyzer.process_candidate(candidate)

        analyzer.generate_frames.assert_called_once_with(candidate)
        analyzer.bind_variables.assert_called_once_with(candidate)
        analyzer.populate_frames.assert_called_once_with(candidate)
        analyzer.redirect_null_sem_relations.assert_called_once_with(candidate)
        analyzer.remove_null_sems.assert_called_once_with(candidate)
        analyzer.fix_inverses.assert_called_once_with(candidate)
        analyzer.build_mp_frames.assert_called_once_with(candidate)

    def test_generate_frames(self):
        # Add three senses to the lexicon, and connect sense maps to them.
        # Verify:
        #   1) Head concepts are used to make frames
        #   2) Sub concepts are used to make frames
        #   3) Refsems are used to make frames
        #   4) Variables that act as heads are *not* used to make frames, but any unbound variable's properties are
        #   5) All frames are indexed, and have their resolution ids added locally

        lexicon = Lexicon(self.m, "")

        s1 = self.mockSense("TEST-T1", semstruc={
            "EVENT": {"RELATION": "$VAR0"},
            "REFSEM1": {"HUMAN": {"AGE": 50}},
            "HUMAN": {"AGE": 30},
            "REFSEM2": {"AUTOMOBILE": {"COLOR": "RED"}}
        })

        s2 = self.mockSense("TEST-T2", semstruc={
            "EVENT": {"RELATION": "$VAR0"},
            "^$VAR1": {"THING": "HUMAN", "AGE": 50},
            "^$VAR2": {"COLOR": "red", "AGENT": {"VALUE": "^$VAR3"}},
        })

        s3 = self.mockSense("TEST-T3", semstruc={
            "^$VAR4": {"THING": "HUMAN", "AGE": 50},
        })

        lexicon.word("TEST").add_sense(s1)
        lexicon.word("TEST").add_sense(s2)
        lexicon.word("TEST").add_sense(s3)

        sm1 = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)
        sm2 = SenseMap(Word.basic(1), "TEST-T2", {"$VAR1": 123}, 0.5)
        sm3 = SenseMap(Word.basic(2), "TEST-T3", {"$VAR4": None}, 0.5)

        candidate = Candidate(self.m, sm1, sm2, sm3)

        analyzer = SemanticCompiler(OntoSemConfig(), lexicon=lexicon)
        frames = list(analyzer.generate_frames(candidate))

        self.assertEqual([
            ("EVENT.1", {"0.HEAD"}),
            ("HUMAN.1", {"0.SUB.1"}),
            ("HUMAN.2", {"0.REFSEM.1"}),
            ("AUTOMOBILE.1", {"0.REFSEM.2"}),
            ("EVENT.2", {"1.HEAD"}),
            ("COLOR.1", {"1.VAR.2.COLOR"}),
            ("AGENT.1", {"1.VAR.2.AGENT"}),
            ("THING.1", {"2.VAR.4.THING", "2.HEAD"}),
            ("AGE.1", {"2.VAR.4.AGE"}),
        ], list(map(lambda f: (f.id(), f.resolutions), frames)))

        self.assertEqual("EVENT.1", candidate.resolve(0, SemStruc.Head()).id())
        self.assertEqual("EVENT.2", candidate.resolve(1, SemStruc.Head()).id())
        self.assertEqual("HUMAN.1", candidate.resolve(0, SemStruc.Sub(1)).id())
        self.assertEqual("HUMAN.2", candidate.resolve(0, SemStruc.RefSem(1)).id())
        self.assertEqual("AUTOMOBILE.1", candidate.resolve(0, SemStruc.RefSem(2)).id())
        self.assertEqual("COLOR.1", candidate.resolve(1, SemStruc.Property(2, "COLOR")).id())
        self.assertEqual("AGENT.1", candidate.resolve(1, SemStruc.Property(2, "AGENT")).id())
        self.assertEqual("THING.1", candidate.resolve(2, SemStruc.Property(4, "THING")).id())
        self.assertEqual("THING.1", candidate.resolve(2, SemStruc.Head()).id())
        self.assertEqual("AGE.1", candidate.resolve(2, SemStruc.Property(4, "AGE")).id())

    def test_bind_variables(self):
        # All variables mentioned in each sense mapping in the candidate's synmap should be resolved
        # to the existing frames.  If a variable is bound to a frame that does not exist, skip it.

        f0 = TMRInstance(self.m, "TEST", 1)
        f1 = TMRInstance(self.m, "TEST", 2)
        f7 = TMRInstance(self.m, "TEST", 3)

        sm1 = SenseMap(Word.basic(0), "TEST-T1", {"$VAR3": 0, "$VAR1": 1}, 0.5)
        sm2 = SenseMap(Word.basic(1), "TEST-T2", {"$VAR3": 1, "$VAR2": 7}, 0.5)
        sm3 = SenseMap(Word.basic(7), "TEST-T3", {"$VAR9": 9}, 0.5)                 # Word 9 does not exist, this will be skipped.

        candidate = Candidate(self.m, sm1, sm2, sm3)

        candidate.bind(0, SemStruc.Head("TEST", {}), f0)
        candidate.bind(1, SemStruc.Head("TEST", {}), f1)
        candidate.bind(7, SemStruc.Head("TEST", {}), f7)

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.bind_variables(candidate)

        self.assertEqual(f0, candidate.resolve(0, SemStruc.Variable(0)))
        self.assertEqual(f0, candidate.resolve(0, SemStruc.Variable(3)))
        self.assertEqual(f1, candidate.resolve(0, SemStruc.Variable(1)))
        self.assertEqual(f1, candidate.resolve(1, SemStruc.Variable(0)))
        self.assertEqual(f1, candidate.resolve(1, SemStruc.Variable(3)))
        self.assertEqual(f7, candidate.resolve(1, SemStruc.Variable(2)))
        self.assertEqual(f7, candidate.resolve(7, SemStruc.Variable(0)))

        self.assertEqual({"0.VAR.0", "0.VAR.3"}, f0.resolutions)
        self.assertEqual({"0.VAR.1", "1.VAR.0", "1.VAR.3"}, f1.resolutions)
        self.assertEqual({"1.VAR.2", "7.VAR.0"}, f7.resolutions)

    def test_populate_frames(self):
        # Verify that all elements of all words are populated; the order of the elements within a word doesn't
        # matter, but the order of the words does (most bindings first).

        # Create a lexicon with two senses; each semstruc has a head and a single sub element
        lexicon = Lexicon(Memory("", "", ""), "")

        s1 = self.mockSense("TEST-T1", semstruc={
            "HEAD": {"head1": "content"},
            "SUB": {"sub1": "content"}
        })

        s2 = self.mockSense("TEST-T2", semstruc={
            "HEAD": {"head2": "content"},
            "^$VAR1": {"ABC": "content"}
        })

        lexicon.word("TEST").add_sense(s1)
        lexicon.word("TEST").add_sense(s2)

        # Create a candidate with two sense maps; word 0 points to TEST-T1 and word 1 points to TEST-T2.
        # The candidate has already bound 0.HEAD, 0.SUB.1, 1.HEAD, and 1.VAR.1.ABC to some frames.
        # (Note that VAR1 is unbound, so its properties evoke as frames.)
        sm1 = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)
        sm2 = SenseMap(Word.basic(1), "TEST-T2", {"$VAR1": None}, 0.5)

        f1 = TMRInstance(self.m, "TEST", 1)
        f2 = TMRInstance(self.m, "TEST", 2)
        f3 = TMRInstance(self.m, "TEST", 3)
        f4 = TMRInstance(self.m, "TEST", 4)

        candidate = Candidate(self.m, sm1, sm2)
        candidate.bind(0, SemStruc.Head(), f1)
        candidate.bind(0, SemStruc.Sub(1), f2)
        candidate.bind(1, SemStruc.Head(), f3)
        candidate.bind(1, SemStruc.Property(1, "ABC"), f4)

        # Mock the words_by_binding_count function on the candidate to return sm1 and sm2 in that order
        candidate.words_by_binding_count = MagicMock()
        candidate.words_by_binding_count.return_value = [sm1, sm2]

        # The analyzer must use the special lexicon; mock the populate_*_properties functions so we can test the calls made to them.
        analyzer = SemanticCompiler(OntoSemConfig(), lexicon=lexicon)
        analyzer.populate_semantic_properties = MagicMock()
        analyzer.populate_syntactic_properties = MagicMock()

        # Run the method.
        analyzer.populate_frames(candidate)

        # We expect a particular set of calls in a particular order to the populate_*_frames functions:
        analyzer.populate_semantic_properties.assert_has_calls([
            call(f1, sm1, SemStruc.Head("HEAD", {"head1": "content"}), candidate),
            call(f2, sm1, SemStruc.Sub(1, "SUB", {"sub1": "content"}), candidate),
            call(f3, sm2, SemStruc.Head("HEAD", {"head2": "content"}), candidate),
            call(f4, sm2, SemStruc.Property(1, "ABC", "content"), candidate),
        ])

        # Only HEAD elements are passed to the populate_syntactic_frames function:
        analyzer.populate_syntactic_properties.assert_has_calls([
            call(f1, sm1, SemStruc.Head("HEAD", {"head1": "content"}), candidate),
            call(f3, sm2, SemStruc.Head("HEAD", {"head2": "content"}), candidate),
        ])

    def test_populate_semantic_properties(self):
        candidate = Candidate(self.m)
        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)
        element = SemStruc.Head("TEST", {
            "AGENT": "HUMAN",
            "COLOR": "RED",
            "TIME": [">", "FIND-ANCHOR-TIME"]
        })

        self.assertEqual([], frame.fillers("AGENT"))
        self.assertEqual([], frame.fillers("COLOR"))
        self.assertEqual([], frame.fillers("SIZE"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.resolve_embedded_semstruc = MagicMock(side_effect=analyzer.resolve_embedded_semstruc)
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual(["HUMAN"], frame.fillers("AGENT"))
        self.assertEqual(["RED"], frame.fillers("COLOR"))
        self.assertEqual([[">", "FIND-ANCHOR-TIME"]], frame.fillers("TIME"))

        analyzer.resolve_embedded_semstruc.assert_called_once_with([">", "FIND-ANCHOR-TIME"], sense_map, candidate)

    def test_populate_semantic_properties_as_refsem(self):
        # If the element itself is a refsem, the inner head needs to be extracted and used

        candidate = Candidate(self.m)
        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)
        element = SemStruc.RefSem(1, SemStruc({
            "HEAD": {
                "AGENT": "HUMAN",
                "COLOR": "RED",
                "TIME": [">", "FIND-ANCHOR-TIME"]
            }
        }))

        self.assertEqual([], frame.fillers("AGENT"))
        self.assertEqual([], frame.fillers("COLOR"))
        self.assertEqual([], frame.fillers("SIZE"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual(["HUMAN"], frame.fillers("AGENT"))
        self.assertEqual(["RED"], frame.fillers("COLOR"))
        self.assertEqual([[">", "FIND-ANCHOR-TIME"]], frame.fillers("TIME"))

    def test_populate_semantic_properties_with_refsems(self):
        # Refsems found in the fillers need to be resolved

        candidate = Candidate(self.m)

        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)
        element = SemStruc.Head("TEST", {
            "AGENT": "REFSEM1",
        })

        f1 = TMRInstance(self.m, "REF", 1)
        f2 = TMRInstance(self.m, "REF", 2)

        candidate.bind(0, SemStruc.RefSem(1), f1)   # This is REFSEM1 in word 1 (the word that is currently being populated)
        candidate.bind(1, SemStruc.RefSem(1), f2)   # This is REFSEM1 in word 2 (this should be ignored; it is not the correct binding)

        self.assertEqual([], frame.fillers("AGENT"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual([f1.id()], frame.fillers("AGENT"))

    def test_populate_semantic_properties_with_refsems_and_dot_notation(self):
        # Refsems found in the fillers with dot notation need to be partially resolved

        candidate = Candidate(self.m)

        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)
        element = SemStruc.Head("TEST", {
            "AGENT": "REFSEM1.THEME",
        })

        f1 = TMRInstance(self.m, "REF", 1)
        f2 = TMRInstance(self.m, "REF", 2)

        candidate.bind(0, SemStruc.RefSem(1), f1)  # This is REFSEM1 in word 1 (the word that is currently being populated)
        candidate.bind(1, SemStruc.RefSem(1), f2)  # This is REFSEM1 in word 2 (this should be ignored; it is not the correct binding)

        self.assertEqual([], frame.fillers("AGENT"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual(["%s" % f1.id() + "?THEME"], frame.fillers("AGENT"))

    def test_populate_semantic_properties_as_variable(self):
        # If the element itself is a variable, resolve it and then populate it

        candidate = Candidate(self.m)
        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {
            "$VAR1": 4,  # This variable points to word 4, and is the variable found in the semstruc
        }, 0.5)

        element = SemStruc.Variable(1, {
            "AGENT": "HUMAN",
            "COLOR": "RED",
            "TIME": [">", "FIND-ANCHOR-TIME"]
        })

        candidate.bind(0, SemStruc.Variable(1), frame)  # This is the binding for VAR1 in word 0, pointing to the head frame for word 4

        self.assertEqual([], frame.fillers("AGENT"))
        self.assertEqual([], frame.fillers("COLOR"))
        self.assertEqual([], frame.fillers("SIZE"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual(["HUMAN"], frame.fillers("AGENT"))
        self.assertEqual(["RED"], frame.fillers("COLOR"))
        self.assertEqual([[">", "FIND-ANCHOR-TIME"]], frame.fillers("TIME"))

    def test_populate_semantic_properties_with_variables(self):
        # Variables found in the fillers need to be resolved

        candidate = Candidate(self.m)

        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {
            "$VAR1": 4,     # This variable points to word 4, and is found in the semstruc
            "$VAR2": 5,     # This variable points to word 5, and is found in the semstruc
            "$VAR3": 6,     # This variable should be ignored
        }, 0.5)

        element = SemStruc.Head("TEST", {
            "AGENT": "^$VAR1",              # Variables can be found directly as fillers
            "THEME": {                      # They can also be found as the VALUE of a filler
                "VALUE": "^$VAR2"
            }
        })

        f1 = TMRInstance(self.m, "HEAD", 1)
        f2 = TMRInstance(self.m, "HEAD", 2)
        f3 = TMRInstance(self.m, "HEAD", 3)

        candidate.bind(0, SemStruc.Variable(1), f1) # This is the binding for VAR1 in word 0, pointing to the head frame for word 4
        candidate.bind(0, SemStruc.Variable(2), f2) # This is the binding for VAR2 in word 0, pointing to the head frame for word 5
        candidate.bind(0, SemStruc.Variable(3), f3) # This is the binding for VAR3 in word 0, pointing to the head frame for word 6 (this should be ignored)

        self.assertEqual([], frame.fillers("AGENT"))
        self.assertEqual([], frame.fillers("THEME"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual([f1.id()], frame.fillers("AGENT"))
        self.assertEqual([f2.id()], frame.fillers("THEME"))

    def test_populate_semantic_properties_with_variables_and_dot_notation(self):
        # Variables found in the fillers with dot notation need to be partially resolved

        candidate = Candidate(self.m)

        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {
            "$VAR1": 4,     # This variable points to word 4, and is found in the semstruc
            "$VAR2": 5,     # This variable points to word 5, and is found in the semstruc
            "$VAR3": 6,     # This variable should be ignored
        }, 0.5)

        element = SemStruc.Head("TEST", {
            "AGENT": "^$VAR1.AGENT",        # Variables can be found directly as fillers
            "THEME": {                      # They can also be found as the VALUE of a filler
                "VALUE": "^$VAR2.THEME"
            }
        })

        f1 = TMRInstance(self.m, "HEAD", 1)
        f2 = TMRInstance(self.m, "HEAD", 2)
        f3 = TMRInstance(self.m, "HEAD", 3)

        candidate.bind(0, SemStruc.Variable(1), f1) # This is the binding for VAR1 in word 0, pointing to the head frame for word 4
        candidate.bind(0, SemStruc.Variable(2), f2) # This is the binding for VAR2 in word 0, pointing to the head frame for word 5
        candidate.bind(0, SemStruc.Variable(3), f3) # This is the binding for VAR3 in word 0, pointing to the head frame for word 6 (this should be ignored)

        self.assertEqual([], frame.fillers("AGENT"))
        self.assertEqual([], frame.fillers("THEME"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual(["%s?AGENT" % f1.id()], frame.fillers("AGENT"))
        self.assertEqual(["%s?THEME" % f2.id()], frame.fillers("THEME"))

    def test_populate_semantic_properties_with_variable_lists(self):
        # Variables found in the fillers need to be resolved; even if they are contained in a list

        candidate = Candidate(self.m)

        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {
            "$VAR1": 4,  # This variable points to word 4, and is found in the semstruc
            "$VAR2": 5,  # This variable points to word 5, and is found in the semstruc
            "$VAR3": 6,  # This variable should be ignored
        }, 0.5)

        element = SemStruc.Head("TEST", {
            "AGENT": {
                "VALUE": [
                    "^$VAR1",
                    "^$VAR2",
                ]
            }
        })

        f1 = TMRInstance(self.m, "HEAD", 1)
        f2 = TMRInstance(self.m, "HEAD", 2)
        f3 = TMRInstance(self.m, "HEAD", 3)

        candidate.bind(0, SemStruc.Variable(1), f1)  # This is the binding for VAR1 in word 0, pointing to the head frame for word 4
        candidate.bind(0, SemStruc.Variable(2), f2)  # This is the binding for VAR2 in word 0, pointing to the head frame for word 5
        candidate.bind(0, SemStruc.Variable(3), f3)  # This is the binding for VAR3 in word 0, pointing to the head frame for word 6 (this should be ignored)

        self.assertEqual([], frame.fillers("AGENT"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual([f1.id(), f2.id()], frame.fillers("AGENT"))

    def test_populate_semantic_properties_with_variable_with_lexical_constraint(self):
        # Variables found in the fillers need to be resolved, and lexical constraints need to be added.

        candidate = Candidate(self.m)

        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {
            "$VAR1": 4,     # This variable points to word 4
        }, 0.5)

        element = SemStruc.Head("TEST", {
            "AGENT": {
                "VALUE": "^$VAR1",
                "SEM": "HUMAN"
            },
        })

        f1 = TMRInstance(self.m, "HEAD", 1)

        candidate.bind(0, SemStruc.Variable(1), f1) # This is the binding for VAR1 in word 0, pointing to the head frame for word 4

        self.assertEqual([], frame.fillers("AGENT"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual([f1.id()], frame.fillers("AGENT"))
        self.assertEqual([Constraint(1, f1, "HUMAN", sense_map)], candidate.constraints)

    def test_populate_semantic_properties_as_variable_with_lexical_constraint(self):
        candidate = Candidate(self.m)
        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {
            "$VAR1": 4,  # This variable points to word 4, and is the variable found in the semstruc
        }, 0.5)

        element = SemStruc.Variable(1, {
            "AGENT": "HUMAN",
            "SEM": "VOTE",
        })

        candidate.bind(0, SemStruc.Variable(1), frame)  # This is the binding for VAR1 in word 0, pointing to the head frame for word 4

        self.assertEqual([], frame.fillers("AGENT"))
        self.assertEqual([], frame.fillers("SEM"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual(["HUMAN"], frame.fillers("AGENT"))
        self.assertEqual([], frame.fillers("SEM"))                                          # This is not added as a property
        self.assertEqual([Constraint(1, frame, "VOTE", sense_map)], candidate.constraints)  # Instead, it is added to a special "constraints" field

    def test_populate_semantic_properties_as_set_with_lexical_constraint(self):
        candidate = Candidate(self.m)
        frame = TMRInstance(self.m, "TEST", 1)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)

        element = SemStruc.Head("SET", {
            "MEMBER-TYPE": {
                "SEM": "HUMAN",
                "DEFAULT": "ANIMATE"
            }
        })

        self.assertEqual([], frame.fillers("MEMBER-TYPE"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame, sense_map, element, candidate)

        self.assertEqual([], frame.fillers("MEMBER-TYPE"))                                                  # This is not added as a property
        self.assertEqual([Constraint(1, frame, {"HUMAN", "ANIMATE"}, sense_map)], candidate.constraints)    # Instead, constraints are added

    def test_populate_semantic_properties_as_null_sem(self):
        # When a NULL-SEM + property is added, replace the filler with a reference to the HEAD of the sense that
        # is responsible for adding it.

        candidate = Candidate(self.m)
        frame1 = TMRInstance(self.m, "TEST", 1)
        frame2 = TMRInstance(self.m, "TEST", 2)
        candidate.bind(Word.basic(0), SemStruc.Head(), frame1)

        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)

        element = SemStruc.Head("^$VAR2", {
            "NULL-SEM": "+"
        })

        self.assertEqual([], frame2.fillers("NULL-SEM"))

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.populate_semantic_properties(frame2, sense_map, element, candidate)

        self.assertEqual([frame1.id()], frame2.fillers("NULL-SEM"))

        # If no HEAD exists, the first element can be used instead
        lexicon = Lexicon(Memory("", "", ""), "")
        lexicon.word("TEST").add_sense(self.mockSense("TEST-T1", semstruc={"REFSEM1": {}}))

        candidate = Candidate(self.m)
        frame1 = TMRInstance(self.m, "TEST", 1)
        frame2 = TMRInstance(self.m, "TEST", 2)
        candidate.bind(Word.basic(0), SemStruc.RefSem(1), frame1)

        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)

        element = SemStruc.Head("^$VAR2", {
            "NULL-SEM": "+"
        })

        self.assertEqual([], frame2.fillers("NULL-SEM"))

        analyzer = SemanticCompiler(OntoSemConfig(), lexicon=lexicon)
        analyzer.populate_semantic_properties(frame2, sense_map, element, candidate)

        self.assertEqual([frame1.id()], frame2.fillers("NULL-SEM"))

        # If no elements can be used at all, a "+" is retained
        candidate = Candidate(self.m)
        frame1 = TMRInstance(self.m, "TEST", 1)
        frame2 = TMRInstance(self.m, "TEST", 2)

        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)

        element = SemStruc.Head("^$VAR2", {
            "NULL-SEM": "+"
        })

        self.assertEqual([], frame2.fillers("NULL-SEM"))

        analyzer = SemanticCompiler(OntoSemConfig(), lexicon=lexicon)
        analyzer.populate_semantic_properties(frame2, sense_map, element, candidate)

        self.assertEqual(["+"], frame2.fillers("NULL-SEM"))

    def test_resolve_embedded_semstruc(self):
        candidate = Candidate(self.m)
        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)
        semstruc = [">", ["X", "Y"], ["Z", [1, 2, 3]]]

        analyzer = SemanticCompiler(OntoSemConfig())

        # In this simple case, there is nothing to resolve, the semstruc (no matter how complex) is returned
        # in the same state it went in.
        self.assertEqual(semstruc, analyzer.resolve_embedded_semstruc(semstruc, sense_map, candidate))

    def test_resolve_embedded_semstruc_with_variables(self):
        candidate = Candidate(self.m)

        sense_map = SenseMap(Word.basic(0), "TEST-T1", {
            "$VAR1": 4,  # This variable points to word 4, and is found in the semstruc
            "$VAR2": 5,  # This variable points to word 5, and is found in the semstruc
            "$VAR3": 6,  # This variable should be ignored
        }, 0.5)

        semstruc = [">", ["VALUE", "^$VAR1"], ["XYZ", ["VALUE", "^$VAR2"]], ["NOSUCH", "$VAR4"]]

        f1 = TMRInstance(self.m, "HEAD", 1)
        f2 = TMRInstance(self.m, "HEAD", 2)
        f3 = TMRInstance(self.m, "HEAD", 3)

        candidate.bind(0, SemStruc.Variable(1), f1)  # This is the binding for VAR1 in word 0, pointing to the head frame for word 4
        candidate.bind(0, SemStruc.Variable(2), f2)  # This is the binding for VAR2 in word 0, pointing to the head frame for word 5
        candidate.bind(0, SemStruc.Variable(3), f3)  # This is the binding for VAR3 in word 0, pointing to the head frame for word 6 (this should be ignored)

        analyzer = SemanticCompiler(OntoSemConfig())

        # The variable names are replaced where written.
        self.assertEqual([">", ["VALUE", f1.id()], ["XYZ", ["VALUE", f2.id()]], ["NOSUCH", "$VAR4"]], analyzer.resolve_embedded_semstruc(semstruc, sense_map, candidate))

        semstruc = [">", ["VALUE", "^$VAR1.AGENT"]]

        # The variable names can also be part of a pointer to another property.
        self.assertEqual([">", ["VALUE", "%s?AGENT" % f1.id()]], analyzer.resolve_embedded_semstruc(semstruc, sense_map, candidate))

    def test_resolve_embedded_semstruc_with_refsems(self):
        candidate = Candidate(self.m)

        sense_map = SenseMap(Word.basic(0), "TEST-T1", {}, 0.5)
        semstruc = [">", ["VALUE", "REFSEM1"], ["XYZ", ["VALUE", "REFSEM2"]], ["NOSUCH", "REFSEM3"]]

        f1 = TMRInstance(self.m, "REF", 1)
        f2 = TMRInstance(self.m, "REF", 2)

        candidate.bind(0, SemStruc.RefSem(1), f1)  # This is REFSEM1 in word 1
        candidate.bind(0, SemStruc.RefSem(2), f2)  # This is REFSEM2 in word 1

        analyzer = SemanticCompiler(OntoSemConfig())

        # The refesem names are replaced where written.
        self.assertEqual([">", ["VALUE", f1.id()], ["XYZ", ["VALUE", f2.id()]], ["NOSUCH", "REFSEM3"]], analyzer.resolve_embedded_semstruc(semstruc, sense_map, candidate))

        semstruc = [">", ["VALUE", "REFSEM1.AGENT"]]

        # The refsem names can also be part of a pointer to another property.
        self.assertEqual([">", ["VALUE", "%s?AGENT" % f1.id()]], analyzer.resolve_embedded_semstruc(semstruc, sense_map, candidate))

    def test_populate_syntatic_properties_with_past_tense_verb(self):
        # Declare EVENT and TEST in the ontology
        event = self.m.ontology.concept("EVENT")
        test = self.m.ontology.concept("TEST")

        # Setup the relevant syntax (a word with a synmap)
        word0 = Word(0, "", [], "", 0, 0, Word.Ner.NONE, [])
        sense_map = SenseMap(word0, "TEST-T1", {}, 0.5)

        # Build the candidate and frame; mock a semstruc element head
        candidate = Candidate(self.m)
        frame = TMRInstance(self.m, "TEST", 1)
        element = SemStruc.Head()

        # Run the populate method
        analyzer = SemanticCompiler(self.config)
        analyzer.populate_syntactic_properties(frame, sense_map, element, candidate)

        # Nothing happens; the frame is not a type of EVENT, and its associated word is not a past-tense verb
        self.assertEqual(0, len(frame.properties))

        # Make TEST a type of EVENT, and make the word a past-tense verb
        test.add_parent(event)
        word0.pos = {"V", "PAST"}

        # Run the populate method
        analyzer = SemanticCompiler(self.config)
        analyzer.populate_syntactic_properties(frame, sense_map, element, candidate)

        self.assertEqual([["<", "FIND-ANCHOR-TIME"]], frame.values("TIME"))

    def test_populate_syntatic_properties_with_present_tense_verb(self):
        # Declare EVENT and TEST in the ontology
        event = self.m.ontology.concept("EVENT")
        test = self.m.ontology.concept("TEST")

        # Setup the relevant syntax (a word with a synmap)
        word0 = Word(0, "", list(), "", 0, 0, Word.Ner.NONE, [])
        sense_map = SenseMap(word0, "TEST-T1", {}, 0.5)

        # Build the candidate and frame; mock a semstruc element head
        candidate = Candidate(self.m)
        frame = TMRInstance(self.m, "TEST", 1)
        element = SemStruc.Head()

        # Run the populate method
        analyzer = SemanticCompiler(self.config)
        analyzer.populate_syntactic_properties(frame, sense_map, element, candidate)

        # Nothing happens; the frame is not a type of EVENT, and its associated word is not a past-tense verb
        self.assertEqual(0, len(frame.properties))

        # Make TEST a type of EVENT, and make the word a present-tense verb
        test.add_parent(event)
        word0.pos = {"V", "PRESENT"}

        # Run the populate method
        analyzer = SemanticCompiler(self.config)
        analyzer.populate_syntactic_properties(frame, sense_map, element, candidate)

        self.assertEqual([["FIND-ANCHOR-TIME"]], frame.fillers("TIME"))

    def test_populate_syntatic_properties_with_infinitive_verb(self):
        # Declare EVENT and TEST in the ontology
        event = self.m.ontology.concept("EVENT")
        test = self.m.ontology.concept("TEST")

        # Setup the relevant syntax (a word with a synmap)
        word0 = Word(0, "", list(), "", 0, 0, Word.Ner.NONE, [])
        sense_map = SenseMap(word0, "TEST-T1", {}, 0.5)

        # Build the candidate and frame; mock a semstruc element head
        candidate = Candidate(self.m)
        frame = TMRInstance(self.m, "TEST", 1)
        element = SemStruc.Head()

        # Run the populate method
        analyzer = SemanticCompiler(self.config)
        analyzer.populate_syntactic_properties(frame, sense_map, element, candidate)

        # Nothing happens; the frame is not a type of EVENT, and its associated word is not an infinitive verb
        self.assertEqual(0, len(frame.properties))

        # Make TEST a type of EVENT, and make the word an infinivite verb
        test.add_parent(event)
        word0.pos = {"V", "INFINITIVE"}

        # Run the populate method
        analyzer = SemanticCompiler(self.config)
        analyzer.populate_syntactic_properties(frame, sense_map, element, candidate)

        self.assertEqual([[">", "FIND-ANCHOR-TIME"]], frame.fillers("TIME"))

    def test_populate_syntatic_properties_with_plural_nouns(self):
        # Declare EVENT and TEST in the ontology; neither are required for this test, but the populate_syntactic_properties
        # method performs other checks that require these concepts to exist.
        ontology = Ontology(self.m, "", load_now=False)
        event = ontology.concept("EVENT")
        test = ontology.concept("TEST")

        # Setup the relevant syntax (a word with a synmap)
        word0 = Word(0, "", list(), "", 0, 0, Word.Ner.NONE, [])
        sense_map = SenseMap(word0, "TEST-T1", {}, 0.5)

        # Build the candidate and frame; mock a semstruc element head
        candidate = Candidate(self.m)
        frame = TMRInstance(self.m, "TEST", 1)
        element = SemStruc.Head()

        # Run the populate method
        analyzer = SemanticCompiler(OntoSemConfig(), ontology=ontology)
        analyzer.populate_syntactic_properties(frame, sense_map, element, candidate)

        # Nothing happens; the word is not a plural noun
        self.assertEqual(0, len(frame.properties))

        # Make the word a plural noun
        word0.pos = {"N", "PLURAL"}

        # Run the populate method
        analyzer = SemanticCompiler(OntoSemConfig(), ontology=ontology)
        analyzer.populate_syntactic_properties(frame, sense_map, element, candidate)

        self.assertEqual([[">", 1]], frame.fillers("CARDINALITY"))

    def test_redirect_null_sem_relations(self):
        candidate = Candidate(self.m)

        f1 = candidate.basic_tmr.new_instance("TEST")
        f2 = candidate.basic_tmr.new_instance("TEST")
        f3 = candidate.basic_tmr.new_instance("TEST")
        f4 = candidate.basic_tmr.new_instance("TEST")
        f5 = candidate.basic_tmr.new_instance("TEST")

        f1.add_filler("THEME", f2.id())                   # f1 references f2, f3, and f4
        f1.add_filler("THEME", f3.id())
        f1.add_filler("THEME", f4.id())
        f2.add_filler("NULL-SEM", f2.id())                # f2 is null-semmed by itself
        f3.add_filler("NULL-SEM", f5.id())                # f3 is null-semmed by f5
        f4.add_filler("NULL-SEM", "+")                    # f4 is null-semmed by an unknown entity

        # Run the redirect method
        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.redirect_null_sem_relations(candidate)

        # Check to see that f2 and f4 have NOT been redirected (a self null-sem, and an unknown null-sem)
        # Check to see that f3 HAS been redirected to f5 (which null-semmed it)
        self.assertEqual([f2.id(), f4.id(), f5.id()], f1.values("THEME"))

    def test_remove_null_sems(self):
        candidate = Candidate(self.m)

        f1 = candidate.basic_tmr.new_instance("TEST")
        f2 = candidate.basic_tmr.new_instance("TEST")

        f2.add_filler("NULL-SEM", f1.id())

        analyzer = SemanticCompiler(OntoSemConfig())
        analyzer.remove_null_sems(candidate)

        self.assertEqual(1, len(candidate.basic_tmr.instances))
        self.assertIn(f1.id(), candidate.basic_tmr.instances)
        self.assertNotIn(f2.id(), candidate.basic_tmr.instances)

    def test_fix_inverses(self):
        self.m.properties.add_property(Property(self.m, "RELATION", contents={"type": "relation"}))

        # No inverse is defined, so the default R-INVERSE will be used
        self.m.properties.add_property(Property(self.m, "R", contents={"type": "relation"}))

        candidate = Candidate(self.m)

        f1 = candidate.basic_tmr.new_instance("TEST")
        f2 = candidate.basic_tmr.new_instance("TEST")

        f1.add_filler("RELATION", f2.id())
        f1.add_filler("R-INVERSE", f2.id())
        f1.add_filler("OTHER", f2.id())

        self.assertEqual([], f2.fillers("R"))           # Sanity check, there are no fillers for R in f2

        config = OntoSemConfig()
        config._memory = self.m

        analyzer = SemanticCompiler(config)
        analyzer.fix_inverses(candidate)

        self.assertEqual([], f1.fillers("R-INVERSE"))
        self.assertEqual([f2.id()], f1.fillers("RELATION"))
        self.assertEqual([f2.id()], f1.fillers("OTHER"))
        self.assertEqual([f1.id()], f2.fillers("R"))

    def test_build_mp_frames(self):
        lexicon = Lexicon(self.m, "")

        # Multiple meaning procedures in one sense
        # Meaning procedures can include ["VALUE", "^$VAR#"] to be resolved
        s1 = self.mockSense("TEST-T1", meaning_procedures=[
            ["TESTMP1", "ABCD", "DEFG"],
            ["TESTMP2", "ABCD", ["VALUE", "^$VAR1"]]
        ])

        # Some meaning procedures don't include the ["VALUE, ...] component, but the variable should be resolved anyway
        s2 = self.mockSense("TEST-T2", meaning_procedures=[
            ["TESTMP3", "^$VAR1", ["VALUE", "^$VAR2"]]
        ])

        # Meaning procedure variables are optional; if they can't be resolved, they should resolve to None
        s3 = self.mockSense("TEST-T3", meaning_procedures=[
            ["TESTMP4", "^$VAR1", ["VALUE", "^$VAR2"]]
        ])

        lexicon.word("TEST").add_sense(s1)
        lexicon.word("TEST").add_sense(s2)
        lexicon.word("TEST").add_sense(s3)

        sm1 = SenseMap(Word.basic(0), "TEST-T1", {"$VAR1": -1, "$VAR2": -1}, 0.5)
        sm2 = SenseMap(Word.basic(1), "TEST-T2", {"$VAR1": -1, "$VAR2": -1}, 0.5)
        sm3 = SenseMap(Word.basic(2), "TEST-T3", {}, 0.5)
        candidate = Candidate(self.m, sm1, sm2, sm3)

        f1 = candidate.basic_tmr.new_instance("BOUND")
        f2 = candidate.basic_tmr.new_instance("BOUND")
        f3 = candidate.basic_tmr.new_instance("BOUND")
        f4 = candidate.basic_tmr.new_instance("BOUND")

        candidate.bind(0, SemStruc.Variable(1), f1)
        candidate.bind(0, SemStruc.Variable(2), f2)
        candidate.bind(1, SemStruc.Variable(1), f3)
        candidate.bind(1, SemStruc.Variable(2), f4)

        analyzer = SemanticCompiler(OntoSemConfig(), lexicon=lexicon)
        analyzer.build_mp_frames(candidate)

        self.assertEqual(8, len(candidate.basic_tmr.instances))

        mp1frame = list(filter(lambda f: f.fillers("NAME") == ["TESTMP1"], candidate.basic_tmr.instances.values()))[0]
        mp2frame = list(filter(lambda f: f.fillers("NAME") == ["TESTMP2"], candidate.basic_tmr.instances.values()))[0]
        mp3frame = list(filter(lambda f: f.fillers("NAME") == ["TESTMP3"], candidate.basic_tmr.instances.values()))[0]
        mp4frame = list(filter(lambda f: f.fillers("NAME") == ["TESTMP4"], candidate.basic_tmr.instances.values()))[0]

        self.assertEqual(["ABCD", "DEFG"], mp1frame.values("PARAMETERS"))
        self.assertEqual(["ABCD", f1.id()], mp2frame.values("PARAMETERS"))
        self.assertEqual([f3.id(), f4.id()], mp3frame.values("PARAMETERS"))
        self.assertEqual([None, None], mp4frame.values("PARAMETERS"))