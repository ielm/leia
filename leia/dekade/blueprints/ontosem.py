from flask import abort, Blueprint, request
from leia.dekade.app import DEKADE
from leia.ontosem.config import OntoSemConfig
from leia.ontosem.runner import OntoSemRunner

import json
import traceback


class DEKADEAPIOntoSemBlueprint(Blueprint):

    def __init__(self, app: DEKADE):
        super().__init__(
            "DEKADE-API-ONTOSEM",
            __name__,
            static_folder=app.static_folder,
            template_folder=app.template_folder,
        )
        self.app = app

        self.add_url_rule(
            "/api/ontosem/analyze",
            endpoint=None,
            view_func=self.ontosem_analyze,
            methods=["POST"],
        )

    def ontosem_analyze(self):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        if "input" not in data:
            abort(400)

        input = data["input"]

        config_file = "../../ontosem.yaml"
        config = OntoSemConfig.from_file(config_file)
        config._memory = self.app.agent.memory

        runner = OntoSemRunner(config)

        try:
            results = runner.run([input])
            results = results.to_dict()
        except Exception as e:
            results = {"error": str(e), "trace": traceback.format_tb(e.__traceback__)}

        return json.dumps(results)


cached_tmr = {
    "config": {
        "ontosyn-mem": "/Users/ivan/Dropbox/leia/RPI/OntoSem/build/ontosem2-new4.mem",
        "ontosyn-lexicon": "/Users/ivan/Dropbox/leia/RPI/OntoSem/build/lexicon.lisp",
        "corenlp-host": "localhost",
        "corenlp-port": 9002,
        "knowledge-path": "leia/knowledge/",
        "semantics-mp-mem": "/Users/ivan/Dropbox/leia/RPI/OntoSem/build/post-basic-semantic-MPs.mem",
        "ontomem-host": None,
        "ontomem-port": None,
    },
    "sentences": [
        {
            "text": "The man hit the building.",
            "syntax": {
                "words": [
                    {
                        "index": 0,
                        "lemma": "THE",
                        "pos": ["ART"],
                        "token": "The",
                        "char-start": 0,
                        "char-end": 3,
                        "ner": "NONE",
                        "coref": [],
                    },
                    {
                        "index": 1,
                        "lemma": "MAN",
                        "pos": ["N", "SINGULAR"],
                        "token": "man",
                        "char-start": 4,
                        "char-end": 7,
                        "ner": "NONE",
                        "coref": [],
                    },
                    {
                        "index": 2,
                        "lemma": "HIT",
                        "pos": ["V", "PAST"],
                        "token": "hit",
                        "char-start": 8,
                        "char-end": 11,
                        "ner": "NONE",
                        "coref": [],
                    },
                    {
                        "index": 3,
                        "lemma": "THE",
                        "pos": ["ART"],
                        "token": "the",
                        "char-start": 12,
                        "char-end": 15,
                        "ner": "NONE",
                        "coref": [],
                    },
                    {
                        "index": 4,
                        "lemma": "BUILDING",
                        "pos": ["N", "SINGULAR"],
                        "token": "building",
                        "char-start": 16,
                        "char-end": 24,
                        "ner": "NONE",
                        "coref": [],
                    },
                    {
                        "index": 5,
                        "lemma": "*PERIOD*",
                        "pos": ["PUNCT"],
                        "token": ".",
                        "char-start": 24,
                        "char-end": 25,
                        "ner": "NONE",
                        "coref": [],
                    },
                ],
                "synmap": {
                    "sense-maps": [
                        [
                            {
                                "word": 0,
                                "sense": "THE-ART1",
                                "bindings": {"$VAR0": 0, "$VAR1": 1},
                                "preference": 4.0,
                            }
                        ],
                        [
                            {
                                "word": 1,
                                "sense": "MAN-N1",
                                "bindings": {"$VAR0": 1},
                                "preference": 4.0,
                            }
                        ],
                        [
                            {
                                "word": 2,
                                "sense": "HIT-V1",
                                "bindings": {
                                    "$VAR0": 2,
                                    "$VAR1": 1,
                                    "$VAR2": 4,
                                    "$VAR3": None,
                                    "$VAR4": None,
                                },
                                "preference": 4.0,
                            }
                        ],
                        [
                            {
                                "word": 3,
                                "sense": "THE-ART1",
                                "bindings": {"$VAR0": 3, "$VAR1": 4},
                                "preference": 4.0,
                            }
                        ],
                        [
                            {
                                "word": 4,
                                "sense": "BUILDING-N1",
                                "bindings": {"$VAR0": 4},
                                "preference": 4.0,
                            }
                        ],
                        [
                            {
                                "word": 5,
                                "sense": "*PERIOD*-PUNCT1",
                                "bindings": {"$VAR0": 5},
                                "preference": 4.0,
                            }
                        ],
                    ]
                },
                "lex-senses": [],
                "sentence": "The man hit the building.",
                "original-sentence": "The man hit the building.",
                "parse": [
                    "ROOT",
                    [
                        "S",
                        ["NP", ["ART", "THE", "0"], ["N", "MAN", "1"]],
                        [
                            "VP",
                            ["V", "HIT", "2"],
                            ["NP", ["ART", "THE", "3"], ["N", "BUILDING", "4"]],
                        ],
                        ["PUNCT", "*PERIOD*", "5"],
                    ],
                ],
                "basic-deps": [
                    ["ART", "4", "3"],
                    ["SUBJECT", "2", "1"],
                    ["OBJ", "2", "4"],
                    ["ART", "1", "0"],
                    ["ROOT", "-1", "2"],
                ],
                "enhanced-deps": [
                    ["ROOT", "-1", "2"],
                    ["ART", "1", "0"],
                    ["SUBJECT", "2", "1"],
                    ["ART", "4", "3"],
                    ["OBJ", "2", "4"],
                ],
            },
            "candidates": [
                {
                    "id": "f1449183-bcea-48a4-8212-f96360f0abe5",
                    "sense-maps": [
                        {
                            "word": 0,
                            "sense": "THE-ART1",
                            "bindings": {"$VAR0": 0, "$VAR1": 1},
                            "preference": 4.0,
                        },
                        {
                            "word": 1,
                            "sense": "MAN-N1",
                            "bindings": {"$VAR0": 1},
                            "preference": 4.0,
                        },
                        {
                            "word": 2,
                            "sense": "HIT-V1",
                            "bindings": {
                                "$VAR0": 2,
                                "$VAR1": 1,
                                "$VAR2": 4,
                                "$VAR3": None,
                                "$VAR4": None,
                            },
                            "preference": 4.0,
                        },
                        {
                            "word": 3,
                            "sense": "THE-ART1",
                            "bindings": {"$VAR0": 3, "$VAR1": 4},
                            "preference": 4.0,
                        },
                        {
                            "word": 4,
                            "sense": "BUILDING-N1",
                            "bindings": {"$VAR0": 4},
                            "preference": 4.0,
                        },
                        {
                            "word": 5,
                            "sense": "*PERIOD*-PUNCT1",
                            "bindings": {"$VAR0": 5},
                            "preference": 4.0,
                        },
                    ],
                    "basic-tmr": {
                        "instances": [
                            {
                                "id": "HUMAN.1",
                                "concept": "@HUMAN",
                                "index": 1,
                                "properties": {"GENDER": ["MALE"]},
                                "resolutions": [
                                    "2.VAR.1",
                                    "1.HEAD",
                                    "0.VAR.1",
                                    "1.VAR.0",
                                ],
                            },
                            {
                                "id": "HIT.1",
                                "concept": "@HIT",
                                "index": 1,
                                "properties": {
                                    "AGENT": ["HUMAN.1"],
                                    "THEME": ["BUILDING.1"],
                                },
                                "resolutions": ["2.HEAD", "2.VAR.0"],
                            },
                            {
                                "id": "BUILDING.1",
                                "concept": "@BUILDING",
                                "index": 1,
                                "properties": {},
                                "resolutions": [
                                    "4.HEAD",
                                    "2.VAR.2",
                                    "4.VAR.0",
                                    "3.VAR.1",
                                ],
                            },
                            {
                                "id": "MEANING-PROCEDURE.1",
                                "concept": "@MEANING-PROCEDURE",
                                "index": 1,
                                "properties": {
                                    "NAME": ["RESOLVE-REFERENCE"],
                                    "PARAMETERS": ["HUMAN.1"],
                                },
                                "resolutions": [],
                            },
                            {
                                "id": "MEANING-PROCEDURE.2",
                                "concept": "@MEANING-PROCEDURE",
                                "index": 2,
                                "properties": {
                                    "NAME": ["FIX-CASE-ROLE"],
                                    "PARAMETERS": ["HUMAN.1", "HIT.1"],
                                },
                                "resolutions": [],
                            },
                            {
                                "id": "MEANING-PROCEDURE.3",
                                "concept": "@MEANING-PROCEDURE",
                                "index": 3,
                                "properties": {
                                    "NAME": ["RESOLVE-REFERENCE"],
                                    "PARAMETERS": ["BUILDING.1"],
                                },
                                "resolutions": [],
                            },
                        ]
                    },
                    "extended-tmr": {"instances": []},
                    "constraints": [],
                    "scores": [
                        {
                            "type": "SenseMapPreferenceScore",
                            "score": 1.0,
                            "message": "",
                            "sense-map": 0,
                        },
                        {
                            "type": "SenseMapPreferenceScore",
                            "score": 1.0,
                            "message": "",
                            "sense-map": 1,
                        },
                        {
                            "type": "SenseMapPreferenceScore",
                            "score": 1.0,
                            "message": "",
                            "sense-map": 2,
                        },
                        {
                            "type": "SenseMapPreferenceScore",
                            "score": 1.0,
                            "message": "",
                            "sense-map": 3,
                        },
                        {
                            "type": "SenseMapPreferenceScore",
                            "score": 1.0,
                            "message": "",
                            "sense-map": 4,
                        },
                        {
                            "type": "SenseMapPreferenceScore",
                            "score": 1.0,
                            "message": "",
                            "sense-map": 5,
                        },
                        {
                            "type": "POSTBASICSEMANTICMPSCORE",
                            "score": 1.0,
                            "message": "Test",
                        },
                    ],
                    "final-score": 1.0,
                }
            ],
        }
    ],
}
