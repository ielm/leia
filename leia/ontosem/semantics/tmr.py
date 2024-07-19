from leia.ontomem.episodic import Instance, Space, XMR
from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Concept
from typing import Any, Type, Union


class TMR(XMR):

    def __init__(self, memory: Memory, name: str=None, private: bool=False, raw: Any=None, timestamp: float=None, speaker: Instance=None, listener: Instance=None):
        super().__init__(memory, name=name, private=private, raw=raw, timestamp=timestamp)
        self._speaker = speaker
        self._listener = listener

    def new_instance(self, concept: Union[str, Concept], frame_type: Type['Instance']=None) -> 'Instance':
        return super().new_instance(concept, instance_type=TMRInstance)

    def speaker(self) -> Union[Instance, None]:
        return self._speaker

    def set_speaker(self, speaker: Instance):
        self._speaker = speaker

    def listener(self) -> Union[Instance, None]:
        return self._listener

    def set_listener(self, listener: Instance):
        self._listener = listener


class TMRInstance(Instance):

    def __init__(self, memory: Memory, concept: Union[str, Concept], index: int, private_to: Space=None, grounded: bool=False):
        super().__init__(memory, concept, index)

        self.resolutions = set()        # List of ids that this frame resolves to
        self.grounded = grounded        # Ungrounded (default) means a fresh TMR frame; grounded means it already exists in agent memory

    def to_dict(self, space: Space=None) -> dict:
        out = super().to_dict(space=space)
        out["resolutions"] = list(self.resolutions)

        return out