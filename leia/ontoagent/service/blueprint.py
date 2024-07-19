from enum import Enum
from flask import Blueprint
from leia.ontoagent.agent import Agent
from leia.ontomem.episodic import Instance
from leia.ontomem.ontology import Concept
from leia.ontomem.properties import Property
from typing import Any, Tuple, Union

import pickle


class OntoAgentBlueprint(Blueprint):

    def __init__(self, agent: Agent, name: str, import_name: str, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.agent = agent

    def build_payload(self):
        from leia.ontoagent.engine.module import OntoAgentModule

        def module_service(m: OntoAgentModule) -> Union[None, str]:
            try:
                return m.service()
            except:
                return None

        return {
            "agent": repr(self.agent.instance),
            "name": repr(self.agent.instance),
            "head": {
                "host": "localhost",
                "port": 5000,
                "path": ""
            },
            "modules": list(map(lambda m: {
                "id": m.name,
                "service": module_service(m)
            }, self.agent.modules)),
            # "scripts": {
            #     "available": list(sorted(OntoAgentScript.repository.keys())),
            #     "current": None if OntoAgentScript.current_script is None else {
            #         "name": OntoAgentScript.current_script.name,
            #         "time": OntoAgentScript.current_script.time,
            #         "duration": OntoAgentScript.current_script.duration
            #     }
            # }
        }

    def output_instance(cls, instance: Instance) -> dict:

        def cast_filler(filler: Any) -> Tuple[Any, str]:
            type = "*"
            if isinstance(filler, Instance):
                type = "id"
                filler = repr(filler)
            elif isinstance(filler, Concept):
                type = "id"
                filler = repr(filler)
            elif isinstance(filler, Property):
                type = "id"
                filler = repr(filler)
            elif isinstance(filler, Enum):
                type = "enum"
                filler = "%s" % (filler.__class__.__qualname__ + "." + filler.name)
            elif filler is None:
                type = "none"
                filler = "None"
            elif isinstance(filler, str):
                filler = "%s" % (filler)
            elif isinstance(filler, int):
                pass
            elif isinstance(filler, float):
                pass
            elif isinstance(filler, bool):
                pass
            elif isinstance(filler, dict):
                pass
            else:
                type = "pickle"
                filler = memoryview(pickle.dumps(filler))

            return filler, type

        def _output_filler(filler):
            if isinstance(filler, Instance):
                return repr(filler)
            if isinstance(filler, Concept):
                return repr(filler)
            if isinstance(filler, Property):
                return repr(filler)
            if isinstance(filler, type):
                return [filler.__module__, filler.__name__]
            return cast_filler(filler)[0]

        def _output_filler_type(filler) -> str:
            if isinstance(filler, Instance):
                return "relation/instance"
            if isinstance(filler, Concept):
                return "relation/concept"
            if isinstance(filler, Property):
                return "relation/property"
            if isinstance(filler, str):
                return "attribute/text"
            if isinstance(filler, bool):
                return "attribute/boolean"
            if isinstance(filler, int) or isinstance(filler, float):
                return "attribute/number"
            if isinstance(filler, Enum):
                return "attribute/enum"
            if isinstance(filler, type):
                return "attribute/exec"
            if isinstance(filler, dict):
                return "attribute/dict"
            return "attribute/other"

        fillers = []
        for slot, fs in instance.properties.items():
            for filler in fs:
                fillers.append({
                    "slot": slot,
                    "filler": _output_filler(filler.value()),
                    "type": _output_filler_type(filler.value())
                })

        return {
            "id": instance.id(),
            "fillers": fillers,
            "instance-of": repr(instance.concept)
        }