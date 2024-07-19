from flask import abort, Blueprint, request
from leia.dekade.app import DEKADE
from leia.ontomem.ontology import Concept, OSet
from leia.ontomem.properties import COMPARATOR, Property, WILDCARD
from typing import Tuple, Union

import json


class DEKADEAPIOntologyBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__("DEKADE-API-ONTOLOGY", __name__, static_folder=app.static_folder, template_folder=app.template_folder)
        self.app = app

        # Read APIs
        self.add_url_rule("/api/knowledge/ontology/list", endpoint=None, view_func=self.read_list, methods=["GET"])
        self.add_url_rule("/api/knowledge/ontology/filter/<substring>", endpoint=None, view_func=self.read_filter, methods=["GET"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>", endpoint=None, view_func=self.read_concept, methods=["GET"])
        self.add_url_rule("/api/knowledge/ontology/children/<concept>", endpoint=None, view_func=self.read_children, methods=["GET"])

        # Write APIs
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>/create", endpoint=None, view_func=self.write_create, methods=["POST"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>/parent/add", endpoint=None, view_func=self.write_parent_add, methods=["POST"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>/parent/remove", endpoint=None, view_func=self.write_parent_remove, methods=["POST"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>/definition/edit", endpoint=None, view_func=self.write_definition_edit, methods=["POST"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>/filler/add", endpoint=None, view_func=self.write_filler_add, methods=["POST"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>/filler/remove", endpoint=None, view_func=self.write_filler_remove, methods=["POST"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>/filler/block", endpoint=None, view_func=self.write_filler_block, methods=["POST"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>/filler/unblock", endpoint=None, view_func=self.write_filler_unblock, methods=["POST"])

    def _guess_filler(self, concept: Concept, property: str, filler: str) -> Concept.FILLER:
        # Attempts to parse the filler without being explicitly told the type.
        # The expectations of the property are leveraged in the cases of ambiguity.

        # TODO: the property is not currently being used (99% coverage from proper input without it)

        if filler.startswith("@"):
            filler = filler[1:]
            if filler in concept.private:
                return concept.private[filler]
            return self.app.agent.memory.ontology.concept(filler)
        if filler.startswith("$"):
            return self.app.agent.memory.properties.get_property(filler[1:])
        if filler.startswith("!"):
            return WILDCARD(filler)
        if "," in filler:
            try:
                parts = list(map(lambda p: p.strip(), filler.split(",")))
                if len(parts) == 2 or len(parts) == 3:
                    comparator = COMPARATOR(parts[0])
                    parts = parts[1:]
                    parts = list(map(lambda p: float(p) if "." in p else int(p), parts))
                    parts = [comparator] + parts
                    return tuple(parts)
            except: pass
        try:
            return float(filler)
        except: pass
        try:
            return int(filler)
        except: pass

        return filler

    def _parse_filler(self, concept: Concept, filler: str, type: str) -> Concept.FILLER:
        if type == "concept":
            if filler.startswith("@"):
                filler = filler[1:]
            if filler in concept.private:
                return concept.private[filler]
            return self.app.agent.memory.ontology.concept(filler)
        if type == "property":
            if filler.startswith("$"):
                filler = filler[1:]
            return self.app.agent.memory.properties.get_property(filler)
        if type == "text":
            return filler
        if type == "comparator":
            parts = list(map(lambda p: p.strip(), filler.split(",")))
            comparator = COMPARATOR(parts[0])
            parts = parts[1:]
            parts = list(map(lambda p: float(p) if "." in p else int(p), parts))
            parts = [comparator] + parts
            return tuple(parts)
        if type == "wildcard":
            return WILDCARD(filler)
        if type == "set":
            if filler.startswith("@"):
                filler = filler[1:]
            return concept.private[filler]
        if type == "number":
            if "." in filler:
                return float(filler)
            return int(filler)

        raise NotImplementedError("Cannot parse filler %s of type %s in %s." % (filler, type, str(concept)))

    def _cast_filler(self, concept: Concept, filler: Concept.FILLER) -> Tuple[Union[str, Tuple, int, float], str]:
        if isinstance(filler, Concept):
            return str(filler), "concept"
        if isinstance(filler, Property):
            return str(filler), "property"
        if isinstance(filler, str):
            return filler, "text"
        if isinstance(filler, tuple):
            if len(filler) == 2:
                return (filler[0].value, filler[1]), "comparator"
            if len(filler) == 3:
                return (filler[0].value, filler[1], filler[2]), "comparator"
        if isinstance(filler, WILDCARD):
            return filler.value, "wildcard"
        if isinstance(filler, OSet):
            return str(filler), "set"
        if isinstance(filler, int) or isinstance(filler, float):
            return filler, "number"

        raise NotImplementedError("Cannot cast filler %s in %s." % (str(filler), str(concept)))

    def read_list(self):
        return json.dumps(list(sorted(self.app.agent.memory.ontology.names())))

    def read_filter(self, substring: str):
        substring = substring.lower()

        concepts = self.app.agent.memory.ontology.names()
        concepts = filter(lambda c: substring in c.lower(), concepts)

        return json.dumps(list(sorted(concepts)))

    def read_concept(self, concept: str):

        def _format_row(row) -> dict:

            cast = self._cast_filler(concept, row.filler)

            output = {
                "row": "local",
                "property": row.property,
                "facet": row.facet,
                "filler": cast[0],
                "type": cast[1],
            }

            if isinstance(row, Concept.LocalRow):
                output["meta"] = row.meta
                if row.concept != concept:
                    output["row"] = "inherit"
                    output["from"] = row.concept.name
            if isinstance(row, Concept.BlockedRow):
                output["row"] = "block"

            return output

        concept = self.app.agent.memory.ontology.concept(concept)
        output = {
            "name": concept.name,
            "definition": concept.definition(),
            "parents": list(map(lambda p: p.name, concept.parents())),
            "rows": list(map(lambda r: _format_row(r), concept.rows()))
        }

        return json.dumps(output)

    def read_children(self, concept: str):
        concept = self.app.agent.memory.ontology.concept(concept)
        children = concept.children()
        children = sorted(list(map(lambda c: c.name, children)))

        return json.dumps(children)

    def write_create(self, concept: str):
        raise NotImplementedError

    def write_parent_add(self, concept: str):
        raise NotImplementedError

    def write_parent_remove(self, concept: str):
        raise NotImplementedError

    def write_definition_edit(self, concept: str):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        definition = data["definition"]

        concept = self.app.agent.memory.ontology.concept(concept)
        concept.set_definition(definition)

        self.app.agent.memory.edits.ontology.note_edited(concept.name, "DEKADE")

        return "OK"

    def write_filler_add(self, concept: str):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        property = data["property"]
        facet = data["facet"]
        filler = data["filler"]
        meta = dict()
        if len(data["meta"]) > 0:
            meta = dict(map(lambda m: tuple([m[0].strip(), m[1].strip()]), map(lambda m: m.strip().split("="), data["meta"].split(","))))

        concept = self.app.agent.memory.ontology.concept(concept)

        filler = self._guess_filler(concept, property, filler)
        concept.add_local(property, facet, filler, **meta)

        self.app.agent.memory.edits.ontology.note_edited(concept.name, "DEKADE")

        return "OK"

    def write_filler_remove(self, concept: str):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        property = data["property"]
        facet = data["facet"]
        filler = data["filler"]
        type = data["type"]

        concept = self.app.agent.memory.ontology.concept(concept)

        filler = self._parse_filler(concept, filler, type)
        concept.remove_local(property, facet, filler)

        self.app.agent.memory.edits.ontology.note_edited(concept.name, "DEKADE")

        return "OK"

    def write_filler_block(self, concept: str):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        property = data["property"]
        facet = data["facet"]
        filler = data["filler"]
        type = data["type"]

        concept = self.app.agent.memory.ontology.concept(concept)

        filler = self._parse_filler(concept, filler, type)
        concept.add_block(property, facet, filler)

        self.app.agent.memory.edits.ontology.note_edited(concept.name, "DEKADE")

        return "OK"

    def write_filler_unblock(self, concept: str):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        property = data["property"]
        facet = data["facet"]
        filler = data["filler"]
        type = data["type"]

        concept = self.app.agent.memory.ontology.concept(concept)

        filler = self._parse_filler(concept, filler, type)
        concept.remove_block(property, facet, filler)

        self.app.agent.memory.edits.ontology.note_edited(concept.name, "DEKADE")

        return "OK"