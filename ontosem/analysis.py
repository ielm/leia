from ontomem.episodic import Frame
from ontosem.config import OntoSemConfig
from ontosem.semantics.candidate import Candidate
from ontosem.syntax.results import Syntax
from typing import List


class Analysis(object):

    def __init__(self, config: OntoSemConfig):
        self.config = config
        self.sentences: List[Sentence] = []

    def to_dict(self) -> dict:
        return {
            "config": self.config.to_dict(),
            "sentences": list(map(lambda s: s.to_dict(), self.sentences))
        }

    def to_memory(self, speaker: str=None, listener: str=None) -> Frame:
        frame = Frame("ANALYSIS.?").add_parent("ANALYSIS")
        frame["CONFIG"] = self.config.to_dict()

        for sentence in self.sentences:
            frame["HAS-SENTENCES"] += sentence.to_memory(speaker=speaker, listener=listener)

        return frame


class Sentence(object):

    def __init__(self, text: str):
        self.text: str = text
        self.syntax: Syntax = None
        self.semantics: List[Candidate] = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "syntax": self.syntax.to_dict(),
            "candidates": list(map(lambda c: c.to_dict(), self.semantics))
        }

    def to_memory(self, speaker: str=None, listener: str=None) -> Frame:
        frame = Frame("SENTENCE.?").add_parent("SENTENCE")
        frame["TEXT"] = self.text
        frame["HAS-SYNTAX"] = self.syntax.to_dict()

        for candidate in self.semantics:
            frame["HAS-CANDIDATES"] += candidate.to_memory(self.text, speaker=speaker, listener=listener)

        return frame