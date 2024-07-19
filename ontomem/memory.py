

class Memory(object):

    def __init__(self, props_path: str, ont_path: str):
        from ontomem.ontology import Ontology
        from ontomem.properties import PropertyInventory

        self.properties = PropertyInventory(self, props_path, load_now=False)
        self.ontology = Ontology(self, ont_path, load_now=False)
