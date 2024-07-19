from ontomem.memory import Memory
from typing import Union

import json
import os


class Lexicon(object):

    def __init__(self, memory: Memory, contents_dir: str, load_now: bool=True):
        self.memory = memory
        self.contents_dir = contents_dir
        self.cache = {}

        if load_now:
            self.load()

    def load(self):
        # This method has been added to mirror the ontology loading pattern; the lexicon is intended to be
        # lazy loaded, so this method does nothing for now.  In the future, should something be needed as
        # part of an initial load, it can be placed here.
        pass

    def word(self, word: str) -> 'Word':
        # 1) Check the cache
        if word in self.cache:
            return self.cache[word]

        # 2) Lazy load from the contents_dir
        loaded = self.load_word(word)
        if loaded is not None:
            self.cache[word] = loaded
            return loaded

        # 3) Create a new (empty) word
        created = self.create_word(word)
        self.cache[word] = created
        return created

    def load_word(self, word: str) -> Union['Word', None]:
        try:
            with open("%s/%s.word" % (self.contents_dir, word), "r") as f:
                return Word(self.memory, word, contents=json.load(f))
        except FileNotFoundError:
            return None

    def create_word(self, word: str) -> 'Word':
        return Word(self.memory, word)

    def sense(self, sense: str) -> 'Sense':
        word = self.word(sense[0:sense.rfind("-")])
        return word.sense(sense)


class Word(object):

    def __init__(self, memory: Memory, name: str, contents: dict=None):
        self.memory = memory
        self.name = name
        self.contents = contents if contents is not None else {
            "name": self.name,
            "senses": {}
        }

    def sense(self, sense: str) -> 'Sense':
        if sense in self.contents["senses"]:
            return Sense(self.memory, sense, contents=self.contents["senses"][sense])

        raise Exception("Unknown sense %s." % sense)

    def __eq__(self, other):
        if isinstance(other, Word):
            return self.name == other.name and self.contents == other.contents


class Sense(object):

    def __init__(self, memory: Memory, name: str, contents: dict=None):
        self.memory = memory
        self.name = name
        self.contents = contents if contents is not None else {}

    def __eq__(self, other):
        if isinstance(other, Sense):
            return self.name == other.name and self.contents == other.contents


if __name__ == "__main__":

    knowledge_dir = "%s/knowledge/words" % os.getcwd()

    memory = Memory("", "", knowledge_dir)
    lexicon = memory.lexicon

    import time
    start = time.time()
    lexicon.load()
    print("Time to load: %s" % str(time.time() - start))

    start = time.time()
    print(lexicon.word("BE").contents)
    print("Time to load BE: %s" % str(time.time() - start))

    start = time.time()
    print(lexicon.word("BE").contents)
    print("Time to read BE from cache: %s" % str(time.time() - start))

    start = time.time()
    print(lexicon.sense("BE-V1").contents)
    print(lexicon.sense("BE-V2").contents)
    print("Time to read BE-V1 and BE-V2 from cache: %s" % str(time.time() - start))