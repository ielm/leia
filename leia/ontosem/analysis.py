from leia.ontomem.episodic import Instance
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.semantics.candidate import Candidate
from leia.ontosem.syntax.results import Syntax
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