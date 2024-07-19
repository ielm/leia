from flask import abort, render_template, request
from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.effector import Effector
from leia.ontoagent.service.blueprint import OntoAgentBlueprint
from leia.ontomem.episodic import Instance, XMR
from leia.ontomem.ontology import Concept
from leia.utils.threads import StoppableThread
from typing import List, Union
from urllib.request import Request, urlopen

import json
import os
import time
import leia.ontoagent


class OntoAgentModule(object):

    class NoServiceDefinedError(Exception): pass

    def __init__(self, agent: Agent, name: str, process_id: int=None, service_host: str=None, service_port: int=None):
        self.agent = agent
        self.name = name
        self._process_id = process_id
        self._service_host = service_host
        self._service_port = service_port

    def set_process_id(self, process_id: int):
        self._process_id = process_id

    def process_id(self) -> Union[int, None]:
        return self._process_id

    def set_service_host(self, host: str):
        self._service_host = host

    def service_host(self) -> Union[str, None]:
        return self._service_host

    def set_service_port(self, port: int):
        self._service_port = port

    def service_port(self) -> Union[int, None]:
        return self._service_port

    def service(self) -> str:
        host = self.service_host()
        port = self.service_port()
        path = self.name

        if host is None or port is None or path is None:
            raise OntoAgentModule.NoServiceDefinedError

        return "http://%s:%s/%s" % (host, port, path)

    @classmethod
    def check_allowed(cls, func):
        def wrapper(self, *args, **kwargs):
            if self.allow(*args, **kwargs):
                func(self, *args, **kwargs)
        return wrapper

    def allow(self, xmr: XMR) -> bool:
        raise NotImplementedError("%s -> allow(xmr)" % self.name)

    def handle_signal(self, xmr: XMR):
        raise NotImplementedError("%s -> handle_signal(xmr)" % self.name)

    def handle_heartbeat(self):
        raise NotImplementedError("%s -> handle_heartbeat()" % self.name)

    def heartbeat(self):
        if os.getpid() == self.process_id():
            self.local_heartbeat()
        else:
            self.remote_heartbeat()

    def local_heartbeat(self):
        self.handle_heartbeat()

    def remote_heartbeat(self):
        url = self.service()
        request = Request("%s/heartbeat/pulse" % url, data={})
        urlopen(request)

    def signal(self, xmr: XMR):
        if os.getpid() == self.process_id():
            self.local_signal(xmr)
        else:
            self.remote_signal(xmr)

    def local_signal(self, xmr: XMR):
        self.handle_signal(xmr)

    def remote_signal(self, xmr: XMR):
        url = self.service()
        data = json.dumps({
            "signal": xmr.name
        }).encode("utf8")
        headers = {
            "content-type": "application/json"
        }

        request = Request("%s/signal" % url, data=data, headers=headers)
        urlopen(request)

    def blueprint(self) -> 'OntoAgentModuleBlueprint':
        return OntoAgentModuleBlueprint(self)


class OntoAgentModuleBlueprint(OntoAgentBlueprint):

    def __init__(self, module: OntoAgentModule, name: str=None, import_name: str=__name__, **kwargs):
        if name is None:
            name = module.name

        ontoagent_path = os.path.dirname(leia.ontoagent.__file__)
        template_path = os.path.join(ontoagent_path, "service/resources/templates/")
        static_path = os.path.join(ontoagent_path, "service/resources/static/")

        if "template_folder" not in kwargs:
            kwargs["template_folder"] = template_path
        if "static_folder" not in kwargs:
            kwargs["static_folder"] = static_path
        if "static_url_path" not in kwargs:
            kwargs["static_url_path"] = ""

        super().__init__(module.agent, name, import_name, **kwargs)
        self.module = module
        self.heartbeat_thread: HeartbeatThread = None

        self.head_host = "localhost"
        self.head_port = 5000

        self.add_url_rule("/", endpoint=None, view_func=self.ui_module, methods=["GET"])
        self.add_url_rule("/signal", endpoint=None, view_func=self.signal, methods=["POST"])
        self.add_url_rule("/heartbeat/pulse", endpoint=None, view_func=self.heartbeat_pulse, methods=["POST"])
        self.add_url_rule("/heartbeat/start", endpoint=None, view_func=self.heartbeat_start, methods=["POST"])
        self.add_url_rule("/heartbeat/stop", endpoint=None, view_func=self.heartbeat_stop, methods=["POST"])

    def set_head_host(self, host: str):
        self.head_host = host

    def set_head_port(self, port: int):
        self.head_port = port

    def build_payload(self) -> dict:
        payload = super().build_payload()

        heartbeat = None
        if self.heartbeat_thread is not None and not self.heartbeat_thread.stopped():
            heartbeat = self.heartbeat_thread.heartbeat

        payload["head"] = {"host": self.head_host, "port": self.head_port, "path": "http://%s:%d" % (self.head_host, self.head_port)}
        payload["heartbeat"] = heartbeat
        payload["name"] = str(self.module.anchor)
        payload["module"] = self.output_frame(self.module.anchor)
        payload["service"] = self.module.service()
        payload["implementation"] = self.module.implementation().__qualname__

        return payload

    def ui_module(self):
        return render_template("module.html", payload=self.build_payload())

    def signal(self):
        if not request.get_json():
            abort(400)

        data = request.get_json()
        if "signal" not in data:
            abort(400)

        xmr = data["signal"]
        if xmr.startswith("@"):
            xmr = xmr[1:]

        signal = self.module.agent.memory.episodic.space(xmr)
        self.module.signal(signal)

        return "OK"

    def heartbeat_pulse(self):
        self.module.heartbeat()

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
        if self.heartbeat_thread is not None:
            self.heartbeat_thread.stop()

        self.heartbeat_thread = HeartbeatThread(self.module, time)
        self.heartbeat_thread.start()

    def heartbeat_stop(self):
        if self.heartbeat_thread is not None:
            self.heartbeat_thread.stop()

        return "OK"


