from flask import abort, Blueprint, Flask, render_template, request, send_from_directory
from flask_cors import CORS
from leia.ontoagent.agent import Agent
from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Concept
from leia.ontomem.properties import Property, WILDCARD

import json
import mimetypes


mimetypes.add_type("text/javascript", ".js")


class DEKADE(Flask):

    def __init__(self, agent: Agent, static_folder: str="static/", template_folder: str="templates/"):
        super().__init__(__name__, static_folder=static_folder, template_folder=template_folder)
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
        return render_template("jinja/index.html")

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

        # OntoSem API
        self.add_url_rule("/api/ontosem/analyze", endpoint=None, view_func=self.ontosem_analyze, methods=["POST"])

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

    def ontosem_analyze(self):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        if "input" not in data:
            abort(400)

        input = data["input"]

        return json.dumps({"ONTOSEM": input})


if __name__ == "__main__":

    properties_folder = "../knowledge/properties/"
    concepts_folder = "../knowledge/concepts/"
    words_folder = "../knowledge/words/"
    static_folder = "static/"
    template_folder = "templates/"

    agent = Agent(memory=Memory(properties_folder, concepts_folder, words_folder))
    agent.memory.properties.load()
    agent.memory.ontology.load()
    # agent.memory.lexicon.load()

    app = DEKADE(agent, static_folder=static_folder, template_folder=template_folder)
    app.config.update(
        TEMPLATES_AUTO_RELOAD=True,
    )

    app.run("", 5000)