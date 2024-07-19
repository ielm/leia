from flask import abort, Blueprint, Flask, render_template, request, send_from_directory
from flask_cors import CORS
from leia.ontoagent.agent import Agent
from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Concept
from leia.ontomem.properties import Property, WILDCARD
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.runner import OntoSemRunner

import json
import mimetypes
import traceback


mimetypes.add_type("text/javascript", ".js")


class DEKADE(Flask):

    def __init__(
        self,
        agent: Agent,
        static_folder: str = "static/",
        template_folder: str = "templates/",
    ):
        super().__init__(
            __name__, static_folder=static_folder, template_folder=template_folder
        )
        CORS(self)

        self.agent = agent

        self.register_blueprint(DEKADEBlueprint(self))
        self.register_blueprint(DEKADEAPIBlueprint(self))


class DEKADEBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__(
            "DEKADE",
            __name__,
            static_folder=app.static_folder,
            template_folder=app.template_folder,
        )
        self.app = app

        self.add_url_rule(
            "/favicon.ico", endpoint=None, view_func=self.favicon, methods=["GET"]
        )
        self.add_url_rule("/", endpoint=None, view_func=self.index, methods=["GET"])
        self.add_url_rule(
            "/handlebars/<path:path>",
            endpoint=None,
            view_func=self.handlebars_template,
            methods=["GET"],
        )

    def read_template(self, name: str) -> str:
        with open("%s/%s" % (self.template_folder, name), "r") as f:
            return f.read()

    def favicon(self):
        return send_from_directory(
            self.static_folder, "favicon.ico", mimetype="image/vnd.microsoft.icon"
        )

    def index(self):
        return render_template("jinja/index.html")

    def handlebars_template(self, path):
        return self.read_template("handlebars/%s" % path)


class DEKADEAPIBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__(
            "DEKADE-API",
            __name__,
            static_folder=app.static_folder,
            template_folder=app.template_folder,
        )
        self.app = app

        # Lexicon API
        from leia.dekade.blueprints.lexicon import DEKADEAPILexiconBlueprint

        self.register_blueprint(DEKADEAPILexiconBlueprint(self.app))

        # Ontology API
        from leia.dekade.blueprints.ontology import DEKADEAPIOntologyBlueprint

        self.register_blueprint(DEKADEAPIOntologyBlueprint(self.app))

        # Properties API
        from leia.dekade.blueprints.properties import DEKADEAPIPropertiesBlueprint

        self.register_blueprint(DEKADEAPIPropertiesBlueprint(self.app))

        # OntoSem API
        from leia.dekade.blueprints.ontosem import DEKADEAPIOntoSemBlueprint

        self.register_blueprint(DEKADEAPIOntoSemBlueprint(self.app))


if __name__ == "__main__":

    static_folder = "static/"
    template_folder = "templates/"

    agent = Agent()
    agent.memory.properties.load()
    agent.memory.ontology.load()
    agent.memory.lexicon.load()

    app = DEKADE(agent, static_folder=static_folder, template_folder=template_folder)
    app.config.update(
        TEMPLATES_AUTO_RELOAD=True,
    )

    app.run("", 5000)
