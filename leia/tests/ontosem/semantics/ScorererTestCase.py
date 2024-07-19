from leia.ontomem.lexicon import Sense, SynStruc
from leia.ontomem.properties import Property
from leia.ontosem.analysis import Analysis
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.semantics.candidate import Candidate, Constraint, Score
from leia.ontosem.semantics.candidate import LexicalConstraintScore, RelationRangeScore, SenseMapScore
from leia.ontosem.semantics.scorer import SemanticScorer
from leia.ontosem.syntax.results import SenseMap, Word
from leia.tests.LEIATestCase import LEIATestCase
from unittest import TestCase


class SemanticScorerTestCase(LEIATestCase):

    def setUp(self):
        self.analysis = Analysis()
        self.config = self.analysis.config
        self.m = self.config.memory()

    def test_calculate_final_score(self):
        candidate = Candidate(self.m)

        candidate.scores.append(Score(1.0))
        candidate.scores.append(Score(2.0))
        candidate.scores.append(Score(3.0))
        candidate.scores.append(Score(4.0))

        scorer = SemanticScorer(self.analysis)
        result = scorer.calculate_final_score(candidate)

        self.assertEqual(24.0, result)

    def test_score_sense_maps(self):

        scorer = SemanticScorer(self.analysis)
        word0 = Word.basic(0)
        word1 = Word.basic(1)

        sense = Sense(self.m, "TEST-T2", contents=self.mockSense("TEST-T2"))
        self.analysis.lexicon.add_sense(word1, sense)
        sense = self.analysis.lexicon.sense(word1, "TEST-T2")

        # If all variables in map are not None, scores are 1.0
        sm1 = SenseMap(word0, "TEST-T1", {})
        sm2 = SenseMap(word1, "TEST-T2", {"$VAR0": 0, "$VAR1": 1})

        self.assertEqual([
            SenseMapScore(1.0, sm1),
            SenseMapScore(1.0, sm2),
        ], scorer.score_sense_maps(Candidate(self.m, sm1, sm2)))

        # If any variable is None, but its corresponding element is optional, there is no penalty
        sm1 = SenseMap(word0, "TEST-T1", {})
        sm2 = SenseMap(word1, "TEST-T2", {"$VAR0": 0, "$VAR1": None})

        sense.synstruc.elements = [SynStruc.TokenElement({"TEST"}, None, dict(), 1, True)]

        self.assertEqual([
            SenseMapScore(1.0, sm1),
            SenseMapScore(1.0, sm2),
        ], scorer.score_sense_maps(Candidate(self.m, sm1, sm2)))

        # If any variable is None, and its corresponding element is not optional, the penalized score is 0.1
        sm1 = SenseMap(word0, "TEST-T1", {})
        sm2 = SenseMap(word1, "TEST-T2", {"$VAR0": 0, "$VAR1": None})

        sense.synstruc.elements = [SynStruc.TokenElement({"TEST"}, None, dict(), 1, False)]

        self.assertEqual([
            SenseMapScore(1.0, sm1),
            SenseMapScore(0.1, sm2),
        ], scorer.score_sense_maps(Candidate(self.m, sm1, sm2)))

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
        scorer = SemanticScorer(self.analysis)

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

        null_sense_map = SenseMap(Word.basic(0), "", {})

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

        scorer = SemanticScorer(self.analysis)

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

    def test_score_lexical_constraints_on_properties(self):
        # Lexical constraints may refer to properties by name, but the instances will be of ABSTRACT-OBJECT
        # with a REPRESENTS field.  This must be accommodated.
        # Properties must be an exact match (0.0 or 1.0 are the only valid outputs).

        property = self.m.properties.get_property("PROPERTY")

        childprop1 = self.m.properties.get_property("CHILDPROP1")
        childprop1.set_contents({"container": "$PROPERTY"})

        childprop2 = self.m.properties.get_property("CHILDPROP2")
        childprop2.set_contents({"container": "$PROPERTY"})

        candidate = Candidate(self.m)
        frame = candidate.basic_tmr.new_instance("ABSTRACT-OBJECT")
        frame.add_filler("REPRESENTS", "CHILDPROP1")

        null_sense_map = SenseMap(Word.basic(0), "", {})

        c1 = Constraint(1, frame, "PROPERTY", null_sense_map)
        c2 = Constraint(2, frame, "CHILDPROP1", null_sense_map)
        c3 = Constraint(3, frame, "CHILDPROP2", null_sense_map)
        c4 = Constraint(4, frame, "OBJECT", null_sense_map)
        c5 = Constraint(5, frame, "ABSTRACT-OBJECT", null_sense_map)

        candidate.constraints.append(c1)
        candidate.constraints.append(c2)
        candidate.constraints.append(c3)
        candidate.constraints.append(c4)
        candidate.constraints.append(c5)

        scorer = SemanticScorer(self.analysis)

        scores = scorer.score_lexical_constraints(candidate)

        self.assertEqual([
            LexicalConstraintScore(0.0, c1),    # It is not a PROPERTY (in that an exact match is required)
            LexicalConstraintScore(1.0, c2),    # It is a CHILDPROPERTY1
            LexicalConstraintScore(0.0, c3),    # It is not a CHILDPROPERTY2
            LexicalConstraintScore(0.1, c4),    # An ABSTRACT-OBJECT is very loosely an OBJECT
            LexicalConstraintScore(1.0, c5),    # It is an ABSTRACT-OBJECT
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

        null_sense_map = SenseMap(Word.basic(0), "", {})

        c1 = Constraint(1, frame, "GRANDPARENT", null_sense_map)
        c2 = Constraint(2, frame, "PARENT1", null_sense_map)
        c3 = Constraint(3, frame, "PARENT2", null_sense_map)

        candidate.constraints.append(c1)
        candidate.constraints.append(c2)
        candidate.constraints.append(c3)

        scorer = SemanticScorer(self.analysis)

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