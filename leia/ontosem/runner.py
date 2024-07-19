from leia.ontosem.analysis import Analysis, Sentence
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.semantics.compiler import SemanticCompiler
from leia.ontosem.semantics.extended import BasicSemanticsMPProcessor
from leia.ontosem.semantics.scorer import SemanticScorer
from leia.ontosem.syntax.analyzer import Preprocessor, SpacyAnalyzer, SyntacticAnalyzer, WMLexiconLoader
from leia.ontosem.syntax.synmapper import SynMapper
from typing import List, Tuple

import json
import sys
import time


class OntoSemTimedResults(object):

    def __init__(self):
        self.results = []

    def add(self, message: str, total_time: float):
        self.results.append((message, total_time))

    def __str__(self):
        return "\n".join(map(lambda r: "Total time to %s: %f" % (r[0], r[1]), self.results))


class OntoSemTimer(object):

    def __init__(self, message: str, timed_results: OntoSemTimedResults):
        self.message = message
        self.timed_results = timed_results
        self.start = None

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.timed_results.add(self.message, time.time() - self.start)


timer = OntoSemTimer


class OntoSemRunner(object):

    def __init__(self, config: OntoSemConfig):
        self.config = config
        self.timed_results = OntoSemTimedResults()

        print("WARNING: Overriding ontosyn_lexicon path to '%s'" % "ontosyn/lisp/lexicon.lisp")
        self.config.ontosyn_lexicon = "ontosyn/lisp/lexicon.lisp"

    def run_from_file(self, file: str) -> Analysis:
        f = open(file, "r")
        sentences = json.load(f)
        print("\n Read", len(sentences), "sentences.\n")
        f.close()

        return self.run(sentences)

    def run(self, sentences: List[str]) -> Analysis:
        analysis = Analysis(self.config)

        sentences = " ".join(sentences)

        with timer("preprocess", self.timed_results):
            pp = Preprocessor(self.config).run(sentences)

        with timer("syntax", self.timed_results):
            syntax = SpacyAnalyzer(self.config).run(pp)
            for s in syntax:
                sentence = Sentence(s.original_sentence)
                sentence.syntax = s
                analysis.sentences.append(sentence)

        with timer("build wm-lexicon", self.timed_results):
            WMLexiconLoader(self.config).run(analysis.lexicon, syntax)

        # TODO: Transformations here

        with timer("synmapping", self.timed_results):
            for sentence in analysis.sentences:
                synmap = SynMapper(self.config, self.config.memory().ontology, analysis.lexicon).run(sentence.syntax)
                sentence.syntax.synmap = synmap

        with timer("basic semantic analysis", self.timed_results):
            for sentence in analysis.sentences:
                ontology = self.config.ontology()
                lexicon = self.config.lexicon()     # TODO: This needs to be updated to the WMLexicon

                candidates = SemanticCompiler(self.config, ontology=ontology, lexicon=lexicon).run(sentence.syntax)
                candidates = SemanticScorer(self.config, ontology=ontology, lexicon=lexicon).run(candidates)

                sentence.semantics = list(candidates)

        # Perform post-basic semantic MP analysis
        # with timer("semantic MP analysis", self.timed_results):
        #     BasicSemanticsMPProcessor(self.config).run(analysis)

        return analysis


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
    with timer("load knowledge", runner.timed_results):
        config.memory().properties.load()
        config.memory().ontology.load()
        config.memory().lexicon.load()

    results = runner.run([sentence])

    print(runner.timed_results)
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