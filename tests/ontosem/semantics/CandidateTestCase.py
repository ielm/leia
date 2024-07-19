from ontomem.lexicon import SemStruc
from ontomem.memory import Memory
from ontosem.semantics.candidate import Candidate
from ontosem.semantics.tmr import TMRFrame
from ontosem.syntax.results import SenseMap, Word
from unittest import TestCase


class CandidateTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_words_by_binding_count(self):

        sm0 = SenseMap(Word.basic(0), "S0-N1", {"$VAR0": 0}, 0.5)
        sm1 = SenseMap(Word.basic(1), "S1-N1", {"$VAR0": 0, "$VAR1": 0, "$VAR2": 0}, 0.5)
        sm2 = SenseMap(Word.basic(2), "S2-N1", {"$VAR0": 0, "$VAR1": 0, "$VAR2": 0}, 0.5)
        sm3 = SenseMap(Word.basic(3), "S3-N1", {"$VAR0": 0, "$VAR1": 0}, 0.5)
        sm4 = SenseMap(Word.basic(4), "S4-N1", {"$VAR0": 0, "$VAR1": 0, "$VAR2": 0}, 0.5)
        sm5 = SenseMap(Word.basic(5), "S5-N1", {"$VAR0": 0, "$VAR1": 0}, 0.5)

        candidate = Candidate(self.m, sm0, sm1, sm2, sm3, sm4, sm5)

        self.assertEqual([sm1, sm2, sm4, sm3, sm5, sm0], candidate.words_by_binding_count())

    def test_bind_resolve_head(self):
        f = TMRFrame(self.m, "TEST", 1)
        c = Candidate(self.m)

        r = c.bind(1, SemStruc.Head("TEST", {}), f)
        self.assertEqual("1.HEAD", r)
        self.assertEqual(f, c.resolve(1, SemStruc.Head("TEST", {})))

    def test_bind_resolve_sub(self):
        f = TMRFrame(self.m, "TEST", 1)
        c = Candidate(self.m)

        r = c.bind(1, SemStruc.Sub(2, "TEST", {}), f)
        self.assertEqual("1.SUB.2", r)
        self.assertEqual(f, c.resolve(1, SemStruc.Sub(2, "TEST", {})))

    def test_bind_resolve_refsem(self):
        f = TMRFrame(self.m, "TEST", 1)
        c = Candidate(self.m)

        r = c.bind(1, SemStruc.RefSem(4, SemStruc({"rs": "test"})), f)
        self.assertEqual("1.REFSEM.4", r)
        self.assertEqual(f, c.resolve(1, SemStruc.RefSem(4, SemStruc({"rs": "test"}))))

    def test_bind_resolve_variable(self):
        f = TMRFrame(self.m, "TEST", 1)
        c = Candidate(self.m)

        r = c.bind(1, SemStruc.Variable(7, {"v7": "test"}), f)
        self.assertEqual("1.VAR.7", r)
        self.assertEqual(f, c.resolve(1, SemStruc.Variable(7, {"v7": "test"})))

    def test_bind_resolve_property(self):
        f = TMRFrame(self.m, "TEST", 1)
        c = Candidate(self.m)

        r = c.bind(1, SemStruc.Property(9, "AGENT", {"AGENT": 123}), f)
        self.assertEqual("1.VAR.9.AGENT", r)
        self.assertEqual(f, c.resolve(1, SemStruc.Property(9, "AGENT", {"AGENT": 123})))

    def test_resolve_returns_none(self):
        # If the element cannot be resolved, none is returned.
        c = Candidate(self.m)
        self.assertIsNone(c.resolve(0, SemStruc.Head()))

    def test_add_constraint(self):
        c = Candidate(self.m)

        c1 = c.add_constraint(TMRFrame(self.m, "", 1), "", SenseMap(Word.basic(0), "", {}, 0.5))
        self.assertEqual(1, c1.index)

        c2 = c.add_constraint(TMRFrame(self.m, "", 1), "", SenseMap(Word.basic(0), "", {}, 0.5))
        self.assertEqual(2, c2.index)

        self.assertIn(c1, c.constraints)
        self.assertIn(c2, c.constraints)
