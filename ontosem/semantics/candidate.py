from ontomem.episodic import Frame
from ontomem.lexicon import SemStruc
from ontomem.memory import Memory
from ontosem.semantics.tmr import TMR, TMRFrame
from ontosem.syntax.results import SenseMap, Word
from typing import List, Set, Union

import uuid


class Candidate(object):

    def __init__(self, memory: Memory, *senses: SenseMap):
        self.id = str(uuid.uuid4())

        self.senses = senses
        self.basic_tmr = TMR(memory)
        self.extended_tmr = TMR(memory)
        self.constraints: List[Constraint] = []
        self.scores: List[Score] = []
        self.score = 0.0

        # Indexes ---

        # Resolved frames from word+semstruc
        # #.HEAD (e.g., 0.HEAD) is the frame representing the head of word 0
        # #.REFSEM.# (e.g., 2.REFSEM.3) is the frame representing the 3rd refsem of word 2
        # #.VAR.# (e.g., 2.VAR.1) is the frame representing var1 in word 2
        self._frame_resolutions = {}

        # Incrementing count of constraints
        self._constraint_index = 0

    def words_by_binding_count(self) -> List[SenseMap]:
        # Returns the senses ordered by highest binding count first, lowest word order second.

        return list(sorted(self.senses, key=lambda s: (len(s.bindings), -s.word.index), reverse=True))

    def _element_resolution_name(self, word: Union[int, Word], element: Union[SemStruc.Head, SemStruc.Sub, SemStruc.RefSem, SemStruc.Variable, SemStruc.Property]) -> str:
        if isinstance(word, Word):
            word = word.index

        if isinstance(element, SemStruc.Head):
            resolution = "%d.HEAD" % word
        elif isinstance(element, SemStruc.Sub):
            resolution = "%d.SUB.%d" % (word, element.index)
        elif isinstance(element, SemStruc.RefSem):
            resolution = "%d.REFSEM.%d" % (word, element.index)
        elif isinstance(element, SemStruc.Variable):
            resolution = "%d.VAR.%d" % (word, element.index)
        elif isinstance(element, SemStruc.Property):
            resolution = "%d.VAR.%d.%s" % (word, element.variable, element.property)
        else:
            raise Exception("Unknown semstruc element: %s." % str(element))

        return resolution

    def bind(self, word: Union[int, Word], element: Union[SemStruc.Head, SemStruc.Sub, SemStruc.RefSem, SemStruc.Variable, SemStruc.Property], frame: TMRFrame) -> str:
        resolution = self._element_resolution_name(word, element)
        self._frame_resolutions[resolution] = frame
        return resolution

    def resolve(self, word: Union[int, Word], element: Union[SemStruc.Head, SemStruc.Sub, SemStruc.RefSem, SemStruc.Variable, SemStruc.Property]) -> Union[TMRFrame, None]:
        resolution = self._element_resolution_name(word, element)
        if resolution in self._frame_resolutions:
            return self._frame_resolutions[resolution]

        return None

    def add_constraint(self, frame: TMRFrame, concept: Union[str, List[str], Set[str]], sense_map: SenseMap) -> 'Constraint':
        self._constraint_index += 1
        c = Constraint(self._constraint_index, frame, concept, sense_map)
        self.constraints.append(c)
        return c

    def to_dict(self) -> dict:
        return  {
            "id": self.id,
            "sense-maps": list(map(lambda sm: sm.to_dict(), self.senses)),
            "basic-tmr": self.basic_tmr.to_dict(),
            "extended-tmr": self.extended_tmr.to_dict(),
            "constraints": list(map(lambda c: c.to_dict(), self.constraints)),
            "scores": list(map(lambda s: s.to_dict(), self.scores)),
            "final-score": self.score
        }

    def __eq__(self, other):
        if isinstance(other, Candidate):
            return self.senses == other.senses and self.basic_tmr == other.basic_tmr and self.extended_tmr == other.extended_tmr
        return super().__eq__(other)

    def __repr__(self):
        return "Candidate %s" % repr(self.senses)


class Constraint(object):

    def __init__(self, index: int, frame: TMRFrame, concepts: Union[str, List[str], Set[str]], sense_map: SenseMap):
        if isinstance(concepts, str):
            concepts = {concepts}

        if isinstance(concepts, list):
            concepts = set(concepts)

        self.negate = False
        if "NOT" in concepts:
            self.negate = True
            concepts.remove("NOT")

        self.index = index
        self.frame = frame
        self.concepts = concepts
        self.sense_map = sense_map

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "frame": self.frame.id(),
            "concepts": list(self.concepts),
            "sense-map": self.sense_map.word.index
        }

    def __eq__(self, other):
        if isinstance(other, Constraint):
            return self.index == other.index and self.frame == other.frame and self.concepts == other.concepts and self.sense_map == other.sense_map
        return super().__eq__(other)

    def __repr__(self):
        return "Constraint: %s should be a %s, according to %s." % (self.frame.id(), self.concepts, self.sense_map)


class Score(object):

    def __init__(self, score: float, message: str=""):
        self.score = score
        self.message = message

    def to_dict(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "score": self.score,
            "message": self.message
        }

    def __repr__(self):
        return "Score %f: '%s'" % (self.score, self.message)


class SenseMapPreferenceScore(Score):

    def __init__(self, score: float, sense_map: SenseMap):
        super().__init__(score)
        self.sense_map = sense_map

    def to_dict(self) -> dict:
        out = super().to_dict()
        out.update({
            "sense-map": self.sense_map.word.index
        })

        return out

    def __repr__(self):
        return "Sense map for word %d (%s) had syntactic preference %f." % (self.sense_map.word.index, self.sense_map.sense, self.score)

    def __eq__(self, other):
        if isinstance(other, SenseMapPreferenceScore):
            return self.score == other.score and self.sense_map == other.sense_map
        return super().__eq__(other)


class RelationRangeScore(Score):

    def __init__(self, score: float, frame: TMRFrame, property, filler: TMRFrame):
        super().__init__(score)
        self.frame = frame
        self.property = property
        self.filler = filler

    def to_dict(self) -> dict:
        out = super().to_dict()
        out.update({
            "frame": self.frame.id(),
            "property": self.property,
            "filler": self.filler.id()
        })

        return out

    def __repr__(self):
        return "Relation range scored %f for %s -[%s]-> %s." % (self.score, self.frame.id(), self.property, self.filler.id())

    def __eq__(self, other):
        if isinstance(other, RelationRangeScore):
            return self.score == other.score and self.frame == other.frame and self.property == other.property and self.filler == other.filler
        return super().__eq__(other)


class LexicalConstraintScore(Score):

    def __init__(self, score: float, constraint: Constraint):
        super().__init__(score)
        self.constraint = constraint

    def to_dict(self) -> dict:
        out = super().to_dict()
        out.update({
            "constraint": self.constraint.index
        })

        return out

    def __repr__(self):
        return "Lexical constraint scored %f for constraint %s on %s (from %s)." % (self.score, self.constraint.concepts, self.constraint.frame.id(), self.constraint.sense_map)

    def __eq__(self, other):
        if isinstance(other, LexicalConstraintScore):
            return self.score == other.score and self.constraint == other.constraint
        return super().__eq__(other)