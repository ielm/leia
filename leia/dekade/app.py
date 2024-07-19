from flask import Blueprint, Flask, render_template, send_from_directory
from flask_cors import CORS
from leia.ontoagent.agent import Agent
from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Concept
from leia.ontomem.properties import Property

import json
import mimetypes


mimetypes.add_type("text/javascript", ".js")


class DEKADE(Flask):

    def __init__(self, agent: Agent):
        super().__init__(__name__, static_folder="static/", template_folder="templates/")
        CORS(self)

        self.agent = agent

        self.register_blueprint(DEKADEBlueprint(self))
        self.register_blueprint(DEKADEAPIBlueprint(self))


class DEKADEBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__("DEKADE", __name__, static_folder=app.static_folder, template_folder=app.template_folder)
        self.app = app

        self.add_url_rule("/favicon.ico", endpoint=None, view_func=self.favicon, methods=["GET"])
        self.add_url_rule("/", endpoint=None, view_func=self.index, methods=["GET"])
        self.add_url_rule("/handlebars/<path:path>", endpoint=None, view_func=self.handlebars_template, methods=["GET"])

    def read_template(self, name: str) -> str:
        with open("%s/%s" % (self.template_folder, name), "r") as f:
            return f.read()

    def favicon(self):
        return send_from_directory(self.static_folder, "favicon.ico", mimetype="image/vnd.microsoft.icon")

    def index(self):
        return render_template("jinja/index.html", thing=123)

    def handlebars_template(self, path):
        return self.read_template("handlebars/%s" % path)


class DEKADEAPIBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__("DEKADE-API", __name__, static_folder=app.static_folder, template_folder=app.template_folder)
        self.app = app

        # Ontology API
        self.add_url_rule("/api/knowledge/ontology/list", endpoint=None, view_func=self.knowledge_ontology_list, methods=["GET"])
        self.add_url_rule("/api/knowledge/ontology/filter/<substring>", endpoint=None, view_func=self.knowledge_ontology_filter, methods=["GET"])
        self.add_url_rule("/api/knowledge/ontology/concept/<concept>", endpoint=None, view_func=self.knowledge_ontology_concept, methods=["GET"])

    def knowledge_ontology_list(self):
        return json.dumps(list(sorted(self.app.agent.memory.ontology.names())))

    def knowledge_ontology_filter(self, substring: str):
        substring = substring.lower()

        concepts = self.app.agent.memory.ontology.names()
        concepts = filter(lambda c: substring in c.lower(), concepts)

        return json.dumps(list(sorted(concepts)))

    def knowledge_ontology_concept(self, concept: str):

        def _format_row(row) -> dict:
            row_type = "local"
            if isinstance(row, Concept.LocalRow) and row.concept.name != concept:
                row_type = "inherit"
            if isinstance(row, Concept.BlockedRow):
                row_type = "block"

            return {
                "row": row_type,
                "from": row.concept.name,
                "property": row.property,
                "facet": row.facet,
                "filler": _format_filler(row.filler),
                "meta": row.meta
            }

        def _format_filler(filler):
            if isinstance(filler, Concept):
                return str(filler)
            if isinstance(filler, Property):
                return str(filler)
            if isinstance(filler, list):
                return filler
            if isinstance(filler, tuple):
                if len(filler) == 2:
                    return (filler[0].name, filler[1])
                if len(filler) == 3:
                    return (filler[0].name, filler[1], filler[2])

            raise NotImplementedError("Cannot format filler %s in %s" % (str(filler), concept))

        concept = self.app.agent.memory.ontology.concept(concept)
        output = {
            "name": concept.name,
            "definition": "TODO: get definition",
            "parents": list(map(lambda p: p.name, concept.parents())),
            "rows": list(map(lambda r: _format_row(r), concept.rows()))
        }

        return json.dumps(output)


if __name__ == "__main__":

    agent = Agent(memory=Memory("../knowledge/properties/", "../knowledge/concepts/", ""))
    agent.memory.properties.load()
    agent.memory.ontology.load()

    app = DEKADE(agent)
    app.config.update(
        TEMPLATES_AUTO_RELOAD=True,
    )

    app.run("", 5000)