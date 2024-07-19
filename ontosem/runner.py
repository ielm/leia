from leia.ontosem.analysis import Analysis, Sentence
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.semantics.compiler import SemanticCompiler
from leia.ontosem.semantics.extended import BasicSemanticsMPProcessor
from leia.ontosem.semantics.scorer import SemanticScorer
from leia.ontosem.syntax.analyzer import Preprocessor, SyntacticAnalyzer
from typing import List

import json
import sys


class OntoSemRunner(object):

    def __init__(self, config: OntoSemConfig):
        self.config = config

    def run_from_file(self, file: str) -> Analysis:
        f = open(file, "r")
        sentences = json.load(f)
        print("\n Read", len(sentences), "sentences.\n")
        f.close()

        return self.run(sentences)

    def run(self, sentences: List[str]) -> Analysis:
        analysis = Analysis(self.config)

        sentences = " ".join(sentences)
        pp = Preprocessor(self.config).run(sentences)
        syn = SyntacticAnalyzer(self.config).run(pp)

        for syntax in syn:
            # For each sentence, refresh the knowledge resources
            ontology = self.config.ontology()
            lexicon = self.config.lexicon()

            # Modify the lexicon, adding the senses generated by syntax
            for sense in syntax.lex_senses:
                lexicon.add_sense(sense)

            candidates = SemanticCompiler(self.config, ontology=ontology, lexicon=lexicon).run(syntax)
            candidates = SemanticScorer(self.config, ontology=ontology, lexicon=lexicon).run(candidates)

            sentence = Sentence(syntax.original_sentence)
            sentence.syntax = syntax
            sentence.semantics = list(candidates)

            analysis.sentences.append(sentence)

        # Perform post-basic semantic MP analysis
        BasicSemanticsMPProcessor(self.config).run(analysis)

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

    for frame in results.sentences[0].semantics[0].basic_tmr.frames.values():
        print(frame.frame_id())
        for p, fillers in frame.properties.items():
            print("--%s = %s" % (p, ",".join(map(lambda f: str(f), fillers))))
    print("----")
    print("SCORE: %f" % results.sentences[0].semantics[0].score)
    print("SCORING:")
    for score in results.sentences[0].semantics[0].scores:
        print("-- %s" % score)

    print(json.dumps(results.to_dict(), indent=2))