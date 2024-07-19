from leia.ontosem.config import OntoSemConfig
from leia.ontomem.lexicon import Sense
from leia.ontosem.semantics.candidate import Candidate
from leia.ontosem.syntax.results import Syntax, Word
from logging import Handler, Logger, LogRecord
from string import Template
from typing import Dict, List, Type, Union

import logging


class Analysis(object):

    class LogHandler(Handler):

        def __init__(self, logs: List[dict], level="INFO"):
            super().__init__(level=level)
            self.logs = logs

        def emit(self, record: LogRecord):
            message = dict(record.msg)
            message["time"] = record.created
            message["level"] = record.levelname
            message["cached"] = False

            self.logs.append(message)

    @classmethod
    def from_dict(cls, input: dict) -> 'Analysis':
        analysis = Analysis()
        analysis.config = OntoSemConfig.from_dict(input["config"])
        analysis.sentences = list(map(lambda s: Sentence.from_dict(s), input["sentences"]))
        analysis.logs.extend(input["logs"])
        analysis.text = input["text"]

        # TODO: Parse WMLexicon if present

        return analysis

    def __init__(self, config: OntoSemConfig=None, text: str=None):
        self.config = config if config is not None else OntoSemConfig()
        self.sentences: List[Sentence] = []
        self.lexicon = WMLexicon()
        self.text = text

        self.logs: List[dict] = []
        self._logger = Logger(Analysis.__name__, level="INFO")
        self._logger.addHandler(Analysis.LogHandler(self.logs, level="INFO"))

    def log(self, template: str, type: str="std", level: str="INFO", source: Type=None, **details):
        if source == None:
            source = Analysis

        level = getattr(logging, level)

        self._logger.log(level, {
            "type": type,
            "source": source.__name__,
            "template": template,
            "details": dict(**details),
            "message": Template(template).substitute(**details),
        })

    def to_dict(self) -> dict:
        return {
            "config": self.config.to_dict(),
            "sentences": list(map(lambda s: s.to_dict(), self.sentences)),
            "logs": self.logs,
            "text": self.text
        }


class Sentence(object):

    @classmethod
    def from_dict(cls, input: dict) -> 'Sentence':
        sentence = Sentence(input["text"])
        sentence.syntax = Syntax.from_dict(input["syntax"])

        # TODO: Parse semantics if present

        return sentence

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