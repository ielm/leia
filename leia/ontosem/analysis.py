from leia.ontomem.episodic import Instance
from leia.ontosem.config import OntoSemConfig
from leia.ontomem.lexicon import Sense
from leia.ontosem.semantics.candidate import Candidate
from leia.ontosem.syntax.results import Syntax, Word
from typing import Dict, List, Union


class Analysis(object):

    def __init__(self, config: OntoSemConfig):
        self.config = config
        self.sentences: List[Sentence] = []
        self.lexicon = WMLexicon()

    def to_dict(self) -> dict:
        return {
            "config": self.config.to_dict(),
            "sentences": list(map(lambda s: s.to_dict(), self.sentences))
        }


class Sentence(object):

    def __init__(self, text: str):
        self.text: str = text
        self.syntax: Syntax = None
        self.semantics: List[Candidate] = []

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "syntax": self.syntax.to_dict(),
            "candidates": list(map(lambda c: c.to_dict(), self.semantics))
        }


class WMLexicon(object):

    """
    This class is for handling the working-memory lexicon produced by the syntactic analysis (and used
    downstream in future stages).  It acts as a replacement for the main agent lexicon as any number
    of transformations may temporarily modify lexical senses in the context of a single analysis.
    """

    def __init__(self):
        self.words = dict()

    def add_sense(self, word: Word, sense: Sense):
        # Add a (copy of) a sense to a specific word
        word = self._word(word)
        copy = Sense(sense.memory, sense.id, contents=sense.to_dict())
        word[sense.id] = copy

    def remove_sense(self, word: Word, sense: str):
        # Remove a sense from a specific word
        word = self._word(word)
        if sense in word:
            del word[sense]

    def senses(self, word: Word) -> List[Sense]:
        # List all senses registered to a specific word
        return list(self._word(word).values())

    def sense(self, word: Word, sense: str) -> Union[Sense, None]:
        # Get a specific sense by name for a specific word (if it exists)
        word = self._word(word)
        if sense in word:
            return word[sense]
        return None

    def _word(self, word: Word) -> Dict[str, Sense]:
        if word not in self.words:
            self.words[word] = dict()
        return self.words[word]