from ontomem.lexicon import Lexicon
from ontomem.ontology import Ontology
from ontosem.config import OntoSemConfig
from ontosem.semantics.candidate import Candidate, LexicalConstraintScore, RelationRangeScore, SenseMapPreferenceScore
from typing import Iterable, List

import itertools


class SemanticScorer(object):

    def __init__(self, config: OntoSemConfig, ontology: Ontology=None, lexicon: Lexicon=None):
        self.config = config
        self.ontology = ontology if ontology is not None else self.config.ontology()
        self.lexicon = lexicon if lexicon is not None else self.config.lexicon()
        self.properties = config.memory().properties

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

        # relations = set(map(lambda f: f.concept, self.ontology.concept("RELATION").descendants()))
        # relations.add("RELATION")

        for frame in candidate.basic_tmr.frames.values():
            for property, fillers in frame.properties.items():
                # Only score relations
                if property not in relations:
                    continue

                # Extract the ranges (and their descendants); only consider SEM for now
                ranges = self.ontology.concept(frame.concept).fillers(property, "SEM")
                descendants = list(itertools.chain.from_iterable(map(lambda r: r.descendants(), ranges)))

                ranges = set(map(lambda r: r.name, ranges))
                descendants = set(map(lambda d: d.name, descendants))

                for filler in fillers:
                    # Only score relations connected to actual frames
                    if filler not in candidate.basic_tmr.frames:
                        continue
                    filler = candidate.basic_tmr.frames[filler]

                    # If there are no ranges, give the minimum score
                    if len(ranges) == 0:
                        results.append(RelationRangeScore(0.1, frame, property, filler))
                        continue

                    # If the filler is one of the ranges, or a direct descendant, give the maximum score
                    if filler.concept in ranges or filler.concept in descendants:
                        results.append(RelationRangeScore(1.0, frame, property, filler))
                        continue

                    # Otherwise, find the nearest common ancestor to any range, calculate the distance from
                    # the filler to that ancestor, and penalize 0.1 for each step (to a maximum of 9 steps).
                    common_ancestors = itertools.chain.from_iterable(map(lambda r: self.ontology.common_ancestors(filler.concept, r), ranges))
                    common_ancestors = list(common_ancestors)

                    if len(common_ancestors) == 0:
                        results.append(RelationRangeScore(0.1, frame, property, filler))
                        continue

                    distance = min(map(lambda a: self.ontology.distance_to_ancestor(filler.concept, a), common_ancestors))
                    distance = min(distance, 9)
                    penalty = distance * 0.1
                    score = 1.0 - penalty
                    results.append(RelationRangeScore(score, frame, property, filler))

        return results

    def score_lexical_constraints(self, candidate: Candidate) -> List[LexicalConstraintScore]:
        results = []

        for constraint in candidate.constraints:
            tmr_frame_concept = self.ontology.concept(constraint.frame.concept)
            tmr_frame_concept_options = {tmr_frame_concept}

            # If the constraints are over a SET, evaluate the constraints over the members of the set instead
            if constraint.frame.concept == "SET":
                if "MEMBER-TYPE" in constraint.frame.properties:
                    tmr_frame_concept_options = set(map(lambda m: self.ontology.concept(m), constraint.frame.fillers("MEMBER-TYPE")))
                elif "ELEMENTS" in constraint.frame.properties:
                    tmr_frame_concept_options = set(map(lambda e: self.ontology.concept(candidate.basic_tmr.frames[e].concept), constraint.frame.fillers("ELEMENTS")))

            scores = []

            for tmr_frame_concept in tmr_frame_concept_options:

                for expected_concept in constraint.concepts:
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