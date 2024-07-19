from ontomem.episodic import Frame, XMR
from ontomem.memory import Memory
from ontomem.ontology import Concept
from typing import Type, Union


class TMR(XMR):

    def new_instance(self, concept: Union[str, Concept], frame_type: Type['Frame']=None) -> 'Frame':
        return super().new_instance(concept, frame_type=TMRFrame)


class TMRFrame(Frame):

    def __init__(self, memory: Memory, concept: Union[str, Concept], index: int, grounded: bool=False):
        super().__init__(memory, concept, index)

        self.resolutions = set()        # List of ids that this frame resolves to
        self.grounded = grounded        # Ungrounded (default) means a fresh TMR frame; grounded means it already exists in agent memory

    def to_dict(self) -> dict:
        out = super().to_dict()
        out["resolutions"] = list(self.resolutions)

        return out