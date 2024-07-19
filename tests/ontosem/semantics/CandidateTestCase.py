from ontomem.lexicon import SemStruc
from ontosem.semantics.candidate import Candidate, Score
from ontosem.semantics.tmr import TMRFrame
from ontosem.semantics.tmr import TMR
from ontosem.syntax.results import SenseMap, Word
from unittest import TestCase
from unittest.mock import MagicMock


class CandidateTestCase(TestCase):

    def test_words_by_binding_count(self):

        sm0 = SenseMap(Word.basic(0), "S0-N1", {"$VAR0": 0}, 0.5)
        sm1 = SenseMap(Word.basic(1), "S1-N1", {"$VAR0": 0, "$VAR1": 0, "$VAR2": 0}, 0.5)
        sm2 = SenseMap(Word.basic(2), "S2-N1", {"$VAR0": 0, "$VAR1": 0, "$VAR2": 0}, 0.5)
        sm3 = SenseMap(Word.basic(3), "S3-N1", {"$VAR0": 0, "$VAR1": 0}, 0.5)
        sm4 = SenseMap(Word.basic(4), "S4-N1", {"$VAR0": 0, "$VAR1": 0, "$VAR2": 0}, 0.5)
        sm5 = SenseMap(Word.basic(5), "S5-N1", {"$VAR0": 0, "$VAR1": 0}, 0.5)

        candidate = Candidate(sm0, sm1, sm2, sm3, sm4, sm5)

        self.assertEqual([sm1, sm2, sm4, sm3, sm5, sm0], candidate.words_by_binding_count())

    def test_bind_resolve_head(self):
        f = TMRFrame("TEST", 1)
        c = Candidate()

        r = c.bind(1, SemStruc.Head("TEST", {}), f)
        self.assertEqual("1.HEAD", r)
        self.assertEqual(f, c.resolve(1, SemStruc.Head("TEST", {})))

    def test_bind_resolve_sub(self):
        f = TMRFrame("TEST", 1)
        c = Candidate()

        r = c.bind(1, SemStruc.Sub(2, "TEST", {}), f)
        self.assertEqual("1.SUB.2", r)
        self.assertEqual(f, c.resolve(1, SemStruc.Sub(2, "TEST", {})))

    def test_bind_resolve_refsem(self):
        f = TMRFrame("TEST", 1)
        c = Candidate()

        r = c.bind(1, SemStruc.RefSem(4, SemStruc({"rs": "test"})), f)
        self.assertEqual("1.REFSEM.4", r)
        self.assertEqual(f, c.resolve(1, SemStruc.RefSem(4, SemStruc({"rs": "test"}))))

    def test_bind_resolve_variable(self):
        f = TMRFrame("TEST", 1)
        c = Candidate()

        r = c.bind(1, SemStruc.Variable(7, {"v7": "test"}), f)
        self.assertEqual("1.VAR.7", r)
        self.assertEqual(f, c.resolve(1, SemStruc.Variable(7, {"v7": "test"})))

    def test_bind_resolve_property(self):
        f = TMRFrame("TEST", 1)
        c = Candidate()

        r = c.bind(1, SemStruc.Property(9, "AGENT", {"AGENT": 123}), f)
        self.assertEqual("1.VAR.9.AGENT", r)
        self.assertEqual(f, c.resolve(1, SemStruc.Property(9, "AGENT", {"AGENT": 123})))

    def test_resolve_returns_none(self):
        # If the element cannot be resolved, none is returned.
        c = Candidate()
        self.assertIsNone(c.resolve(0, SemStruc.Head()))

    def test_add_constraint(self):
        c = Candidate()

        c1 = c.add_constraint(TMRFrame("", 1), "", SenseMap(Word.basic(0), "", {}, 0.5))
        self.assertEqual(1, c1.index)

        c2 = c.add_constraint(TMRFrame("", 1), "", SenseMap(Word.basic(0), "", {}, 0.5))
        self.assertEqual(2, c2.index)

        self.assertIn(c1, c.constraints)
        self.assertIn(c2, c.constraints)


class CandidateToMemoryTestCase(TestCase):

    def test_to_memory(self):
        s1 = SenseMap(Word.basic(0), "", {}, 0.25)
        s2 = SenseMap(Word.basic(0), "", {}, 0.75)

        score1 = Score(0.15, "message 1")
        score2 = Score(0.35, "message 2")

        c = Candidate(s1, s2)
        c.basic_tmr = TMR()
        c.extended_tmr = TMR()
        constraint1 = c.add_constraint(TMRFrame("", 1), "", s1)
        constraint2 = c.add_constraint(TMRFrame("", 1), "", s2)
        c.scores.append(score1)
        c.scores.append(score2)
        c.score = 123.456

        c.basic_tmr.to_memory = MagicMock(return_value="MOCKED BASIC TMR")
        c.extended_tmr.to_memory = MagicMock(return_value="MOCKED EXTENDED TMR")

        frame = c.to_memory("The man hit the building.", speaker="@SPEAKER.1", listener="@LISTENER.1")

        self.assertIsNotNone(frame["UUID"].singleton())
        self.assertEqual([s1.to_dict(), s2.to_dict()], frame["SENSES"].values())
        self.assertEqual("MOCKED BASIC TMR", frame["BASIC-TMR"].singleton())
        self.assertEqual("MOCKED EXTENDED TMR", frame["EXTENDED-TMR"].singleton())
        self.assertEqual([constraint1.to_dict(), constraint2.to_dict()], frame["HAS-CONSTRAINTS"].values())
        self.assertEqual([score1.to_dict(), score2.to_dict()], frame["HAS-SCORES"].values())
        self.assertEqual(123.456, frame["SCORE"].singleton())

        c.basic_tmr.to_memory.assert_called_once_with("The man hit the building.", speaker="@SPEAKER.1", listener="@LISTENER.1")
        c.extended_tmr.to_memory.assert_called_once_with("The man hit the building.", speaker="@SPEAKER.1", listener="@LISTENER.1")