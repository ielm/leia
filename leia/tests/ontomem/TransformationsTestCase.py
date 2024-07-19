from leia.ontomem.memory import Memory
from leia.ontomem.lexicon import SynStruc
from leia.ontomem.transformations import Transformation, TransformationsCatalogue, TransformationExecutable, TransformationSynStruc
from unittest import TestCase


class TestTransformationExecutable(TransformationExecutable): pass


class TransformationsCatalogueTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")
        self.c = TransformationsCatalogue(self.m, "", load_now=False)

    def test_transformations(self):
        self.assertEqual([], self.c.transformations())

        t1 = Transformation("T1")
        t2 = Transformation("T2")
        t3 = Transformation("T3")

        # Transformations can be added
        self.c.add_transformation(t1)

        self.assertEqual([t1], self.c.transformations())

        self.c.add_transformation(t2)
        self.c.add_transformation(t3)

        self.assertEqual([t1, t2, t3], self.c.transformations())

        # Transformations can be requested by name
        self.assertEqual(t1, self.c.transformation("T1"))

        # Transformations can be removed by references
        self.c.remove_transformation(t3)

        self.assertEqual([t1, t2], self.c.transformations())

        # Transformations ca be removed by name
        self.c.remove_transformation("T2")

        self.assertEqual([t1], self.c.transformations())

        # Unknown transformation removals are ignored
        self.c.remove_transformation("TX")

        # Unknown transformation requests return None
        self.assertIsNone(self.c.transformation("T2"))


class TransformationTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_index(self):
        content = {
            "name": "Passivization of transitive and optionally transitive verbs",
            "example": "A sandwich was eaten by a chicken.",
            "syn-struc": {
                "vars": {
                    "0": {"pos": ["v"], "tag": ["trans"]}
                },
                "patterns": [
                    [
                        {"type": "dependency", "deptype": "nsubjpass", "governor": 0}
                    ],
                    [
                        {"type": "constituency", "contype": "NP", "children": []},
                        {"type": "token", "lemma": ["be"], "pos": None, "morph": {}},
                        {"type": "token", "lemma": [], "pos": ["V"], "var": 0, "morph": {"tense": "past", "verbform": "part"}}
                    ]
                ]
            },
            "executable": "*leia.tests.ontomem.TransformationsTestCase.TestTransformationExecutable"
        }

        trans = Transformation(content["name"], contents=content)

        self.assertEqual(content["example"], trans.example)
        self.assertEqual(TransformationSynStruc(content["syn-struc"]), trans.synstruc)
        self.assertEqual(TestTransformationExecutable.__name__, trans.executable.__name__)


class TransformationSynStrucTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_index(self):
        content = {
            "vars": {
                "0": {"pos": ["v"], "tag": ["trans"]}
            },
            "patterns": [
                [
                    {"type": "dependency", "deptype": "nsubjpass", "governor": 0}
                ],
                [
                    {"type": "constituency", "contype": "NP", "children": []},
                    {"type": "token", "lemma": ["be"], "pos": None, "morph": {}},
                    {"type": "token", "lemma": [], "pos": "V", "var": 0, "morph": {"tense": "past", "verbform": "part"}}
                ]
            ]
        }

        synstruc = TransformationSynStruc(contents=content)

        self.assertEqual([
            TransformationSynStruc.Variable(0, ["v"], ["trans"])
        ], synstruc.variables)

        self.assertEqual([
            [
                TransformationSynStruc.DependencyElement("nsubjpass", None, False, 0, None)
            ],
            [
                SynStruc.ConstituencyElement("NP", [], None, False),
                SynStruc.TokenElement({"be"}, None, {}, None, False),
                SynStruc.TokenElement(set(), "V", {"tense": "past", "verbform": "part"}, 0, False)
            ]
        ], synstruc.patterns)
