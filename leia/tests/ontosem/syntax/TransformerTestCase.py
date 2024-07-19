from leia.ontomem.memory import Memory
from leia.ontosem.syntax.transformer import LexicalTransformer
from leia.tests.LEIATestCase import LEIATestCase


class LexicalTransformerTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory("", "", "")