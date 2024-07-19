from leia.ontomem.lexicon import Sense, SynStruc
from leia.ontomem.transformations import TransformationExecutable
from leia.ontosem.syntax.synmapper import SynMatcher
from typing import List, Tuple


class PassivizationOfTransVerbs(TransformationExecutable):

    def run(self, sense: Sense, synmatch_result: SynMatcher.SynMatchResult, alignment: List[Tuple[SynStruc.Element, SynStruc.Element]]):
        pass