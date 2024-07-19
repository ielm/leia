from flask import Blueprint
from leia.dekade.app import DEKADE
from leia.ontomem.ontology import Concept
from leia.ontomem.properties import Property, WILDCARD

import json


class DEKADEAPIOntologyBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__("DEKADE-API-ONTOLOGY", __name__, static_folder=app.static_folder, template_folder=app.template_folder)
        self.app = app

        self.add_url_rule("/api/knowledge/ontology/list", endpoint=None, view_func=self.knowledge_ontology_list, methods=["GET"])
        self.add_url_rule("/api/knowledge/ontology/filter/<substring>", endpoint=None, view_func=self.knowledge_ontology_filter, methods=["GET"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>", endpoint=None, view_func=self.knowledge_ontology_concept, methods=["GET"])
        self.add_url_rule("/api/knowledge/ontology/children/<concept>", endpoint=None, view_func=self.knowledge_ontology_children, methods=["GET"])

    def knowledge_ontology_list(self):
        return json.dumps(list(sorted(self.app.agent.memory.ontology.names())))

    def knowledge_ontology_filter(self, substring: str):
        substring = substring.lower()

        concepts = self.app.agent.memory.ontology.names()
        concepts = filter(lambda c: substring in c.lower(), concepts)

        return json.dumps(list(sorted(concepts)))

    def knowledge_ontology_concept(self, concept: str):

        def _format_row(row) -> dict:

            output = {
                "row": "local",
                "property": row.property,
                "facet": row.facet,
                "filler": _format_filler(row.filler),
            }

            if isinstance(row, Concept.LocalRow):
                output["meta"] = row.meta
                if row.concept != concept:
                    output["row"] = "inherit"
                    output["from"] = row.concept.name
            if isinstance(row, Concept.BlockedRow):
                output["row"] = "block"

            return output

        def _format_filler(filler):
            if isinstance(filler, Concept):
                return str(filler)
            if isinstance(filler, Property):
                return str(filler)
            if isinstance(filler, str):
                return filler
            if isinstance(filler, tuple):
                if len(filler) == 2:
                    return (filler[0].value, filler[1])
                if len(filler) == 3:
                    return (filler[0].value, filler[1], filler[2])
            if isinstance(filler, WILDCARD):
                return filler.value

            raise NotImplementedError("Cannot format filler %s in %s" % (str(filler), concept))

        concept = self.app.agent.memory.ontology.concept(concept)
        output = {
            "name": concept.name,
            "definition": concept.definition(),
            "parents": list(map(lambda p: p.name, concept.parents())),
            "rows": list(map(lambda r: _format_row(r), concept.rows()))
        }

        return json.dumps(output)

    def knowledge_ontology_children(self, concept: str):
        concept = self.app.agent.memory.ontology.concept(concept)
        children = concept.children()
        children = sorted(list(map(lambda c: c.name, children)))

        return json.dumps(children)