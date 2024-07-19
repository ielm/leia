from leia.ontomem.lexicon import Sense, SynStruc
from leia.ontomem.memory import Memory
from leia.ontosem.analysis import Analysis
from leia.ontosem.syntax.synmapper import SynMatcher
from leia.ontosem.syntax.transformations.passivization import PassivizationOfTransVerbs
from leia.tests.LEIATestCase import LEIATestCase


class PassivizationOfTransVerbsTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory()

    def test_run(self):
        # The current contents of the syn-struc do not matter.
        # The current contents of the sem-struc will be augmented.
        sense = Sense(self.m, "TEST-V1", contents=self.mockSense("TEST-V1", semstruc={"TEST": {"AGENT": "^$VAR2", "THEME": "^$VAR1"}}))

        # This transformer doesn't care about any of the matches or alignments; so they can all be blank.
        analysis = Analysis()
        synmatch = SynMatcher.SynMatchResult([])
        alignment = []

        # Run the transformer
        transformer = PassivizationOfTransVerbs(analysis)
        transformer.run(sense, synmatch, alignment)

        # Verify the syn-struc has been modified
        expected = SynStruc(contents=[
            {"type": "dependency", "deptype": "NSUBJPASS", "var": 2},
            {"type": "token", "lemma": ["be"], "pos": "V", "morph": {}, "var": 3},
            {"type": "dependency", "deptype": "AUXPASS"},
            {"type": "root"},
            {"type": "constituency", "contype": "PP", "opt": True, "children": [
                {"type": "constituency", "contype": "IN", "children": [
                    {"type": "token", "lemma": ["by"], "pos": "ADP", "morph": {}, "var": 4},
                ]},
                {"type": "constituency", "contype": "NP", "children": [
                    {"type": "constituency", "contype": "NN", "children": [
                        {"type": "token", "lemma": [], "pos": "N", "morph": {}, "var": 1},
                    ]}
                ]}
            ]},
        ])

        self.assertEqual(expected, sense.synstruc)

        # Verify the sem-struc has been modified
        self.assertEqual("^$VAR1", sense.semstruc.data["TEST"]["AGENT"])
        self.assertEqual("^$VAR2", sense.semstruc.data["TEST"]["THEME"])