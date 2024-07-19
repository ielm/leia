from collections import OrderedDict
from pyparsing import nestedExpr, OneOrMore
from typing import List, Union

import re


class FormatToLISP(object):

    def sense_to_lisp(self, sense: dict) -> str:
        template = "({sid} {cat} {d} {ex} {com} {tmr} {syn} {sem} {out} {mp} {exbind} {exdep} {synonyms} {hyponyms} {types} {usewithtypes})"

        sid = self._escape_sense_name(sense["SENSE"])
        cat = self.cat_to_lisp(sense["CAT"])
        definition = "(DEF \"%s\")" % sense["DEF"]
        example = "(EX \"%s\")" % sense["EX"]
        comments = "(COMMENTS \"%s\")" % sense["COMMENTS"]

        tmrhead = self.tmr_head_to_lisp(sense["TMR-HEAD"] if "TMR-HEAD" in sense else "NIL")
        synstruc = self.synstruc_to_lisp(sense["SYN-STRUC"])
        semstruc = self.semstruc_to_lisp(sense["SEM-STRUC"])
        output_syntax = self.output_syntax_to_lisp(sense["OUTPUT-SYNTAX"] if "OUTPUT-SYNTAX" in sense else "NIL")
        meaning_procedures = self.meaning_procedures_to_lisp(sense["MEANING-PROCEDURES"] if "MEANING-PROCEDURES" in sense else "NIL")

        example_bindings = self.example_bindings_to_lisp(sense["EXAMPLE-BINDINGS"] if "EXAMPLE-BINDINGS" in sense else "NIL")
        example_deps = self.example_deps_to_lisp(sense["EXAMPLE-DEPS"] if "EXAMPLE-DEPS" in sense else "NIL")

        synonyms = self.synonyms_to_lisp(sense["SYNONYMS"])
        hyponyms = self.hyponyms_to_lisp(sense["HYPONYMS"])

        types = self.types_to_lisp(sense["TYPES"])
        use_with_types = self.use_with_types_to_lisp(sense["USE-WITH-TYPES"])

        return template.format(
            sid=sid, cat=cat, d=definition, ex=example, com=comments,
            tmr=tmrhead, syn=synstruc, sem=semstruc, out=output_syntax, mp=meaning_procedures,
            exbind=example_bindings, exdep=example_deps, synonyms=synonyms, hyponyms=hyponyms,
            types=types, usewithtypes=use_with_types
        )

    def cat_to_lisp(self, cat: Union[str, List[str]]) -> str:
        if isinstance(cat, str):
            return "(CAT %s)" % cat
        if isinstance(cat, list):
            return "(CAT (%s))" % " ".join(cat)

        raise Exception("Unknown CAT type: %s" % type(cat))

    def tmr_head_to_lisp(self, tmrhead: str) -> str:
        if tmrhead == "":
            tmrhead = "NIL"

        return "(TMR-HEAD %s)" % tmrhead

    def synstruc_to_lisp(self, synstruc: OrderedDict) -> str:
        return "(SYN-STRUC %s)" % self._flatten_synstruc(synstruc)

    def _flatten_synstruc(self, synstruc: Union[str, int, float, list, OrderedDict]):
        if isinstance(synstruc, dict):
            return "(%s)" % " ".join(map(lambda i: "(%s %s)" % (self._tidy_synstruc_header(i[0]), self._flatten_synstruc(i[1])), synstruc.items()))
        if isinstance(synstruc, list):
            return "(%s)" % " ".join(map(lambda i: self._flatten_semstruc(i), synstruc))
        return str(synstruc)

    def _tidy_synstruc_header(self, header: str) -> str:
        matches = re.findall("-[0-9]+$", header)
        if len(matches) > 0:
            header = header.replace(matches[0], "")

        if header == "ROOT-WORD":
            header = "ROOT"

        return header

    def semstruc_to_lisp(self, semstruc: Union[str, dict]) -> str:
        if semstruc == "":
            return "(SEM-STRUC NIL)"
        if semstruc == "NIL":
            return "(SEM-STRUC NIL)"
        if isinstance(semstruc, str):
            return "(SEM-STRUC (%s))" % semstruc

        return "(SEM-STRUC %s)" % self._flatten_semstruc(semstruc)

    def _flatten_semstruc(self, semstruc: Union[str, dict, list]) -> str:
        if isinstance(semstruc, dict):
            elements = []
            for k, v in semstruc.items():
                if k == "CONSTRAINT":
                    elements.append("(%s)" % " ".join(map(lambda i: self._flatten_semstruc(i), v)))
                elif v == dict():
                    elements.append("(%s)" % self._tidy_semstruc_header(k))
                else:
                    elements.append("(%s %s)" % (self._tidy_semstruc_header(k), self._flatten_semstruc(v)))

            return " ".join(elements)
        elif isinstance(semstruc, list):
            return "(%s)" % " ".join(map(lambda i: self._flatten_semstruc(i), semstruc))
        else:
            return str(semstruc)

    def _tidy_semstruc_header(self, header: str) -> str:
        matches = re.findall("-[0-9]+$", header)
        if len(matches) > 0:
            header = header.replace(matches[0], "")

        return header

    def output_syntax_to_lisp(self, output_syntax: Union[str, List[str]]) -> str:
        if output_syntax == "":
            output_syntax = "NIL"
        if isinstance(output_syntax, str):
            return "(OUTPUT-SYNTAX %s)" % output_syntax

        return "(OUTPUT-SYNTAX (%s))" % " ".join(output_syntax)

    def meaning_procedures_to_lisp(self, meaning_procedures: Union[str, List[Union[str, List]]]) -> str:
        if meaning_procedures == "":
            return "(MEANING-PROCEDURES NIL)"
        if meaning_procedures == "NIL":
            return "(MEANING-PROCEDURES NIL)"
        if not meaning_procedures:
            return "(MEANING-PROCEDURES NIL)"

        return "(MEANING-PROCEDURES %s)" % " ".join(map(lambda e: self._flatten_mp(e), meaning_procedures))

    def _flatten_mp(self, mp: Union[str, List[Union[str, List]]]) -> str:
        if isinstance(mp, str):
            if mp.startswith("^$VAR") or mp.startswith("REFSEM"):
                return "(VALUE %s)" % mp
            return mp
        elif isinstance(mp, list):
            return "(%s)" % " ".join(map(lambda e: self._flatten_mp(e), mp))
        else:
            return str(mp)

    def example_bindings_to_lisp(self, example_bindings: Union[str, List[str], List[List[str]]]):
        if example_bindings == "":
            return "(EXAMPLE-BINDINGS NIL)"
        if example_bindings == "NIL":
            return "(EXAMPLE-BINDINGS NIL)"
        if not example_bindings:
            return "(EXAMPLE-BINDINGS NIL)"

        types = set(map(lambda e: type(e), example_bindings))

        if list not in types:
            return "(EXAMPLE-BINDINGS (%s))" % " ".join(map(lambda eb: str(eb), example_bindings))

        return "(EXAMPLE-BINDINGS %s)" % " ".join(map(lambda eb: "(%s)" % " ".join(map(lambda x: str(x), eb)), example_bindings))

    def example_deps_to_lisp(self, example_deps: Union[str, List[List[str]]]):
        if example_deps == "":
            return "(EXAMPLE-DEPS NIL)"
        if example_deps == "NIL":
            return "(EXAMPLE-DEPS NIL)"
        if not example_deps:
            return "(EXAMPLE-DEPS NIL)"

        return "(EXAMPLE-DEPS (%s))" % " ".join(map(lambda ed: "(%s)" % " ".join(map(lambda e: str(e), ed)), example_deps))

    def synonyms_to_lisp(self, synonyms: Union[str, int, List[Union[str, int]]]) -> str:
        if synonyms == "":
            return "(SYNONYMS NIL)"
        if synonyms == "NIL":
            return "(SYNONYMS NIL)"
        if not synonyms:
            return "(SYNONYMS NIL)"

        if isinstance(synonyms, str):
            synonyms = [synonyms]

        return "(SYNONYMS (%s))" % " ".join(map(lambda s: self._escape_word_name(s) if isinstance(s, str) else str(s), synonyms))

    def hyponyms_to_lisp(self, hyponyms: Union[str, int, List[Union[str, int]]]) -> str:
        if hyponyms == "":
            return "(HYPONYMS NIL)"
        if hyponyms == "NIL":
            return "(HYPONYMS NIL)"
        if not hyponyms:
            return "(HYPONYMS NIL)"

        if isinstance(hyponyms, str):
            hyponyms = [hyponyms]

        return "(HYPONYMS (%s))" % " ".join(map(lambda h: self._escape_word_name(h) if isinstance(h, str) else str(h), hyponyms))

    def types_to_lisp(self, types: Union[str, List[str]]) -> str:
        if types == "":
            return "(TYPES NIL)"
        if types == "NIL":
            return "(TYPES NIL)"
        if not types:
            return "(TYPES NIL)"

        if isinstance(types, str):
            types = [types]

        return "(TYPES (%s))" % " ".join(types)

    def use_with_types_to_lisp(self, use_with_types: Union[str, List[str]]) -> str:
        if use_with_types == "":
            return "(USE-WITH-TYPES NIL)"
        if use_with_types == "NIL":
            return "(USE-WITH-TYPES NIL)"
        if not use_with_types:
            return "(USE-WITH-TYPES NIL)"

        if isinstance(use_with_types, str):
            use_with_types = [use_with_types]

        return "(USE-WITH-TYPES (%s))" % " ".join(use_with_types)

    def word_to_lisp(self, word: str, senses: dict) -> str:
        if len(senses) == 0:
            return "(%s)" % self._escape_word_name(word)

        return "(%s\n%s)" % (self._escape_word_name(word), "\n".join(map(lambda s: self.sense_to_lisp(s), senses.values())))

    def _escape_word_name(self, name: str):
        if len(list(filter(lambda c: self._is_quotable_character(c), name))) == 0:
            return name
        return "\"%s\"" % name

    def _escape_sense_name(self, name: str):
        suffix = re.findall("-[A-Z]+[0-9]+$", name)

        if len(suffix) == 0:
            return name
        name_trimmed = name.replace(suffix[0], "")

        if len(list(filter(lambda c: self._is_quotable_character(c), name_trimmed))) == 0:
            return name
        return "\"%s\"" % name

    def _is_quotable_character(self, c: str) -> bool:
        return not c.isalpha() and not c == "_" and not c == "*"


