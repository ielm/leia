from flask import Blueprint, Flask, render_template, send_from_directory
from flask_cors import CORS
from leia.ontoagent.agent import Agent

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
        concept = self.app.agent.memory.ontology.concept(concept)
        output = {
            "name": concept.name,
            "definition": "TODO: get definition",
            "parents": list(map(lambda p: p.name, concept.parents())),
            "rows": concept.rows()
        }

        # Mock output
        output = {
            "name": concept.name,
            "definition": "This is an an example definition.",
            "parents": ["all", "object"],
            "rows": [
                {"row": "local", "property": "agent", "facet": "sem", "filler": "@primate", "meta": {}},
                {"row": "local", "property": "color", "facet": "sem", "filler": "yellow", "meta": {}},
                {"row": "local", "property": "size", "facet": "sem", "filler": (">", 1.0), "meta": {"measured-in": "inches"}},
                {"row": "inherit", "from": "object", "property": "name", "facet": "sem", "filler": ["abcd", "defg"], "meta": {}},
                {"row": "block", "from": "physical-object", "property": "theme", "facet": "sem", "filler": "@all"},
            ]
        }

        return json.dumps(output)


if __name__ == "__main__":

    agent = Agent()

    # For testing, load some fake data
    agent.memory.ontology.concept("all")
    agent.memory.ontology.concept("object")
    agent.memory.ontology.concept("physical-object")
    agent.memory.ontology.concept("animate")
    agent.memory.ontology.concept("primate")
    agent.memory.ontology.concept("human")
    agent.memory.ontology.concept("human-professional")

    app = DEKADE(agent)
    app.config.update(
        TEMPLATES_AUTO_RELOAD=True,
    )

    app.run("", 5000)