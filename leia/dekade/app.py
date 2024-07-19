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
        self.add_url_rule("/api/knowledge/ontology/children/<concept>", endpoint=None, view_func=self.knowledge_ontology_children, methods=["GET"])

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

    def knowledge_ontology_children(self, concept: str):
        concept = self.app.agent.memory.ontology.concept(concept)
        children = concept.children()
        children = sorted(list(map(lambda c: c.name, children)))

        return json.dumps(children)

    def ontosem_analyze(self):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        if "input" not in data:
            abort(400)

        input = data["input"]

        # config_file = "../../ontosem.yaml"
        # config = OntoSemConfig.from_file(config_file)
        # config._memory = self.app.agent.memory
        #
        # runner = OntoSemRunner(config)
        # results = runner.run([input])
        # results = results.to_dict()

        results = cached_tmr

        return json.dumps(results)


cached_tmr = {'config': {'ontosyn-mem': '/Users/jesse/Documents/RPI/OntoSem/build/ontosem2-new4.mem', 'ontosyn-lexicon': '/Users/jesse/Documents/RPI/OntoSem/build/lexicon.lisp', 'corenlp-host': 'localhost', 'corenlp-port': 9002, 'knowledge-path': 'leia/knowledge/', 'semantics-mp-mem': '/Users/jesse/Documents/RPI/OntoSem/build/post-basic-semantic-MPs.mem', 'ontomem-host': None, 'ontomem-port': None}, 'sentences': [{'text': 'The man hit the building.', 'syntax': {'words': [{'index': 0, 'lemma': 'THE', 'pos': ['ART'], 'token': 'The', 'char-start': 0, 'char-end': 3, 'ner': 'NONE', 'coref': []}, {'index': 1, 'lemma': 'MAN', 'pos': ['N', 'SINGULAR'], 'token': 'man', 'char-start': 4, 'char-end': 7, 'ner': 'NONE', 'coref': []}, {'index': 2, 'lemma': 'HIT', 'pos': ['V', 'PAST'], 'token': 'hit', 'char-start': 8, 'char-end': 11, 'ner': 'NONE', 'coref': []}, {'index': 3, 'lemma': 'THE', 'pos': ['ART'], 'token': 'the', 'char-start': 12, 'char-end': 15, 'ner': 'NONE', 'coref': []}, {'index': 4, 'lemma': 'BUILDING', 'pos': ['N', 'SINGULAR'], 'token': 'building', 'char-start': 16, 'char-end': 24, 'ner': 'NONE', 'coref': []}, {'index': 5, 'lemma': '*PERIOD*', 'pos': ['PUNCT'], 'token': '.', 'char-start': 24, 'char-end': 25, 'ner': 'NONE', 'coref': []}], 'synmap': {'sense-maps': [[{'word': 0, 'sense': 'THE-ART1', 'bindings': {'$VAR0': 0, '$VAR1': 1}, 'preference': 4.0}], [{'word': 1, 'sense': 'MAN-N1', 'bindings': {'$VAR0': 1}, 'preference': 4.0}], [{'word': 2, 'sense': 'HIT-V1', 'bindings': {'$VAR0': 2, '$VAR1': 1, '$VAR2': 4, '$VAR3': None, '$VAR4': None}, 'preference': 4.0}], [{'word': 3, 'sense': 'THE-ART1', 'bindings': {'$VAR0': 3, '$VAR1': 4}, 'preference': 4.0}], [{'word': 4, 'sense': 'BUILDING-N1', 'bindings': {'$VAR0': 4}, 'preference': 4.0}], [{'word': 5, 'sense': '*PERIOD*-PUNCT1', 'bindings': {'$VAR0': 5}, 'preference': 4.0}]]}, 'lex-senses': [], 'sentence': 'The man hit the building.', 'original-sentence': 'The man hit the building.', 'parse': ['ROOT', ['S', ['NP', ['ART', 'THE', '0'], ['N', 'MAN', '1']], ['VP', ['V', 'HIT', '2'], ['NP', ['ART', 'THE', '3'], ['N', 'BUILDING', '4']]], ['PUNCT', '*PERIOD*', '5']]], 'basic-deps': [['ART', '4', '3'], ['SUBJECT', '2', '1'], ['OBJ', '2', '4'], ['ART', '1', '0'], ['ROOT', '-1', '2']], 'enhanced-deps': [['ROOT', '-1', '2'], ['ART', '1', '0'], ['SUBJECT', '2', '1'], ['ART', '4', '3'], ['OBJ', '2', '4']]}, 'candidates': [{'id': 'f1449183-bcea-48a4-8212-f96360f0abe5', 'sense-maps': [{'word': 0, 'sense': 'THE-ART1', 'bindings': {'$VAR0': 0, '$VAR1': 1}, 'preference': 4.0}, {'word': 1, 'sense': 'MAN-N1', 'bindings': {'$VAR0': 1}, 'preference': 4.0}, {'word': 2, 'sense': 'HIT-V1', 'bindings': {'$VAR0': 2, '$VAR1': 1, '$VAR2': 4, '$VAR3': None, '$VAR4': None}, 'preference': 4.0}, {'word': 3, 'sense': 'THE-ART1', 'bindings': {'$VAR0': 3, '$VAR1': 4}, 'preference': 4.0}, {'word': 4, 'sense': 'BUILDING-N1', 'bindings': {'$VAR0': 4}, 'preference': 4.0}, {'word': 5, 'sense': '*PERIOD*-PUNCT1', 'bindings': {'$VAR0': 5}, 'preference': 4.0}], 'basic-tmr': {'instances': [{'id': 'HUMAN.1', 'concept': '@HUMAN', 'index': 1, 'properties': {'GENDER': ['MALE']}, 'resolutions': ['2.VAR.1', '1.HEAD', '0.VAR.1', '1.VAR.0']}, {'id': 'HIT.1', 'concept': '@HIT', 'index': 1, 'properties': {'AGENT': ['HUMAN.1'], 'THEME': ['BUILDING.1']}, 'resolutions': ['2.HEAD', '2.VAR.0']}, {'id': 'BUILDING.1', 'concept': '@BUILDING', 'index': 1, 'properties': {}, 'resolutions': ['4.HEAD', '2.VAR.2', '4.VAR.0', '3.VAR.1']}, {'id': 'MEANING-PROCEDURE.1', 'concept': '@MEANING-PROCEDURE', 'index': 1, 'properties': {'NAME': ['RESOLVE-REFERENCE'], 'PARAMETERS': ['HUMAN.1']}, 'resolutions': []}, {'id': 'MEANING-PROCEDURE.2', 'concept': '@MEANING-PROCEDURE', 'index': 2, 'properties': {'NAME': ['FIX-CASE-ROLE'], 'PARAMETERS': ['HUMAN.1', 'HIT.1']}, 'resolutions': []}, {'id': 'MEANING-PROCEDURE.3', 'concept': '@MEANING-PROCEDURE', 'index': 3, 'properties': {'NAME': ['RESOLVE-REFERENCE'], 'PARAMETERS': ['BUILDING.1']}, 'resolutions': []}]}, 'extended-tmr': {'instances': []}, 'constraints': [], 'scores': [{'type': 'SenseMapPreferenceScore', 'score': 1.0, 'message': '', 'sense-map': 0}, {'type': 'SenseMapPreferenceScore', 'score': 1.0, 'message': '', 'sense-map': 1}, {'type': 'SenseMapPreferenceScore', 'score': 1.0, 'message': '', 'sense-map': 2}, {'type': 'SenseMapPreferenceScore', 'score': 1.0, 'message': '', 'sense-map': 3}, {'type': 'SenseMapPreferenceScore', 'score': 1.0, 'message': '', 'sense-map': 4}, {'type': 'SenseMapPreferenceScore', 'score': 1.0, 'message': '', 'sense-map': 5}, {'type': 'POSTBASICSEMANTICMPSCORE', 'score': 1.0, 'message': 'Test'}], 'final-score': 1.0}]}]}


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