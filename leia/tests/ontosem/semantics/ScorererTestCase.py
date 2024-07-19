from leia.ontomem.episodic import Instance
from leia.ontomem.properties import Property
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.semantics.candidate import Candidate, Constraint, Score
from leia.ontosem.semantics.candidate import LexicalConstraintScore, RelationRangeScore, SenseMapPreferenceScore
from leia.ontosem.semantics.scorer import SemanticScorer
from leia.ontosem.syntax.results import SenseMap, Word
from unittest import TestCase


class SemanticScorerTestCase(TestCase):

    def setUp(self):
        self.config = OntoSemConfig()
        self.m = self.config.memory()

    def test_calculate_final_score(self):
        candidate = Candidate(self.m)

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

        candidate = Candidate(self.m, sm1, sm2)

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
        self.m.properties.add_property(Property(self.m, "RELATION", contents={"type": "relation"}))
        self.m.properties.add_property(Property(self.m, "REL1", contents={"type": "relation"}))
        self.m.properties.add_property(Property(self.m, "REL2", contents={"type": "relation"}))
        self.m.properties.add_property(Property(self.m, "ATTRIBUTE", contents={"type": "literal"})) # TODO: THIS IS WRONG
        self.m.properties.add_property(Property(self.m, "ATTR1", contents={"type": "literal"}))

        # Now add some objects and events.
        obj = self.m.ontology.concept("OBJECT")
        o1 = self.m.ontology.concept("O1").add_parent(obj)
        self.m.ontology.concept("O2").add_parent(obj)
        self.m.ontology.concept("O1-1").add_parent(o1)
        event = self.m.ontology.concept("EVENT")
        e1 = self.m.ontology.concept("E1").add_parent(event)
        self.m.ontology.concept("E2").add_parent(event)
        self.m.ontology.concept("E1-1").add_parent(e1)

        # Now make some domains and ranges.
        e1.add_local("REL1", "SEM", o1)

        # Set up the scorer.
        scorer = SemanticScorer(self.config)

        # Score a candidate with a perfect match relation.
        candidate = Candidate(self.m)
        f1 = candidate.basic_tmr.new_instance(e1)
        f2 = candidate.basic_tmr.new_instance(o1)
        f1.add_filler("REL1", f2)
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([
            RelationRangeScore(1.0, f1, "REL1", f2)
        ], scores)

        # Score a candidate with a perfect match relation; this extends to descendants.
        candidate = Candidate(self.m)
        f1 = candidate.basic_tmr.new_instance("E1-1")
        f2 = candidate.basic_tmr.new_instance("O1-1")
        f1.add_filler("REL1", f2)
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([
            RelationRangeScore(1.0, f1, "REL1", f2)
        ], scores)

        # Score a candidate with an invalid relation.
        candidate = Candidate(self.m)
        f1 = candidate.basic_tmr.new_instance("E1")
        f2 = candidate.basic_tmr.new_instance("O1")
        f1.add_filler("REL2", f2)
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([
            RelationRangeScore(0.1, f1, "REL2", f2)
        ], scores)

        # Score a candidate with an acceptable, but penalized, relation.
        candidate = Candidate(self.m)
        f1 = candidate.basic_tmr.new_instance("E1")
        f2 = candidate.basic_tmr.new_instance("O2")
        f1.add_filler("REL1", f2)
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([
            RelationRangeScore(0.9, f1, "REL1", f2)
        ], scores)

        # Score a candidate with attributes (they are ignored).
        candidate = Candidate(self.m)
        f1 = candidate.basic_tmr.new_instance("E1")
        f2 = candidate.basic_tmr.new_instance("O1")
        f1.add_filler("ATTR1", f2)
        scores = scorer.score_relation_ranges(candidate)
        self.assertEqual([], scores)

    def test_score_lexical_constraints(self):
        # Each previously recorded lexical constraint is checked.  A score of 1.0 is assigned for any perfect match
        # or descendant.  Any ancestor is penalized 0.3 per step, to a maximum of 0.9.  Any other frame receives
        # the maximum penalty (0.1).

        gp = self.m.ontology.concept("GRANDPARENT")
        p1 = self.m.ontology.concept("PARENT1").add_parent(gp)
        p2 = self.m.ontology.concept("PARENT2").add_parent(gp)
        c = self.m.ontology.concept("CHILD").add_parent(p1)

        candidate = Candidate(self.m)
        frame = candidate.basic_tmr.new_instance("PARENT1")

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

        scorer = SemanticScorer(self.config)

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
        # TODO: LOOK INTO HOW SETS ARE BEING HANDLED HERE

        self.config.memory().ontology.concept("SET")
        gp = self.config.memory().ontology.concept("GRANDPARENT")
        p1 = self.config.memory().ontology.concept("PARENT1").add_parent(gp)
        p2 = self.config.memory().ontology.concept("PARENT2").add_parent(gp)

        candidate = Candidate(self.m)
        frame = candidate.basic_tmr.new_instance("SET")
        pf1 = candidate.basic_tmr.new_instance("PARENT1")

        null_sense_map = SenseMap(Word.basic(0), "", {}, 0.5)

        c1 = Constraint(1, frame, "GRANDPARENT", null_sense_map)
        c2 = Constraint(2, frame, "PARENT1", null_sense_map)
        c3 = Constraint(3, frame, "PARENT2", null_sense_map)

        candidate.constraints.append(c1)
        candidate.constraints.append(c2)
        candidate.constraints.append(c3)

        scorer = SemanticScorer(self.config)

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
            "ELEMENTS": [pf1.id()]
        }

        self.assertEqual([
            LexicalConstraintScore(1.0, c1),
            LexicalConstraintScore(1.0, c2),
            LexicalConstraintScore(0.1, c3),
        ], scorer.score_lexical_constraints(candidate))