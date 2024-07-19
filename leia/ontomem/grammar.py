from leia.ontomem.memory import Memory
from typing import List, Union

import json


class POSInventory(object):

    def __init__(self, memory: Memory, contents_file: str, load_now: bool = True):
        self.memory = memory
        self._contents_file = contents_file
        self._entries = list()
        self._loaded = False

        if load_now:
            self.load()

    def get(self, name: str) -> "POS":
        # For now, all POS are stored in a list, rather than an indexed dict.
        # Primarily, this is due to having multiple names that could change (e.g., in learning).
        # If no matching name can be found, a new POS is made.

        # POS are case insensitive.
        name = name.upper()

        for entry in self._entries:
            if name in entry.names:
                return entry

        entry = POS([name], [], "")
        self._entries.append(entry)
        return entry

    def load(self):
        with open(self._contents_file, "r") as file:
            contents = json.load(file)
            for row in contents:
                pos = self.get(row["names"][0])
                pos.names = row["names"]
                pos.parents = list(map(lambda p: self.get(p), row["isa"]))
                pos.desc = row["desc"]

        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded


class POS(object):

    def __init__(self, names: List[str], parents: List["POS"], desc: str):
        self.names = names
        self.parents = parents
        self.desc = desc

    def isa(self, ancestry: Union["POS", str]) -> bool:
        if isinstance(ancestry, POS):
            if ancestry == self:
                return True
        if isinstance(ancestry, str):
            if ancestry.upper() in self.names:
                return True

        for parent in self.parents:
            if parent.isa(ancestry):
                return True

        return False
