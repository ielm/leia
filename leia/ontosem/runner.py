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

        if not config.memory().properties.is_loaded():
            with timer(analysis, "load properties"):
                config.memory().properties.load()

        if not config.memory().ontology.is_loaded():
            with timer(analysis, "load ontology"):
                config.memory().ontology.load()

        if not config.memory().lexicon.is_loaded():
            with timer(analysis, "load lexicon"):
                config.memory().lexicon.load()

        if not config.memory().parts_of_speech.is_loaded():
            with timer(analysis, "load parts of speech"):
                config.memory().parts_of_speech.load()

        sentences = " ".join(sentences)

        with timer(analysis, "preprocess"):
            pp = Preprocessor(analysis).run(sentences)

        with timer(analysis, "run spacy syntax"):
            syntax = SpacyAnalyzer(analysis).run(pp)
            for s in syntax:
                sentence = Sentence(s.original_sentence)
                sentence.syntax = s
                analysis.sentences.append(sentence)

        with timer(analysis, "build wm-lexicon"):
            WMLexiconLoader(analysis).run(syntax)

        # TODO: Transformations here

        with timer(analysis, "run synmapping"):
            for sentence in analysis.sentences:
                synmap = SynMapper(analysis).run(sentence.syntax)
                sentence.syntax.synmap = synmap

        with timer(analysis, "run basic semantic analysis"):
            for sentence in analysis.sentences:
                candidates = SemanticCompiler(analysis).run(sentence.syntax)
                candidates = SemanticScorer(analysis).run(candidates)

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

    results = runner.run([sentence])
    for log in results.logs:
        print(log.msg["message"])

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