from leia.ontomem.memory import Memory
from leia.ontosem.syntax.synmapper import SynMapper
from leia.tests.LEIATestCase import LEIATestCase


class SynMapperTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory("", "", "")