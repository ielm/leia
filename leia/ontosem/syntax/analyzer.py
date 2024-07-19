from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.results import Syntax
from typing import List

import subprocess


class Preprocessor(object):

    def __init__(self, config: OntoSemConfig):
        self.config = config

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
        host = self.config.corenlp_host
        port = self.config.corenlp_port

        type = "default"
        lexicon = self.config.ontosyn_lexicon
        mem_file = self.config.ontosyn_mem

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
