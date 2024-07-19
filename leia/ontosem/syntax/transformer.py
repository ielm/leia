from leia.ontomem.lexicon import SynStruc
from leia.ontosem.analysis import Analysis
from leia.ontosem.syntax.results import ConstituencyNode, Dependency, Syntax, Word
from leia.ontosem.syntax.synmapper import SynMatcher
from typing import List, Tuple, Union


class LexicalTransformer(object):

    def __init__(self, analysis: Analysis):
        self.analysis = analysis

    def run(self, syntax: Syntax):
        for (
            transformation
        ) in self.analysis.config.memory().transformations.transformations():
            for synstruc in transformation.input_synstrucs:
                matches = SynMatcher(self.analysis).run(syntax, synstruc)
                for match in matches:
                    root = self.root_for_match(match)
                    if root is None:
                        continue

                    for sense in self.analysis.lexicon.senses(root):
                        alignment = self.align_syn_strucs(
                            transformation.root_synstruc, sense.synstruc
                        )

                        if None in list(map(lambda a: a[1], alignment)):
                            continue

                        transformation.executable(self.analysis).run(
                            sense, match, alignment
                        )
                        self.analysis.log(
                            "Transformed $sense (of word $word) with $transformation",
                            type="knowledge",
                            source=self.__class__,
                            word=root.index,
                            sense=sense.id,
                            transformation=transformation.name,
                        )

    def root_for_match(self, match: SynMatcher.SynMatchResult) -> Union[Word, None]:
        root = match.component_for_var(0)
        if root is None:
            return None

        if isinstance(root, Word):
            return root
        if isinstance(root, Dependency):
            # The dependent is the target word.
            return root.governor
        if isinstance(root, ConstituencyNode):
            # The leftmost word is the target word.
            return root.leftmost_word()

        # The match is some unknown type; this is an error.
        self.analysis.log(
            "Unknown component from SynMatcher.SynMatchResult: $component",
            type="error",
            level="WARN",
            source=self.__class__,
            component=root.__class__.__name__,
        )
        return None

    def align_syn_strucs(
        self, synstruc1: SynStruc, synstruc2: SynStruc
    ) -> List[Tuple[SynStruc.Element, SynStruc.Element]]:
        # For now, this is a simple alignment; elements in the first syn-struc must all be present, in order, in the
        # second.  We assume all are top-level elements (that is, no looking inside constituency nodes).
        # Elements must be a fuzzy match - certain fields in certain element types are allowed to mismatch.

        results = []

        candidates = iter(synstruc2.elements)
        for element in synstruc1.elements:
            result = (element, None)

            for candidate in candidates:
                if self._do_elements_match(element, candidate):
                    result = (element, candidate)
                    break

            results.append(result)

        return results

    def _do_elements_match(
        self, element1: SynStruc.Element, element2: SynStruc.Element
    ) -> bool:
        if isinstance(element1, SynStruc.RootElement) and isinstance(
            element2, SynStruc.RootElement
        ):
            return self._do_root_elements_match(element1, element2)
        if isinstance(element1, SynStruc.TokenElement) and isinstance(
            element2, SynStruc.TokenElement
        ):
            return self._do_token_elements_match(element1, element2)
        if isinstance(element1, SynStruc.DependencyElement) and isinstance(
            element2, SynStruc.DependencyElement
        ):
            return self._do_dependency_elements_match(element1, element2)
        if isinstance(element1, SynStruc.ConstituencyElement) and isinstance(
            element2, SynStruc.ConstituencyElement
        ):
            return self._do_constituency_elements_match(element1, element2)

        # The types are not the same, or are invalid
        return False

    def _do_root_elements_match(
        self, element1: SynStruc.RootElement, element2: SynStruc.RootElement
    ) -> bool:
        return True

    def _do_token_elements_match(
        self, element1: SynStruc.TokenElement, element2: SynStruc.TokenElement
    ) -> bool:
        for lemma in element1.lemmas:
            if lemma not in element2.lemmas:
                return False

        # TODO: Should this use the POS knowledge manager?
        if element1.pos != element2.pos:
            return False

        for k, v in element1.morph.items():
            if k not in element2.morph:
                return False
            if v != element2.morph[k]:
                return False

        # No filtering occurred, the elements are "close enough"
        return True

    def _do_dependency_elements_match(
        self, element1: SynStruc.DependencyElement, element2: SynStruc.DependencyElement
    ) -> bool:
        if element1.type.lower() != element2.type.lower():
            return False

        if element1.governor != element2.governor:
            return False

        if element1.dependent != element2.dependent:
            return False

        # No filtering occurred, the elements are "close enough"
        return True

    def _do_constituency_elements_match(
        self,
        element1: SynStruc.ConstituencyElement,
        element2: SynStruc.ConstituencyElement,
    ) -> bool:
        if element1.type.lower() != element2.type.lower():
            return False

        candidates = iter(element2.children)
        for child in element1.children:
            match_found = False
            for candidate in candidates:
                if self._do_elements_match(child, candidate):
                    match_found = True
                    break
            if not match_found:
                return False

        # No filtering occurred, the elements are "close enough"
        return True
