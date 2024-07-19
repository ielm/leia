from leia.ontomem.grammar import POSInventory
from leia.ontomem.lexicon import Lexicon
from leia.ontomem.memory import Memory
from leia.ontomem.ontology import Ontology
from leia.ontomem.transformations import TransformationsCatalogue

import os
import yaml


class OntoSemConfig(object):

    @classmethod
    def from_file(cls, filename: str) -> 'OntoSemConfig':
        with open(filename, "r") as config_file:
            config_dict = yaml.load(config_file, Loader=yaml.FullLoader)
            return OntoSemConfig(
                knowledge_path=config_dict["knowledge-path"],
                properties_path=config_dict["properties-path"],
                ontology_path=config_dict["ontology-path"],
                lexicon_path=config_dict["lexicon-path"],
                trans_path=config_dict["trans-path"],
                pos_file=config_dict["pos-file"],
            )

    def __init__(self,
                 knowledge_path: str=None,
                 properties_path: str=None,
                 ontology_path: str=None,
                 lexicon_path: str=None,
                 trans_path: str=None,
                 pos_file: str=None,
                 ):

        self.knowledge_path = self.parameter_environment_or_default(knowledge_path, "KNOWLEDGE-PATH", None)
        self.properties_path = self.parameter_environment_or_default(properties_path, "KNOWLEDGE-PATH", None)
        self.ontology_path = self.parameter_environment_or_default(ontology_path, "KNOWLEDGE-PATH", None)
        self.lexicon_path = self.parameter_environment_or_default(lexicon_path, "KNOWLEDGE-PATH", None)
        self.trans_path = self.parameter_environment_or_default(trans_path, "TRANS-PATH", None)
        self.pos_file = self.parameter_environment_or_default(pos_file, "POS-FILE", None)

        self._memory = None

    def parameter_environment_or_default(self, parameter, env_var: str, default):
        if parameter is not None:
            return parameter
        if env_var in os.environ:
            return os.environ[env_var]
        return default

    def init_ontomem(self):
        self._memory = Memory(
            knowledge_path=self.knowledge_path,
            props_path=self.properties_path,
            ont_path=self.ontology_path,
            lex_path=self.lexicon_path,
            trans_path=self.trans_path,
            pos_file=self.pos_file,
        )

    # Generates a new memory object or returns the current one
    def memory(self) -> Memory:
        if self._memory is None:
            self.init_ontomem()
        return self._memory

    # Generates a new Ontology object from the available knowledge
    def ontology(self) -> Ontology:
        return self.memory().ontology

    # Generates a new Lexicon object from the available knowledge
    def lexicon(self) -> Lexicon:
        return self.memory().lexicon

    # Generates a new Transformations Catalogue from the available knowledge
    def transformations(self) -> TransformationsCatalogue:
        return self.memory().transformations

    # Generates a new Part of Speech Inventory from the available knowledge
    def parts_of_speech(self) -> POSInventory:
        return self.memory().parts_of_speech

    def to_dict(self) -> dict:
        return {
            "knowledge-path": self.knowledge_path,
            "properties-path": self.properties_path,
            "ontology-path": self.ontology_path,
            "lexicon-path": self.lexicon_path,
            "trans-path": self.trans_path,
            "pos-file": self.pos_file,
        }