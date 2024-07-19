from ontomem.episodic import Frame, Space
from typing import Any, Dict, List, Union

import time


class TMR(object):

    def __init__(self):
        self.frames = {}

    def next_frame_for_concept(self, concept: str) -> 'TMRFrame':
        instance = 0

        for f in self.frames.values():
            if f.concept == concept:
                instance = max(instance, f.instance)

        instance += 1

        frame = TMRFrame(concept, instance)
        self.frames[frame.frame_id()] = frame

        return frame

    def grounded_frame(self, concept: str, instance: int) -> 'TMRFrame':
        frame = TMRFrame(concept, instance, grounded=True)
        self.frames[frame.frame_id()] = frame

        return frame

    def remove_frame(self, frame: 'TMRFrame'):
        frame_id = frame.frame_id()

        self.frames.pop(frame_id)
        for frame in self.frames.values():
            for property, fillers in list(frame.properties.items()):
                if frame_id in fillers:
                    frame.properties[property].remove(frame_id)

    def root(self) -> Union['TMRFrame', None]:
        # Finds the current root of the TMR.
        # The root is the frame that has the least incoming and most outgoing relations.
        # EVENTs take priority over OBJECTs, who take priority over PROPERTYs (that is, a less good matching EVENT
        # is still better than any OBJECT).
        # In the case of a tie, the lower instance number wins.  Further ties = select "the first one".

        if len(self.frames) == 0:
            return None

        # Setup the scoring index
        root_scoring = {}
        for frame in self.frames.values():
            subtree = None
            ancestors = Frame(frame.concept).ancestors()
            ancestors.add(Frame(frame.concept))
            if Frame("EVENT") in ancestors:
                subtree = "EVENT"
            elif Frame("OBJECT") in ancestors:
                subtree = "OBJECT"
            elif Frame("PROPERTY") in ancestors:
                subtree = "PROPERTY"

            root_scoring[frame.frame_id()] = {
                "frame_id": frame.frame_id(),
                "subtree": subtree,
                "incoming": 0,
                "outgoing": 0,
                "instance": frame.instance
            }

        # Now modify each score
        for frame in self.frames.values():
            for property in frame.properties.keys():
                for filler in frame.fillers(property):
                    if isinstance(filler, str) and filler.startswith("@"):
                        if not "." in filler: continue
                        filler = filler.split("?")[0]
                        root_scoring[frame.frame_id()]["outgoing"] += 1
                        root_scoring[filler]["incoming"] += 1

        # Now find the best root
        candidates = []
        subtrees_present = list(map(lambda s: s["subtree"], root_scoring.values()))
        if "EVENT" in subtrees_present:
            candidates = list(filter(lambda s: s["subtree"] == "EVENT", root_scoring.values()))
        elif "OBJECT" in subtrees_present:
            candidates = list(filter(lambda s: s["subtree"] == "OBJECT", root_scoring.values()))
        elif "PROPERTY" in subtrees_present:
            candidates = list(filter(lambda s: s["subtree"] == "PROPERTY", root_scoring.values()))

        # Calculate the final score for each candidate
        for candidate in candidates:
            candidate["score"] = candidate["outgoing"] - candidate["incoming"]

        # Find the best score, then filter to candidates with that score
        best_score = max(candidates, key=lambda x: x["score"])["score"]
        candidates = list(filter(lambda c: c["score"] == best_score, candidates))

        # Find the lowest instance number, then filter to candidates with that instance
        lowest_instance = min(candidates, key=lambda x: x["instance"])["instance"]
        candidates = list(filter(lambda c: c["instance"] == lowest_instance, candidates))

        # Return the first (ideally only) candidate
        return self.frames[candidates[0]["frame_id"]]

    def to_dict(self) -> dict:
        return {
            "frames": list(map(lambda f: f.to_dict(), self.frames.values()))
        }

    def to_memory(self, text: str, speaker: str=None, listener: str=None) -> Frame:

        def next_available_space() -> str:
            spaces = Space.list_spaces()
            spaces = filter(lambda space: space.startswith("TMR#"), spaces)
            spaces = map(lambda space: int(space.replace("TMR#", "")), spaces)
            spaces = list(spaces)

            next = 1 if len(spaces) == 0 else max(spaces) + 1
            return "TMR#" + str(next)

        space = next_available_space()
        tmr = Frame("TMR.?").add_parent("TMR").add_to_space(space)
        tmr["RAW"] = text
        tmr["TIMESTAMP"] = time.time_ns()
        tmr["SPACE"] = space

        memory_map = {}
        for frame in self.frames.values():
            if frame.grounded:
                memory_map[frame.frame_id()] = Frame("%s.%d" % (frame.concept, frame.instance)).add_to_space(space).mframe.id
            else:
                memory_map[frame.frame_id()] = Frame("%s.?" % frame.concept).add_to_space(space).mframe.id

        root = self.root()
        if not Frame(root.concept) ^ "SPEECH-ACT":
            speech_act = Frame("SPEECH-ACT.?").add_parent("SPEECH-ACT").add_to_space(space)
            speech_act["THEME"] = Frame(memory_map[root.frame_id()])
            root = speech_act
        else:
            root = Frame(memory_map[root.frame_id()])

        tmr["ROOT"] = root

        if speaker is not None:
            root["AGENT"] = Frame(speaker)
        if listener is not None:
            root["BENEFICIARY"] = Frame(listener)

        for frame in self.frames.values():
            frame.to_memory(memory_map)

        return tmr

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.frames
        if isinstance(item, TMRFrame):
            return item.frame_id() in self.frames
        return False

    def __eq__(self, other):
        if isinstance(other, TMR):
            return self.frames == other.frames
        return super().__eq__(other)


