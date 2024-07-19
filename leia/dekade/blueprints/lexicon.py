from flask import Blueprint
from leia.dekade.app import DEKADE

import json


class DEKADEAPILexiconBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__(
            "DEKADE-API-LEXICON",
            __name__,
            static_folder=app.static_folder,
            template_folder=app.template_folder,
        )
        self.app = app

        self.add_url_rule(
            "/api/knowledge/lexicon/filter/<substring>",
            endpoint=None,
            view_func=self.knowledge_lexicon_filter,
            methods=["GET"],
        )
        self.add_url_rule(
            "/api/knowledge/lexicon/sense/<sense>",
            endpoint=None,
            view_func=self.knowledge_lexicon_sense,
            methods=["GET"],
        )

    def knowledge_lexicon_filter(self, substring: str):
        substring = substring.lower()

        senses = self.app.agent.memory.lexicon.senses()
        senses = map(lambda s: s.id, senses)
        senses = filter(lambda s: substring in s.lower(), senses)

        return json.dumps(list(sorted(senses)))

    def knowledge_lexicon_sense(self, sense: str):
        sense = self.app.agent.memory.lexicon.sense(sense)

        return json.dumps(sense.to_dict())
