from enum import Enum
from leia.ontoagent.agent import Agent
from leia.ontomem.ontology import Concept
from leia.ontomem.episodic import XMR
from typing import Union


class Effector(object):

    class Status(Enum):
        AVAILABLE = "AVAILABLE"
        RESERVED = "RESERVED"

    def __init__(self, agent: Agent, type: Union[str, Concept]=None):
        self.agent = agent
        self._type = type
        self._status = Effector.Status.AVAILABLE
        self._reserved_to = None

    def type(self) -> Union[Concept, None]:
        if isinstance(self._type, str):
            return self.agent.memory.ontology.concept(self._type)
        return self._type

    def set_type(self, type: Union[str, Concept]):
        self._type = type

    def status(self) -> Status:
        return self._status

    def set_status(self, status: Status):
        self._status = status

    def reserved_to(self) -> Union[None, XMR]:
        return self._reserved_to

    def set_reserved_to(self, reserved_to: Union[None, XMR]):
        self._reserved_to = reserved_to

    def execute(self, *args, **kwargs):
        raise NotImplementedError

    def interrupt(self, *args, **kwargs):
        raise NotImplementedError