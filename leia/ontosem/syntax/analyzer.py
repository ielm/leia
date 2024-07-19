from leia.ontomem.lexicon import Sense
from leia.ontosem.analysis import Analysis, WMLexicon
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import Syntax, Word
from typing import List

import subprocess


class Preprocessor(object):

    def __init__(self, analysis: Analysis):
        self.analysis = analysis

    def run(self, text: str) -> str:
        return self.split_all_negation_aux_contractions(text.lstrip())

    def split_all_negation_aux_contractions(self, sentence: str) -> str:
        sentence = sentence.replace("’", "'") \
            .replace("can't", "can not") \
            .replace("cannot", "can not") \
            .replace("couldn't", "could not") \
            .replace("don't", "do not") \
            .replace("didn't", "did not") \
            .replace("doesn't", "does not") \
            .replace("isn't", "is not") \
            .replace("wasn't", "was not") \
            .replace("weren't", "were not") \
            .replace("aren't", "are not") \
            .replace("mustn't", "must not") \
            .replace("won't", "will not") \
            .replace("shouldn't", "should not") \
            .replace("wouldn't", "would not") \
            .replace("Let's", "Let us") \
            .replace("let's", "let us") \
            .replace("mightn't", "might not") \
            .replace("<p>", "") \
            .replace("</p>", "") \
            .replace("***", "") \
            .replace("***", "")
        return sentence


class SpacyAnalyzer(object):

    def __init__(self, analysis: Analysis):
        self.analysis = analysis

    def run(self, text: str) -> List[Syntax]:
        # Doing the imports here rather than at the top, as the first-time imports load the data models which can be
        # very slow.  By keeping it here, that only happens if run is actually called (rather than, say, throughout
        # various tests that don't touch this method).

        import benepar
        import coreferee
        import en_core_web_lg
        import spacy
        import warnings

        nlp = en_core_web_lg.load()
        nlp.add_pipe("benepar", config={"model": "benepar_en3"})
        nlp.add_pipe("coreferee")

        # Wrap the nlp(text) call in a warning suppression; benepar throws a warning up that doesn't prevent functionality
        # but does write to sys.err; we don't need it (and can't control it), so just suppress it here.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            doc = nlp(text)

        results = list(map(lambda sent: Syntax.from_spacy(sent), doc.sents))

        return results


class WMLexiconLoader(object):

    def __init__(self, analysis: Analysis):
        self.analysis = analysis
        self._generated_indexes = dict()

    def run(self, syntax: List[Syntax]):
        for sentence in syntax:
            for word in sentence.words:
                for sense in self.get_senses_for_word(word):
                    self.analysis.lexicon.add_sense(word, sense)

    def get_senses_for_word(self, word: Word) -> List[Sense]:
        truth = self.analysis.config.lexicon()
        lemma = word.lemma.upper()

        senses = list(truth.word(lemma).senses())

        if len(senses) == 0:
            senses = [self.generate_sense_for_word(word)]

        return senses

    def generate_sense_for_word(self, word: Word) -> Sense:
        partial_id = "%s-%s" % (word.lemma.upper(), word.pos[0])
        if partial_id not in self._generated_indexes:
            self._generated_indexes[partial_id] = 0

        index = self._generated_indexes[partial_id] + 1
        self._generated_indexes[partial_id] = index

        id = "%s%d?" % (partial_id, index)

        semstruc_options = {
            "NOUN": "OBJECT",
            "VERB": "EVENT",
            "ADJ": "PROPERTY",
            "ADV": "PROPERTY",
        }

        semstruc = "ALL"
        for pos in word.pos:
            if pos in semstruc_options:
                semstruc = semstruc_options[pos]
                break

        sense = Sense(self.analysis.config.memory(), id, contents={
            "SENSE": id,
            "WORD": word.lemma.upper(),
            "CAT": word.pos,
            "SYN-STRUC": [{"type": "root"}],
            "SEM-STRUC": semstruc,
            "MEANING-PROCEDURES": []
        })

        return sense


class SyntacticAnalyzer(object):

    def __init__(self, config: OntoSemConfig):
        self.config = config

    def run(self, text: str) -> List[Syntax]:
        # 1) Run syntax
        syntax = self._run_syntax(text)

        # 2) Parse results
        syntax = Syntax.from_lisp_string(syntax)

        # 3) Return results
        return syntax

    def _run_syntax(self, text: str) -> str:
        host = "localhost"
        port = 4998

        type = "default"
        lexicon = "ontosyn/lisp/lexicon.lisp"
        mem_file = "build/ontosem2-new4.mem"

        lisp_exe = '(run-syntax \'%s \"%s\" \"%s\" \"%s\" %d)' % (type, lexicon, text, host, port)

        cmd = 'clisp -q --silent -M %s' % mem_file

        proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(str.encode(lisp_exe))

        out = out.decode('ascii')
        out = "\n".join(out.split("\n")[1:])

        return out

if __name__ == "__main__":

    config = OntoSemConfig()
    syntax = SyntacticAnalyzer(config).run("Kick the building. The store was hit by the woman.")
    print(syntax)
