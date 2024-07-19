from leia.ontosem.analysis import Analysis
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.semantics.candidate import Score
from leia.ontosem.semantics.tmr import TMR, TMRInstance
from leia.ontosem.syntax.results import LispParser
from typing import Dict, List, Tuple

import json
import subprocess


class BasicSemanticsMPProcessor(object):

    def __init__(self, config: OntoSemConfig):
        self.config = config

    def run(self, analysis: Analysis) -> Analysis:
        # 1) Call the LISP process, passing the analysis object
        extended = self._run_basic_semantics_mp_processor(analysis)

        # 2) Parse the results into a set of TMRs with candidate IDs
        extended = self._parse_lisp_tmrs(extended)

        # 3) Add the candidates as "extended-tmr" to the corresponding candidates
        self._assign_extended_tmrs_to_candidates(analysis, extended)

        return analysis

    def _run_basic_semantics_mp_processor(self, analysis: Analysis) -> str:
        mem_file = "build/post-basic-semantic-MPs.mem"

        analysis = json.dumps(analysis.to_dict())
        analysis = analysis.replace('"', '\\"')

        lisp_exe = '(post-basic-semantic-MPs "%s")' % analysis
        cmd = "clisp -q --silent -M %s" % mem_file

        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate(str.encode(lisp_exe))

        out = out.decode("ascii")
        out = "\n".join(out.split("\n")[1:])

        return out

    def _parse_lisp_tmrs(
        self, lisp: str
    ) -> Dict[str, Tuple[TMR, List["ExtendedScorePlaceholder"]]]:
        # Returns a mapping of candidate ids to extended TMRs and scores

        # 1) Parse the lisp string into python lists
        data = LispParser.lisp_to_list(lisp)[0]

        # 2) Each element represents a candidate; iterate through each and parse them
        results = {}
        for candidate in data:
            candidate_id = LispParser.list_key_to_value(candidate, "ID")[1]

            if candidate_id.startswith('"'):
                candidate_id = candidate_id[1:]
            if candidate_id.endswith('"'):
                candidate_id = candidate_id[:-1]

            tmr_content = LispParser.list_key_to_value(candidate, "EXTENDED-TMR")[1]
            frames = LispParser.list_key_to_value(tmr_content, "FRAMES")[1]
            scores = LispParser.list_key_to_value(candidate, "SCORES")[1]

            extended_tmr = TMR(self.config.memory(), private=True)

            if frames == "NIL":
                frames = []

            for frame in frames:
                self._lisp_to_frame(extended_tmr, frame)

            scores = list(
                map(lambda score: ExtendedScorePlaceholder.parse_lisp(score), scores)
            )

            results[candidate_id] = (extended_tmr, scores)

        return results

    def _lisp_to_frame(self, tmr: TMR, input: list) -> TMRInstance:

        # First, parse the id and related components, make the frame, and register it with the TMR
        fid = LispParser.list_key_to_value(input, "ID")[1]
        concept = LispParser.list_key_to_value(input, "CONCEPT")[1]
        instance = int(LispParser.list_key_to_value(input, "INSTANCE")[1])

        frame = TMRInstance(tmr.memory, concept, instance)
        tmr.register_instance(frame)

        # Now parse the properties
        properties = LispParser.list_key_to_value(input, "PROPERTIES")[1]
        if properties == "NIL":
            properties = []

        def _convert_filler(filler):
            try:
                return int(filler)
            except:
                pass

            try:
                return float(filler)
            except:
                pass

            return filler

        for property in properties:
            if property[1] == "NIL":
                continue

            slot = property[0]
            for filler in property[1]:
                frame.add_filler(slot, _convert_filler(filler))

        # Now parse the resolutions
        resolutions = LispParser.list_key_to_value(input, "RESOLUTIONS")[1]
        if resolutions == "NIL":
            resolutions = []

        for resolution in resolutions:
            frame.resolutions.add(resolution)

        return frame

    def _assign_extended_tmrs_to_candidates(
        self,
        analysis: Analysis,
        extended: Dict[str, Tuple[TMR, List["ExtendedScorePlaceholder"]]],
    ):
        for sentence in analysis.sentences:
            for candidate in sentence.semantics:
                if candidate.id in extended:
                    candidate.extended_tmr = extended[candidate.id][0]
                    for score in extended[candidate.id][1]:
                        candidate.scores.append(score)


class ExtendedScorePlaceholder(Score):

    @classmethod
    def parse_lisp(cls, lisp: list) -> "ExtendedScorePlaceholder":
        name = LispParser.list_key_to_value(lisp, "TYPE")[1]
        score = float(LispParser.list_key_to_value(lisp, "SCORE")[1])
        message = LispParser.list_key_to_value(lisp, "MESSAGE")[1]

        if message.startswith('"'):
            message = message[1:]
        if message.endswith('"'):
            message = message[:-1]

        return ExtendedScorePlaceholder(name, score, message)

    def __init__(self, name: str, score: float, message: str):
        super().__init__(score, message)
        self.name = name

    def to_dict(self) -> dict:
        return {"type": self.name, "score": self.score, "message": self.message}

    def __repr__(self):
        return "ExtendedScorePlaceholder %s %f: '%s'" % (
            self.name,
            self.score,
            self.message,
        )


if __name__ == "__main__":
    import pickle

    results = pickle.load(open("/Users/ivan/Dropbox/leia/analysis.p", "rb"))
    print(results.to_dict())

    results = BasicSemanticsMPProcessor(OntoSemConfig()).run(results)
    print(results.to_dict())