class FormatFromLISP(object):

    # Parse a LISP string, returning a sense dictionary
    def lisp_to_sense(self, lisp: str) -> dict:
        data = OneOrMore(nestedExpr()).parseString(lisp)
        data = data.asList()
        data = data[0]  # Unwrap the first level; it isn't needed.

        return self.list_to_sense(data)

    # After a LISP string has been converted into recursive python list objects, parse it into a sense dictionary
    def list_to_sense(self, list: List) -> dict:
        sense = list[0]
        word = sense.split("-")[0]

        return {
            "SENSE": sense,
            "WORD": word,
            "CAT": self.parse_cat(self.list_key_to_value(list, "CAT", "")),
            "DEF": self.parse_def(self.list_key_to_value(list, "DEF", "")),
            "EX": self.parse_ex(self.list_key_to_value(list, "EX", "")),
            "COMMENTS": self.parse_comments(self.list_key_to_value(list, "COMMENTS", "")),
            "TMR-HEAD": self.parse_tmr_head(self.list_key_to_value(list, "TMR-HEAD", "NIL")),
            "SYN-STRUC": self.parse_syn_struc(self.list_key_to_value(list, "SYN-STRUC", [])),
            "SEM-STRUC": self.parse_sem_struc(self.list_key_to_value(list, "SEM-STRUC", "ALL")),
            "OUTPUT-SYNTAX": self.parse_output_syntax(self.list_key_to_value(list, "OUTPUT-SYNTAX", "NIL")),
            "MEANING-PROCEDURES": self.parse_meaning_procedures(self.list_key_to_value(list, "MEANING-PROCEDURES", "NIL")),
            "EXAMPLE-BINDINGS": self.parse_example_bindings(self.list_key_to_value(list, "EXAMPLE-BINDINGS", "NIL")),
            "EXAMPLE-DEPS": self.parse_example_deps(self.list_key_to_value(list, "EXAMPLE-DEPS", "NIL")),
            "SYNONYMS": self.parse_synonyms(self.list_key_to_value(list, "SYNONYMS", "NIL")),
            "HYPONYMS": self.parse_hyponyms(self.list_key_to_value(list, "HYPONYMS", "NIL")),
            "TYPES": self.parse_types(self.list_key_to_value(list, "TYPES", [])),
            "USE-WITH-TYPES": self.parse_use_with_types(self.list_key_to_value(list, "USE-WITH-TYPES", [])),
        }

    def list_key_to_value(self, lisp: list, key: str, default=None) -> Union[List, None]:
        for element in lisp:
            if isinstance(element, list) and len(element) > 0 and element[0] == key:
                return element

        return [key, default]

    def parse_cat(self, contents: List):
        return contents[1]

    def parse_def(self, contents: List):
        return contents[1]

    def parse_ex(self, contents: List):
        return contents[1]

    def parse_comments(self, contents: List):
        return contents[1]

    def parse_tmr_head(self, contents: List):
        return contents[1]

    def parse_syn_struc(self, contents: List):

        def _parse(l: list, d: OrderedDict) -> OrderedDict:
            if l is None:
                return d

            for e in l:
                if type(e[1]) == str:
                    d[e[0]] = e[1]
                elif e[0] == "CAT" and type(e[1]) == list:
                    # Special case; CAT can sometimes be a list, and shouldn't be recursively parsed
                    d[e[0]] = e[1]
                elif type(e[1]) == list:
                    d[e[0]] = _parse(e[1], type(d)())
            return d

        syn_struc = OrderedDict()
        _parse(contents[1], syn_struc)

        return syn_struc

    def parse_sem_struc(self, contents: List):

        # Simple sem-strucs only contain a single string
        if isinstance(contents[1], list) and len(contents[1]) == 1 and isinstance(contents[1][0], str) and len(contents) == 2:
            return contents[1][0]

        def _parse(input):
            if isinstance(input, str):
                return input
            if len(input) == 1 and isinstance(input[0], str):
                return input[0]

            d = dict()

            for e in input:
                # A semstruc head with no properties can simply be an empty dictionary.
                if len(e) == 1 and isinstance(e[0], str):
                    d[e[0]] = dict()
                    continue

                # REFSEMs sometimes need special treatment; if their only content is a single concept in a list,
                # it should stay that way (not be additionally parsed).
                if e[0].startswith("REFSEM") and len(e) == 2 and isinstance(e[1], list) and len(e[1]) == 1 and isinstance(e[1][0], str):
                    d[e[0]] = e[1]
                    continue

                # Comparator values need special treatment; don't recursively parse them, they are represented as lists.
                if isinstance(e[1], list) and e[1][0] in {">", "<", ">=", "<=", "<>", "><", "="}:
                    d[e[0]] = e[1]
                    continue

                d[e[0]] = _parse(e[1:])

            return d

        sem_struc = _parse(contents[1:])

        return sem_struc

    def parse_output_syntax(self, contents: List):
        output_syntax = contents[1]
        if output_syntax == list():
            output_syntax = "NIL"

        return output_syntax

    def parse_meaning_procedures(self, contents: List):
        meaning_procedures = contents[1:]
        if meaning_procedures == list():
            meaning_procedures = "NIL"
        if meaning_procedures == ["NIL"]:
            meaning_procedures = "NIL"
        if meaning_procedures == [[]]:
            meaning_procedures = "NIL"

        return meaning_procedures

    def parse_example_bindings(self, contents: List):
        example_bindings = contents[1]
        if example_bindings == list():
            example_bindings = "NIL"

        return example_bindings

    def parse_example_deps(self, contents: List):
        example_deps = contents[1]
        if example_deps == list():
            example_deps = "NIL"

        return example_deps

    def parse_synonyms(self, contents: List):
        synonyms = contents[1]
        if synonyms == list():
            synonyms = "NIL"

        return synonyms

    def parse_hyponyms(self, contents: List):
        hyponyms = contents[1]
        if hyponyms == list():
            hyponyms = "NIL"

        return hyponyms

    def parse_types(self, contents: List):
        types = contents[1]
        if types == "NIL":
            types = []

        return types

    def parse_use_with_types(self, contents: List):
        use_with_types = contents[1]
        if use_with_types == "NIL":
            use_with_types = []

        return use_with_types