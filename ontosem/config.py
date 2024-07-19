from ontomem.lexicon import Lexicon
from ontomem.memory import Memory, TCPMemory
from ontomem.ontology import Ontology

import os
import yaml


class OntoSemConfig(object):

    @classmethod
    def from_file(cls, filename: str) -> 'OntoSemConfig':
        with open(filename, "r") as config_file:
            config_dict = yaml.load(config_file, Loader=yaml.FullLoader)
            return OntoSemConfig(
                ontosyn_mem=config_dict["ontosyn-mem-file"],
                ontosyn_lexicon=config_dict["ontosyn-lex-file"],
                corenlp_host=config_dict["corenlp-host"],
                corenlp_port=config_dict["corenlp-port"],
                knowledge_path=config_dict["knowledge-path"],
                semantics_mp_mem=config_dict["semantics-mp-mem-file"],
                ontomem_host=config_dict["ontomem-host"] if "ontomem-host" in config_dict else None,
                ontomem_port=config_dict["ontomem-port"] if "ontomem-port" in config_dict else None,
            )

    def __init__(self,
                 ontosyn_mem: str=None,
                 ontosyn_lexicon: str=None,
                 corenlp_host: str=None,
                 corenlp_port: int=None,
                 knowledge_path: str=None,
                 semantics_mp_mem: str=None,
                 ontomem_host: str=None,
                 ontomem_port: int=None):
        self.ontosyn_mem = self.parameter_environment_or_default(ontosyn_mem, "ONTOSYN-MEM-FILE", "build/ontosem2-new4.mem")
        self.ontosyn_lexicon = self.parameter_environment_or_default(ontosyn_lexicon, "ONTOSYN-LEX-FILE", "ontosyn/lisp/lexicon.lisp")
        self.corenlp_host = self.parameter_environment_or_default(corenlp_host, "CORENLP_HOST", "localhost")
        self.corenlp_port = int(self.parameter_environment_or_default(corenlp_port, "CORENLP_PORT", 9002))
        self.knowledge_path = self.parameter_environment_or_default(knowledge_path, "KNOWLEDGE-PATH", "knowledge/")
        self.semantics_mp_mem = self.parameter_environment_or_default(semantics_mp_mem, "SEMANTICS-MP-MEM-FILE", "build/post-basic-semantic-MPs.mem")
        self.ontomem_host = self.parameter_environment_or_default(ontomem_host, "ONTOMEM-HOST", None)
        self.ontomem_port = self.parameter_environment_or_default(ontomem_port, "ONTOMEM-PORT", None)

        self._memory = None

    def parameter_environment_or_default(self, parameter, env_var: str, default):
        if parameter is not None:
            return parameter
        if env_var in os.environ:
            return os.environ[env_var]
        return default

    def init_ontomem(self):
        if self.ontomem_host is not None and self.ontomem_port is not None:
            self._memory = TCPMemory(self.ontomem_host, self.ontomem_port)
        else:
            props_path = "%s/properties" % self.knowledge_path
            concepts_path = "%s/concepts" % self.knowledge_path
            lex_path = "%s/words" % self.knowledge_path

            self._memory = Memory(props_path, concepts_path, lex_path)

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

    def to_dict(self) -> dict:
        return {
            "ontosyn-mem": self.ontosyn_mem,
            "ontosyn-lexicon": self.ontosyn_lexicon,
            "corenlp-host": self.corenlp_host,
            "corenlp-port": self.corenlp_port,
            "knowledge-path": self.knowledge_path,
            "semantics-mp-mem": self.semantics_mp_mem,
            "ontomem-host": self.ontomem_host,
            "ontomem-port": self.ontomem_port,
        }