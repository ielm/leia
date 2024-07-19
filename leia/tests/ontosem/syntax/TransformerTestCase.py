from leia.ontomem.lexicon import SynStruc
from leia.ontosem.analysis import Analysis
from leia.ontosem.syntax.results import ConstituencyNode, Dependency
from leia.ontosem.syntax.synmapper import SynMatcher
from leia.ontosem.syntax.transformer import LexicalTransformer
from leia.tests.LEIATestCase import LEIATestCase


class LexicalTransformerTestCase(LEIATestCase):

    def setUp(self):
        self.analysis = Analysis()

    def test_root_for_match(self):
        transformer = LexicalTransformer(self.analysis)
        match = SynMatcher.SynMatchResult([])

        word1 = self.mockWord(1, "A", "N")
        word2 = self.mockWord(2, "B", "N")

        # If there is no var 0 in the match, then a null root is returned
        self.assertIsNone(transformer.root_for_match(match))

        # If var 0 is a root element, then the corresponding token is returned
        match.matches = [SynMatcher.RootMatch(
            SynStruc.RootElement(),
            word1
        )]
        self.assertEqual(word1, transformer.root_for_match(match))

        # If var 0 is a token element, then the corresponding token is returned
        match.matches = [SynMatcher.TokenMatch(
            SynStruc.TokenElement({"A"}, "N", dict(), 0, False),
            word1
        )]
        self.assertEqual(word1, transformer.root_for_match(match))

        # If var 0 is a dependency element, then the dependent token is returned
        match.matches = [
            SynMatcher.DependencyMatch(
                SynStruc.DependencyElement("NSUBJ", None, None, 0, False),
                Dependency(word1, word2, "NSUBJ")
            )
        ]
        self.assertEqual(word2, transformer.root_for_match(match))

        # If var 0 is a constituency element, then the leftmost token is returned
        element = SynStruc.ConstituencyElement("NP", [
            SynStruc.TokenElement({"A"}, "N", dict(), None, False),
            SynStruc.TokenElement({"B"}, "N", dict(), None, False),
        ], 0, False)

        node = ConstituencyNode("NP")
        node.children = [
            word1, word2
        ]

        match.matches = [
            SynMatcher.ConstituencyMatch(
                element, node, [
                    SynMatcher.TokenMatch(element.children[0], word1),
                    SynMatcher.TokenMatch(element.children[1], word2),
                ]
            )
        ]
        self.assertEqual(word1, transformer.root_for_match(match))

    def test_align_syn_strucs_root_element(self):
        transformer = LexicalTransformer(self.analysis)

        # Simple root element match
        syn1 = SynStruc()
        syn2 = SynStruc()

        expectation = SynStruc.RootElement()
        match = SynStruc.RootElement()

        # No available match
        syn1.elements = [expectation]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # A match is found
        syn2.elements = [match]
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

    def test_align_syn_strucs_token_element(self):
        transformer = LexicalTransformer(self.analysis)

        syn1 = SynStruc()
        syn2 = SynStruc()

        expectation = SynStruc.TokenElement({"A", "B"}, "N", {"x": 1, "y": 2}, None, False)

        # No available match
        syn1.elements = [expectation]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # An exact match is found
        match = SynStruc.TokenElement({"A", "B"}, "N", {"x": 1, "y": 2}, None, False)
        syn2.elements = [match]
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Optionality flags do not need to match
        match.optional = True
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Extra morphology can be defined in the second syn-struc
        match.morph["z"] = 3
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Extra lemmas can be defined in the second syn-struc
        match.lemmas = {"A", "B", "C"}
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Missing lemmas is not a match
        syn2.elements = [SynStruc.TokenElement({"A"}, "N", {"x": 1, "y": 2}, None, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Differing POS is not a match
        syn2.elements = [SynStruc.TokenElement({"A", "B"}, "V", {"x": 1, "y": 2}, None, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Missing morphology is not a match
        syn2.elements = [SynStruc.TokenElement({"A", "B"}, "N", {"x": 1}, None, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Different variables is not a match
        syn2.elements = [SynStruc.TokenElement({"A", "B"}, "N", {"x": 1, "y": 2}, 123, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

    def test_align_syn_strucs_dependency_element(self):
        transformer = LexicalTransformer(self.analysis)

        syn1 = SynStruc()
        syn2 = SynStruc()

        expectation = SynStruc.DependencyElement("NSUBJ", None, None, None, False)
        match = SynStruc.DependencyElement("NSUBJ", None, None, None, False)

        # No available match
        syn1.elements = [expectation]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # An exact match is found
        syn2.elements = [match]
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Optionality flags do not need to match
        match.optional = True
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Differing types is not a match
        syn2.elements = [SynStruc.DependencyElement("DOBJ", None, None, None, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Differing governors is not a match
        syn2.elements = [SynStruc.DependencyElement("NSUBJ", 123, None, None, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Differing dependents is not a match
        syn2.elements = [SynStruc.DependencyElement("NSUBJ", None, 123, None, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Differing variables is not a match
        syn2.elements = [SynStruc.DependencyElement("NSUBJ", None, None, 123, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

    def test_align_syn_strucs_constituency_element(self):
        transformer = LexicalTransformer(self.analysis)

        syn1 = SynStruc()
        syn2 = SynStruc()

        expectation = SynStruc.ConstituencyElement("NP", [
            SynStruc.TokenElement({"A", "B"}, "N", {"x": 1, "y": 2}, None, False)
        ], None, False)
        match = SynStruc.ConstituencyElement("NP", [
            SynStruc.TokenElement({"A", "B"}, "N", {"x": 1, "y": 2}, None, False)
        ], None, False)

        # No available match
        syn1.elements = [expectation]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # An exact match is found
        syn2.elements = [match]
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Optionality flags do not need to match
        match.optional = True
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Additional children can be found in the second syn-struc
        match.children.append(SynStruc.TokenElement({"C", "D"}, "V", dict(), None, False))

        # Differing types is not a match
        syn2.elements = [SynStruc.ConstituencyElement("VP", [
            SynStruc.TokenElement({"A", "B"}, "N", {"x": 1, "y": 2}, None, False)
        ], None, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Missing children is not a match
        syn2.elements = [SynStruc.ConstituencyElement("VP", [], None, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Differing variables is not a match
        syn2.elements = [SynStruc.ConstituencyElement("NP", [
            SynStruc.TokenElement({"A", "B"}, "N", {"x": 1, "y": 2}, None, False)
        ], 123, False)]
        self.assertEqual([
            (expectation, None)
        ], transformer.align_syn_strucs(syn1, syn2))

        # Children are tested based on the rules for that element type
        # For example, Token elements can have additional lemmas
        match.children[0].lemmas.add("C")
        syn2.elements = [match]
        self.assertEqual([
            (expectation, match)
        ], transformer.align_syn_strucs(syn1, syn2))

    def test_align_syn_strucs_multiple_ordered_elements(self):
        transformer = LexicalTransformer(self.analysis)

        syn1 = SynStruc()
        syn2 = SynStruc()

        s1t1 = SynStruc.TokenElement({"A"}, "N", dict(), None, False)
        s1t2 = SynStruc.TokenElement({"B"}, "N", dict(), None, False)
        s1t3 = SynStruc.TokenElement({"C"}, "N", dict(), None, False)

        s2t1 = SynStruc.TokenElement({"A"}, "N", dict(), None, False)
        s2t2 = SynStruc.TokenElement({"B"}, "N", dict(), None, False)
        s2t3 = SynStruc.TokenElement({"C"}, "N", dict(), None, False)
        s2t4 = SynStruc.TokenElement({"D"}, "N", dict(), None, False)

        # All tokens are aligned in order
        syn1.elements = [s1t1, s1t2, s1t3]
        syn2.elements = [s2t1, s2t2, s2t3]

        self.assertEqual([
            (s1t1, s2t1),
            (s1t2, s2t2),
            (s1t3, s2t3),
        ], transformer.align_syn_strucs(syn1, syn2))

        # Only the first match is found
        syn2.elements = [s2t1, s2t2, s2t3, s2t3]

        self.assertEqual([
            (s1t1, s2t1),
            (s1t2, s2t2),
            (s1t3, s2t3),
        ], transformer.align_syn_strucs(syn1, syn2))

        # Ordering matters; if a component can't be found, it is skipped
        syn1.elements = [s1t1, s1t2, s1t3]
        syn2.elements = [s2t1, s2t3, s2t2]

        self.assertEqual([
            (s1t1, s2t1),
            (s1t2, s2t2),
            (s1t3, None),
        ], transformer.align_syn_strucs(syn1, syn2))

        # Unneeded components are skipped
        syn1.elements = [s1t1, s1t2, s1t3]
        syn2.elements = [s2t1, s2t2, s2t4, s2t3]

        self.assertEqual([
            (s1t1, s2t1),
            (s1t2, s2t2),
            (s1t3, s2t3),
        ], transformer.align_syn_strucs(syn1, syn2))