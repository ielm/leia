from leia.ontosem.analysis import Analysis, Sentence
from leia.ontosem.cache import OntoSemCache
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.semantics.compiler import SemanticCompiler
from leia.ontosem.semantics.scorer import SemanticScorer
from leia.ontosem.syntax.analyzer import Preprocessor, SpacyAnalyzer, WMLexiconLoader
from leia.ontosem.syntax.synmapper import SynMapper
from leia.ontosem.syntax.transformer import LexicalTransformer
from typing import List

import json
import sys
import time


class OntoSemTimer(object):

    def __init__(self, analysis: Analysis, message: str):
        self.analysis = analysis
        self.message = message
        self.start = None

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.analysis.log("Time to $processor: $time", type="time", processor=self.message, time=time.time() - self.start)


timer = OntoSemTimer


class OntoSemRunner(object):

    def __init__(self, config: OntoSemConfig):
        self.config = config
        self.cache = OntoSemCache(self.config)

    def run_from_file(self, file: str) -> Analysis:
        f = open(file, "r")
        sentences = json.load(f)
        print("\n Read", len(sentences), "sentences.\n")
        f.close()

        return self.run(sentences)

    def run(self, sentences: List[str]) -> Analysis:
        sentences = " ".join(sentences)

        # Define the stages to run; each has a name that can be referenced by the cacheing system, as well as a
        # message for the timer logs.
        stages = [
            {"name": "preprocess", "message": "preprocess", "exec": self._run_stage_preprocessor},
            {"name": "syntax", "message": "run spacy syntax", "exec": self._run_stage_syntax},
            {"name": "build-lex", "message": "build wm-lexicon", "exec": self._run_stage_build_lexicon},
            {"name": "transform", "message": "run transformations", "exec": self._run_stage_transformations},
            {"name": "synmap", "message": "run synmapping", "exec": self._run_stage_synmapping},
            {"name": "basic-sem", "message": "run basic semantic analysis", "exec": self._run_stage_basic_semantics},
        ]
        analysis = None

        # For now, the only valid cache read level is syntax
        if self.config.cache_read_level == "syntax":
            cached = self.cache.load(sentences)
            if cached is not None:
                analysis = cached

                # Remove the proprocess and syntax stages to prevent them from running
                stages = list(filter(lambda stage: stage["name"] != "preprocess", stages))
                stages = list(filter(lambda stage: stage["name"] != "syntax", stages))

        # Create a new analysis object if no cached version was loaded
        if analysis is None:
            analysis = Analysis(self.config, text=sentences)

        # Load any memory components that haven't yet been loaded
        self._load_memory(analysis)

        # Now run all stages
        for stage in stages:
            # Time the stage and log the results
            with timer(analysis, stage["message"]):
                stage["exec"](analysis)

            # Cache the results if this is the specified write level
            if stage["name"] == self.config.cache_write_level:
                self.cache.cache(analysis)

        # Return the results
        return analysis

    def _load_memory(self, analysis: Analysis):
        if not self.config.memory().properties.is_loaded():
            with timer(analysis, "load properties"):
                self.config.memory().properties.load()

        if not self.config.memory().ontology.is_loaded():
            with timer(analysis, "load ontology"):
                self.config.memory().ontology.load()

        if not self.config.memory().lexicon.is_loaded():
            with timer(analysis, "load lexicon"):
                self.config.memory().lexicon.load()

        if not self.config.memory().transformations.is_loaded():
            with timer(analysis, "load transformations"):
                self.config.memory().transformations.load()

        if not self.config.memory().parts_of_speech.is_loaded():
            with timer(analysis, "load parts of speech"):
                self.config.memory().parts_of_speech.load()

    def _run_stage_preprocessor(self, analysis: Analysis):
        pp = Preprocessor(analysis).run(analysis.text)
        analysis.text = pp

    def _run_stage_syntax(self, analysis: Analysis):
        syntax = SpacyAnalyzer(analysis).run(analysis.text)
        for s in syntax:
            sentence = Sentence(s.original_sentence)
            sentence.syntax = s
            analysis.sentences.append(sentence)

    def _run_stage_build_lexicon(self, analysis: Analysis):
        WMLexiconLoader(analysis).run(list(map(lambda s: s.syntax, analysis.sentences)))

    def _run_stage_transformations(self, analysis: Analysis):
        for s in analysis.sentences:
            LexicalTransformer(analysis).run(s.syntax)

    def _run_stage_synmapping(self, analysis: Analysis):
        for sentence in analysis.sentences:
            synmap = SynMapper(analysis).run(sentence.syntax)
            sentence.syntax.synmap = synmap

    def _run_stage_basic_semantics(self, analysis: Analysis):
        for sentence in analysis.sentences:
            candidates = SemanticCompiler(analysis).run(sentence.syntax)
            candidates = SemanticScorer(analysis).run(candidates)

            sentence.semantics = list(candidates)


if __name__ == "__main__":
    arguments = sys.argv

    if len(arguments) < 2 or (len(arguments) == 2 and arguments[1].startswith("config=")):
        print("Correct usage: runner.py \"Input text here.\"")
        print("Optional config parameter: runner.py config=ontosem.yml \"Input text here.\"")

    arguments = arguments[1:]

    config = OntoSemConfig()
    if arguments[0].startswith("config="):
        config_file = arguments[0].replace("config=", "")
        config = OntoSemConfig().from_file(config_file)
        arguments = arguments[1:]

    sentence = arguments[0]

    config.init_ontomem()

    runner = OntoSemRunner(config)

    results = runner.run([sentence])
    for log in results.logs:
        print("%s%s" % ("(cached)" if log["cached"] else "", log["message"]))

    print("----")

    for frame in results.sentences[0].semantics[0].basic_tmr.instances():
        print(frame.id())
        for p, fillers in frame.properties.items():
            print("--%s = %s" % (p, ",".join(map(lambda f: str(f.value()), fillers))))
    print("----")
    print("SCORE: %f" % results.sentences[0].semantics[0].score)
    print("SCORING:")
    for score in results.sentences[0].semantics[0].scores:
        print("-- %s" % score)

    print(json.dumps(results.to_dict(), indent=2))