class TMRFrame(object):

    def __init__(self, concept: str, instance: int, grounded: bool=False):
        self.concept = concept
        self.instance = instance
        self.properties = {}
        self.resolutions = set()        # List of ids that this frame resolves to
        self.grounded = grounded        # Ungrounded (default) means a fresh TMR frame; grounded means it already exists in agent memory

    def add_filler(self, property: str, filler: Any) -> 'TMRFrame':
        if property not in self.properties:
            self.properties[property] = []
        self.properties[property].append(filler)

        return self

    def remove_filler(self, property: str, filler: Any) -> 'TMRFrame':
        if property not in self.properties:
            return self
        self.properties[property].remove(filler)
        if len(self.properties[property]) == 0:
            del self.properties[property]

        return self

    def fillers(self, property: str) -> List[Any]:
        if property not in self.properties:
            return []
        return self.properties[property]

    def frame_id(self) -> str:
        if self.grounded:
            return "@%s.%d" % (self.concept, self.instance)

        return "@TMR.%s.%d" % (self.concept, self.instance)

    def to_dict(self) -> dict:
        return {
            "id": self.frame_id(),
            "concept": self.concept,
            "instance": self.instance,
            "properties": self.properties,
            "resolutions": list(self.resolutions)
        }

    def to_memory(self, memory_map: Dict[str, str]):
        # Memory map is a dictionary of TMRFrame.frame_id() -> Frame.mframe.id

        frame = Frame(memory_map[self.frame_id()])

        if not self.grounded:
            frame.add_parent(self.concept)

        for property in self.properties.keys():
            for filler in self.fillers(property):
                if isinstance(filler, str) and filler.startswith("@") and "." in filler and not "?" in filler:
                    filler = Frame(memory_map[filler])
                elif isinstance(filler, str) and filler.startswith("@") and "." not in filler:
                    filler = Frame(filler[1:])
                elif isinstance(filler, str) and filler.startswith("@") and "?" in filler:
                    filler_parts = filler.split("?")
                    filler = "@%s?%s" % (memory_map[filler_parts[0]], filler_parts[1])

                frame[property] += filler

        for resolution in self.resolutions:
            frame["$resolutions"] += resolution

    def __repr__(self):
        return self.frame_id()

    def __eq__(self, other):
        if isinstance(other, TMRFrame):
            return self.concept == other.concept and self.instance == other.instance
        return super().__eq__(other)