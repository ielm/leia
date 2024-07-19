from leia.ontomem.lexicon import Sense, SynStruc
from leia.ontomem.transformations import TransformationExecutable
from leia.ontosem.syntax.synmapper import SynMatcher
from typing import List, Tuple


class PassivizationOfTransVerbs(TransformationExecutable):

    def run(
        self,
        sense: Sense,
        synmatch_result: SynMatcher.SynMatchResult,
        alignment: List[Tuple[SynStruc.Element, SynStruc.Element]],
    ):
        sense.synstruc = SynStruc()
        sense.synstruc.elements = [
            SynStruc.DependencyElement("NSUBJPASS", None, None, 2, False),
            SynStruc.TokenElement({"be"}, "V", dict(), 3, False),
            SynStruc.DependencyElement("AUXPASS", None, None, None, False),
            SynStruc.RootElement(),
            SynStruc.ConstituencyElement(
                "PP",
                [
                    SynStruc.ConstituencyElement(
                        "IN",
                        [
                            SynStruc.TokenElement({"by"}, "ADP", dict(), 4, False),
                        ],
                        None,
                        False,
                    ),
                    SynStruc.ConstituencyElement(
                        "NP",
                        [
                            SynStruc.ConstituencyElement(
                                "NN",
                                [SynStruc.TokenElement(set(), "N", dict(), 1, False)],
                                None,
                                False,
                            )
                        ],
                        None,
                        False,
                    ),
                ],
                None,
                True,
            ),
        ]

        sense.semstruc.head().contents["AGENT"] = "^$VAR1"
        sense.semstruc.head().contents["THEME"] = "^$VAR2"

        sense.semstruc.data["^$VAR2"] = {"DISCOURSE-STATUS": "TOPIC"}

        sense.semstruc.data["^$VAR4"] = {"NULL-SEM": "+"}