class HeartbeatThread(StoppableThread):

    def __init__(self, module: OntoAgentModule, heartbeat: float):
        super().__init__()
        self.module = module
        self.heartbeat = heartbeat

    def run(self):
        while not self.stopped():
            time.sleep(self.heartbeat)
            self.module.heartbeat()


# class OntoAgentPerceptionModule(OntoAgentModule):
#
#     @classmethod
#     def instance(cls, module_type: Union[str, Frame]=None) -> 'OntoAgentPerceptionModule':
#         if module_type is None:
#             module_type = "PERCEPTION-MODULE"
#         module: OntoAgentPerceptionModule = super().instance(module_type)
#         return module
#
#
# class OntoAgentInterpretationModule(OntoAgentModule):
#
#     @classmethod
#     def instance(cls, module_type: Union[str, Frame]=None) -> 'OntoAgentInterpretationModule':
#         if module_type is None:
#             module_type = "INTERPRETATION-MODULE"
#         module: OntoAgentInterpretationModule = super().instance(module_type)
#         return module
#
#
# class OntoAgentAttentionModule(OntoAgentModule):
#
#     @classmethod
#     def instance(cls, module_type: Union[str, Frame]=None) -> 'OntoAgentAttentionModule':
#         if module_type is None:
#             module_type = "ATTENTION-MODULE"
#         module: OntoAgentAttentionModule = super().instance(module_type)
#         return module
#
#
# class OntoAgentReasoningModule(OntoAgentModule):
#
#     @classmethod
#     def instance(cls, module_type: Union[str, Frame]=None) -> 'OntoAgentReasoningModule':
#         if module_type is None:
#             module_type = "REASONING-MODULE"
#         module: OntoAgentReasoningModule = super().instance(module_type)
#         return module
#
#
class OntoAgentRenderingModule(OntoAgentModule):

    def __init__(self, agent: Agent, name: str, process_id: int = None, service_host: str = None, service_port: int = None):
        super().__init__(agent, name, process_id=process_id, service_host=service_host, service_port=service_port)
        self._effectors = []

    def add_effector(self, effector: Effector):
        self._effectors.append(effector)

    def effectors(self) -> List[Effector]:
        return list(self._effectors)

    def signal_preferred_effector(self, xmr: XMR) -> Union[None, Effector, List[Effector]]:
        effectors = self.effectors()
        if len(effectors) == 0:
            return None

        instrument = self.signal_instrument(xmr)
        if instrument is None:
            if len(effectors) == 1:
                return effectors[0]
            return effectors

        results = []
        if isinstance(instrument, Concept):
            for e in effectors:
                e_type = e.type()
                if e_type is not None and e_type.isa(instrument):
                    results.append(e)

        else:
            for e in effectors:
                if e == instrument:
                    results.append(e)

        if len(results) == 0:
            return None
        if len(results) == 1:
            return results[0]
        return results

    def signal_instrument(self, xmr: XMR) -> Union[None, Instance]:
        root = xmr.root()
        if root is None:
            return None

        fillers = root.values("INSTRUMENT")
        if len(fillers) == 1:
            return fillers[0]

        return None