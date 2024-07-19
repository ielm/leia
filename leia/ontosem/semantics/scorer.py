from leia.ontosem.analysis import Analysis
from leia.ontosem.semantics.candidate import Candidate, LexicalConstraintScore, RelationRangeScore, SenseMapPreferenceScore
from leia.ontosem.semantics.tmr import TMRInstance
from typing import Iterable, List

import itertools


class SemanticScorer(object):

    def __init__(self, analysis: Analysis):
        self.analysis = analysis
        self.config = self.analysis.config
        self.ontology = self.config.ontology()
        self.lexicon = self.analysis.lexicon
        self.properties = self.config.memory().properties

    def run(self, candidates: Iterable[Candidate]) -> Iterable[Candidate]:
        for candidate in candidates:
            # Run various scoring mechanisms here, logging the results of each into the candidate.
            candidate.scores.extend(self.score_extract_sense_map_preferences(candidate))
            candidate.scores.extend(self.score_relation_ranges(candidate))
            candidate.scores.extend(self.score_lexical_constraints(candidate))

            # Calculate a final score as an aggregation of all scores on the candidate.
            candidate.score = self.calculate_final_score(candidate)

            # Yield the candidate.
            yield candidate

    def calculate_final_score(self, candidate: Candidate) -> float:
        result = 1.0
        for score in candidate.scores:
            result *= score.score

        return result

    def score_extract_sense_map_preferences(self, candidate: Candidate) -> List[SenseMapPreferenceScore]:
        return list(map(lambda sm: SenseMapPreferenceScore(sm.preference * 0.25, sm), candidate.senses))

    def score_relation_ranges(self, candidate: Candidate) -> List[RelationRangeScore]:
        results = []

        relations = self.properties.relations()
        relations = set(map(lambda r: r.name, relations))

        for frame in candidate.basic_tmr.instances():
            for property, fillers in frame.properties.items():
                # Only score relations
                if property not in relations:
                    continue

                # Extract the ranges (and their descendants); only consider SEM for now
                ranges = frame.concept.fillers(property, "SEM")
                descendants = list(itertools.chain.from_iterable(map(lambda r: r.descendants(), ranges)))

                ranges = set(map(lambda r: r.name, ranges))
                descendants = set(map(lambda d: d.name, descendants))

                for filler in map(lambda f: f.value(), fillers):
                    # Only score relations connected to actual frames
                    if not isinstance(filler, TMRInstance):
                        continue

                    # If there are no ranges, give the minimum score
                    if len(ranges) == 0:
                        results.append(RelationRangeScore(0.1, frame, property, filler))
                        continue

                    # If the filler is one of the ranges, or a direct descendant, give the maximum score
                    if filler.concept.name in ranges or filler.concept.name in descendants:
                        results.append(RelationRangeScore(1.0, frame, property, filler))
                        continue

                    # Otherwise, find the nearest common ancestor to any range, calculate the distance from
                    # the filler to that ancestor, and penalize 0.1 for each step (to a maximum of 9 steps).
                    common_ancestors = itertools.chain.from_iterable(map(lambda r: self.ontology.common_ancestors(filler.concept.name, r), ranges))
                    common_ancestors = list(common_ancestors)

                    if len(common_ancestors) == 0:
                        results.append(RelationRangeScore(0.1, frame, property, filler))
                        continue

                    distance = min(map(lambda a: self.ontology.distance_to_ancestor(filler.concept.name, a), common_ancestors))
                    distance = min(distance, 9)
                    penalty = distance * 0.1
                    score = 1.0 - penalty
                    results.append(RelationRangeScore(score, frame, property, filler))

        return results

    def score_lexical_constraints(self, candidate: Candidate) -> List[LexicalConstraintScore]:
        results = []

        for constraint in candidate.constraints:
            tmr_frame_concept = constraint.frame.concept
            tmr_frame_concept_options = {tmr_frame_concept}

            # If the constraints are over a SET, evaluate the constraints over the members of the set instead
            if constraint.frame.concept.name == "SET":
                if "MEMBER-TYPE" in constraint.frame.properties:
                    tmr_frame_concept_options = set(map(lambda m: self.ontology.concept(m), constraint.frame.fillers("MEMBER-TYPE")))
                elif "ELEMENTS" in constraint.frame.properties:
                    tmr_frame_concept_options = set(map(lambda e: candidate.basic_tmr.instance(e).concept, constraint.frame.fillers("ELEMENTS")))

            scores = []

            for tmr_frame_concept in tmr_frame_concept_options:

                for expected_concept in constraint.concepts:
                    # In the event that the expected constraint is a property, the matching frame must be an ABSTRACT-OBJECT
                    # with a matching REPRESENTS filler.
                    if self.properties.is_property(expected_concept):
                        if constraint.frame.concept.isa(self.ontology.concept("ABSTRACT-OBJECT")) and constraint.frame.value("REPRESENTS") == expected_concept:
                            scores.append(1.0)
                        else:
                            scores.append(0.0)
                        continue


                    expected_concept = self.ontology.concept(expected_concept)
                    # If the constraint is NOT X, either get a 1.0 if it is not, or a 0.1 if it is
                    if constraint.negate:
                        if tmr_frame_concept.isa(expected_concept):
                            scores.append(0.1)
                        else:
                            scores.append(1.0)
                    # Otherwise, gain a 1.0 if it is, a 0.1 if it is not, or a score between depending on distance to a common ancestor
                    else:
                        if tmr_frame_concept.isa(expected_concept):
                            scores.append(1.0)
                        elif expected_concept.isa(tmr_frame_concept):
                            distance = self.ontology.distance_to_ancestor(expected_concept.name, tmr_frame_concept.name)
                            distance = min(distance, 3)
                            score = 1.0 - (distance * 0.3)
                            scores.append(score)
                        else:
                            scores.append(0.1)

            score = max(scores)
            results.append(LexicalConstraintScore(score, constraint))

        return results