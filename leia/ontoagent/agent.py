from typing import List, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from leia.ontoagent.engine.effector import Effector
    from leia.ontoagent.engine.module import OntoAgentModule, OntoAgentRenderingModule
    from leia.ontomem.memory import Memory


class Agent(object):

    def __init__(self, memory: 'Memory'=None, modules: List['OntoAgentModule']=None, effectors: List['Effector']=None):
        from leia.ontomem.memory import Memory

        self.memory = memory if memory is not None else Memory("", "", "")
        self.modules = modules if modules is not None else []
        self.effectors = effectors if effectors is not None else []

        self.instance = self.memory.episodic.new_instance("agent")

    def heartbeat(self):
        for m in self.modules:
            m.heartbeat()

    def renderer_with_effector(self, effector: 'Effector') -> Union[None, 'OntoAgentRenderingModule']:
        from leia.ontoagent.engine.module import OntoAgentRenderingModule

        modules = filter(lambda m: isinstance(m, OntoAgentRenderingModule), self.modules)
        modules = filter(lambda m: effector in m.effectors(), modules)

        modules: List[OntoAgentRenderingModule] = list(modules)
        if len(modules) > 0:
            return modules[0]

        return None
