from typing import List, Tuple, Union
from unittest import TestCase

import string


class LEIATestCase(TestCase):

    # A test case with common helper methods

    def mockSense(self, sense: str, word: str=None, cat: str=None, definition: str=None, example: str=None, comments: str=None,
                  synonyms: List[str]=None, hyponyms: List[str]=None, synstruc: dict=None, semstruc: Union[str, dict]=None,
                  tmrhead: str=None, meaning_procedures: List[List[str]]=None, output_syntax: Union[str, List[str]]=None,
                  example_deps: List[Tuple[str, str, str]]=None, example_bindings: List[str]=None, types: List[str]=None,
                  use_with_types: List[str]=None) -> dict:

        return {
            "SENSE": sense,
            "WORD": sense[0:sense.rfind("-")] if word is None else word,
            "CAT": sense[sense.rfind("-")+1:].rstrip(string.digits),
            "DEF": definition if definition is not None else "",
            "EX": example if example is not None else "",
            "COMMENTS": comments if comments is not None else "",
            "SYNONYMS": synonyms if synonyms is not None else [],
            "HYPONYMS": hyponyms if hyponyms is not None else [],
            "SYN-STRUC": synstruc if synstruc is not None else {},
            "SEM-STRUC": semstruc if semstruc is not None else {},
            "TMR-HEAD": tmrhead,
            "MEANING-PROCEDURES": meaning_procedures if meaning_procedures is not None else [],
            "OUTPUT-SYNTAX": output_syntax if output_syntax is not None else [],
            "EXAMPLE-DEPS": example_deps if example_deps is not None else [],
            "EXAMPLE-BINDINGS": example_bindings if example_bindings is not None else[],
            "TYPES": types if types is not None else [],
            "USE-WITH-TYPES": use_with_types if use_with_types is not None else []
        }