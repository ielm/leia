from flask import abort, Flask, redirect, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO
from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.module import OntoAgentModule, OntoAgentModuleBlueprint
from leia.ontoagent.service.blueprint import OntoAgentBlueprint
from typing import Dict, List, Tuple, Union

import json


class OntoAgentModuleService(Flask):

    def __init__(self, agent: Agent, host: str, port: int, head: Union[bool, Dict] = False):
        super().__init__(__name__)
        CORS(self)
        self.socketio = SocketIO(self)

        self.agent = agent
        self.host = host
        self.port = port
        self.modules: List[Tuple[OntoAgentModule, OntoAgentModuleBlueprint]] = []

        self.head_host = host
        self.head_port = port

        if isinstance(head, dict):
            self.head_host = head["host"]
            self.head_port = head["port"]
        elif head:
            self.register_blueprint(OntoAgentHeadBlueprint(self.agent, self))

        self.add_url_rule("/heartbeat/pulse", endpoint=None, view_func=self.heartbeat_pulse, methods=["POST"])
        self.add_url_rule("/heartbeat/start", endpoint=None, view_func=self.heartbeat_start, methods=["POST"])
        self.add_url_rule("/heartbeat/stop", endpoint=None, view_func=self.heartbeat_stop, methods=["POST"])

    def register(self, module: OntoAgentModule) -> OntoAgentModuleBlueprint:
        blueprint = module.blueprint()
        blueprint.set_head_host(self.head_host)
        blueprint.set_head_port(self.head_port)

        module.set_service_host(self.host)
        module.set_service_port(self.port)
        self.modules.append((module, blueprint))
        self.register_blueprint(blueprint, url_prefix="/%s" % blueprint.name)
        return blueprint

    def start(self, debug: bool=False):
        self.socketio.run(self, host=self.host, port=self.port, debug=debug)

    def stop(self):
        self.socketio.stop()

    def heartbeat_pulse(self):
        for m in self.modules:
            m[1].heartbeat_pulse()

        return "OK"

    def heartbeat_start(self):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        if "time" not in data:
            abort(400)

        self._heartbeat_start(data["time"])

        return "OK"

    def _heartbeat_start(self, time: float):
        for m in self.modules:
            m[1]._heartbeat_start(time)

    def heartbeat_stop(self):
        for m in self.modules:
            m[1].heartbeat_stop()

        return "OK"


class OntoAgentHeadBlueprint(OntoAgentBlueprint):

    def __init__(self, agent: Agent, app: OntoAgentModuleService, name: str=None, import_name: str=__name__, **kwargs):
        self.app = app
        self.loaded_models = []

        if name is None:
            name = agent.instance.id().replace(".", "-")

        super().__init__(agent, name, import_name, template_folder="resources/templates/", static_folder="resources/static/", static_url_path="", **kwargs)

        self.add_url_rule("/", endpoint=None, view_func=self.ui_head, methods=["GET"])
        self.add_url_rule("/memory", endpoint=None, view_func=self.ui_memory, methods=["GET"])
        self.add_url_rule("/memory/<id>", endpoint=None, view_func=self.ui_memory, methods=["GET"])
        self.add_url_rule("/api/instance", endpoint=None, view_func=self.api_instance, methods=["GET"])
        self.add_url_rule("/api/script/advance", endpoint=None, view_func=self.api_script_advance, methods=["POST"])
        self.add_url_rule("/api/script/load", endpoint=None, view_func=self.api_script_load, methods=["POST"])

    def ui_head(self):
        return render_template("head.html", payload=self.build_payload())

    def ui_memory(self, id: str=None):
        payload = self.build_payload()
        payload["name"] = "Memory"

        if id is not None:
            if id.startswith("@"):
                id = id[1:]
            payload["frame"] = self.output_instance(self.agent.memory.episodic.instance(id))

        return render_template("memory.html", payload=payload)

    def api_instance(self):
        id = request.args["id"]
        if id.startswith("@"):
            id = id[1:]

        instance = self.agent.memory.episodic.instance(id)
        payload = self.output_instance(instance)
        return json.dumps(payload)

    def api_script_advance(self):
        # TODO: Awaiting script implementation.
        if OntoAgentScript.current_script is not None:
            OntoAgentScript.current_script.run_next()

        return "OK"

    def api_script_load(self):
        # TODO: Awaiting script implementation.
        if not request.get_json():
            abort(400)

        data = request.get_json()
        if "script" not in data:
            abort(400)

        script = data["script"]
        script = OntoAgentScript.repository[script]
        script.time = 0
        script.run_bootstrap()

        return "OK"

    def build_payload(self):
        payload = super().build_payload()
        return payload