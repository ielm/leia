from ontomem.episodic import Frame
from ontosem.config import OntoSemConfig
from ontosem.semantics.candidate import Candidate, Constraint, Score
from ontosem.semantics.candidate import LexicalConstraintScore, RelationRangeScore, SenseMapPreferenceScore
from ontosem.semantics.scorer import SemanticScorer
from ontosem.syntax.results import SenseMap, Word
from unittest import TestCase


class SemanticScorerTestCase(TestCase):

    def test_calculate_final_score(self):
        candidate = Candidate()

        candidate.scores.append(Score(1.0))
        candidate.scores.append(Score(2.0))
        candidate.scores.append(Score(3.0))
        candidate.scores.append(Score(4.0))

        scorer = SemanticScorer(OntoSemConfig())
        result = scorer.calculate_final_score(candidate)

        self.assertEqual(24.0, result)

    def test_score_extract_sense_map_preferences(self):
        sm1 = SenseMap(Word.basic(0), "TEST-T1", {}, 2.0)
        sm2 = SenseMap(Word.basic(1), "TEST-T1", {}, 4.0)

        candidate = Candidate(sm1, sm2)

        scorer = SemanticScorer(OntoSemConfig())
        scores = scorer.score_extract_sense_map_preferences(candidate)

        self.assertEqual([
            SenseMapPreferenceScore(0.5, sm1),
            SenseMapPreferenceScore(1.0, sm2),
        ], scores)

    def test_score_relation_ranges(self):
        # This function scores only relations in the TMRFrames (not attributes).  It finds what the frame's expected
        # range for the relation is, and scores the actual filler against that.

        # If the filler IS-A one of the ranges, the score = 1.0.
        # If the relation is not defined on the frame at all, the score = 0.1.
        # Otherwise, find the nearest ancestor of the filler and any valid range (whichever is best), and
        # penalize 0.1 per IS-A link from the filler (maximum of 9 penalties, to 0.1).

        # Add knowledge directly to the memory manager.
        # Define relations and attributes, and add one of each.
        # Attributes should be ignored by this scoring mechanism.
        Frame("RELATION").add_to_space("ONT")
        Frame("REL1").add_parent(Frame("RELATION")).add_to_space("ONT")
        Frame("REL2").add_parent(Frame("RELATION")).add_to_space("ONT")
        Frame("ATTRIBUTE").add_to_space("ONT")
        Frame("ATTR1").add_parent(Frame("ATTRIBUTE")).add_to_space("ONT")

        # Now add some objects and events.
        Frame("OBJECT").add_to_space("ONT")
        Frame("O1").add_parent(Frame("OBJECT")).add_to_space("ONT")
        Frame("O2").add_parent(Frame("OBJECT")).add_to_space("ONT")
        Frame("O1-1").add_parent(Frame("O1")).add_to_space("ONT")
        Frame("EVENT").add_to_space("ONT")
        Frame("E1").add_parent(Frame("EVENT")).add_to_space("ONT")
        Frame("E2").add_parent(Frame("EVENT")).add_to_space("ONT")
        Frame("E1-1").add_parent(Frame("E1")).add_to_space("ONT")

        # Now make some domains and ranges.
        Frame("E1")["REL1"]["SEM"] = Frame("O1")

        # Set up the scorer.
        scorer = SemanticScorer(OntoSemConfig())

        # Score a candidate with a perfect match relation.
        candidate = Candidate()
        f1 = candidate.basic_tmr.next_frame_for_concept("E1")
        f2 = candidate.basic_tmr.next_frame_for_concept("O1")
        f1.add_filler("REL1", f2.frame_id())
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([
            RelationRangeScore(1.0, f1, "REL1", f2)
        ], scores)

        # Score a candidate with a perfect match relation; this extends to descendants.
        candidate = Candidate()
        f1 = candidate.basic_tmr.next_frame_for_concept("E1-1")
        f2 = candidate.basic_tmr.next_frame_for_concept("O1-1")
        f1.add_filler("REL1", f2.frame_id())
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([
            RelationRangeScore(1.0, f1, "REL1", f2)
        ], scores)

        # Score a candidate with an invalid relation.
        candidate = Candidate()
        f1 = candidate.basic_tmr.next_frame_for_concept("E1")
        f2 = candidate.basic_tmr.next_frame_for_concept("O1")
        f1.add_filler("REL2", f2.frame_id())
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([
            RelationRangeScore(0.1, f1, "REL2", f2)
        ], scores)

        # Score a candidate with an acceptable, but penalized, relation.
        candidate = Candidate()
        f1 = candidate.basic_tmr.next_frame_for_concept("E1")
        f2 = candidate.basic_tmr.next_frame_for_concept("O2")
        f1.add_filler("REL1", f2.frame_id())
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([
            RelationRangeScore(0.9, f1, "REL1", f2)
        ], scores)

        # Score a candidate with attributes (they are ignored).
        candidate = Candidate()
        f1 = candidate.basic_tmr.next_frame_for_concept("E1")
        f2 = candidate.basic_tmr.next_frame_for_concept("O1")
        f1.add_filler("ATTR1", f2.frame_id())
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([], scores)

    def test_score_lexical_constraints(self):
        # Each previously recorded lexical constraint is checked.  A score of 1.0 is assigned for any perfect match
        # or descendant.  Any ancestor is penalized 0.3 per step, to a maximum of 0.9.  Any other frame receives
        # the maximum penalty (0.1).

        gp = Frame("GRANDPARENT")
        p1 = Frame("PARENT1").add_parent(gp)
        p2 = Frame("PARENT2").add_parent(gp)
        c  = Frame("CHILD").add_parent(p1)

        candidate = Candidate()
        frame = candidate.basic_tmr.next_frame_for_concept("PARENT1")

        null_sense_map = SenseMap(Word.basic(0), "", {}, 0.5)

        c1 = Constraint(1, frame, "PARENT1", null_sense_map)
        c2 = Constraint(2, frame, "GRANDPARENT", null_sense_map)
        c3 = Constraint(3, frame, "CHILD", null_sense_map)
        c4 = Constraint(4, frame, "PARENT2", null_sense_map)
        c5 = Constraint(5, frame, ["CHILD", "PARENT2"], null_sense_map)
        c6 = Constraint(6, frame, ["NOT", "GRANDPARENT"], null_sense_map)
        c7 = Constraint(7, frame, ["NOT", "PARENT2"], null_sense_map)

        candidate.constraints.append(c1)
        candidate.constraints.append(c2)
        candidate.constraints.append(c3)
        candidate.constraints.append(c4)
        candidate.constraints.append(c5)
        candidate.constraints.append(c6)
        candidate.constraints.append(c7)

        scorer = SemanticScorer(OntoSemConfig())

        scores = scorer.score_lexical_constraints(candidate)

        self.assertEqual([
            LexicalConstraintScore(1.0, c1),
            LexicalConstraintScore(1.0, c2),
            LexicalConstraintScore(0.7, c3),
            LexicalConstraintScore(0.1, c4),
            LexicalConstraintScore(0.7, c5),    # The best option of CHILD and PARENT2 is used
            LexicalConstraintScore(0.1, c6),    # Violation of a NOT constraint earns a maximum penalty
            LexicalConstraintScore(1.0, c7),    # Maximum score applied if a NOT constraint is passed
        ], scores)

    def test_score_lexical_constraints_on_sets(self):
        Frame("SET")
        gp = Frame("GRANDPARENT")
        p1 = Frame("PARENT1").add_parent(gp)
        p2 = Frame("PARENT2").add_parent(gp)

        candidate = Candidate()
        frame = candidate.basic_tmr.next_frame_for_concept("SET")
        pf1 = candidate.basic_tmr.next_frame_for_concept("PARENT1")

        null_sense_map = SenseMap(Word.basic(0), "", {}, 0.5)

        c1 = Constraint(1, frame, "GRANDPARENT", null_sense_map)
        c2 = Constraint(2, frame, "PARENT1", null_sense_map)
        c3 = Constraint(3, frame, "PARENT2", null_sense_map)

        candidate.constraints.append(c1)
        candidate.constraints.append(c2)
        candidate.constraints.append(c3)

        scorer = SemanticScorer(OntoSemConfig())

        frame.properties = {
            "MEMBER-TYPE": ["GRANDPARENT"]
        }

        self.assertEqual([
            LexicalConstraintScore(1.0, c1),
            LexicalConstraintScore(0.7, c2),
            LexicalConstraintScore(0.7, c3),
        ], scorer.score_lexical_constraints(candidate))

        frame.properties = {
            "MEMBER-TYPE": ["PARENT1", "PARENT2"]
        }

        self.assertEqual([
            LexicalConstraintScore(1.0, c1),
            LexicalConstraintScore(1.0, c2),
            LexicalConstraintScore(1.0, c3),
        ], scorer.score_lexical_constraints(candidate))

        frame.properties = {
            "ELEMENTS": [pf1.frame_id()]
        }

        self.assertEqual([
            LexicalConstraintScore(1.0, c1),
            LexicalConstraintScore(1.0, c2),
            LexicalConstraintScore(0.1, c3),
        ], scorer.score_lexical_constraints(candidate))