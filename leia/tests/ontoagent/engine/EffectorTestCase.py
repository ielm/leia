from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.effector import Effector
from leia.ontomem.episodic import XMR
from unittest import TestCase


class EffectorTestCase(TestCase):

    def setUp(self):
        self.a = Agent()

    def test_status(self):
        e = Effector(self.a)
        self.assertEqual(Effector.Status.AVAILABLE, e.status())

        e.set_status(Effector.Status.RESERVED)
        self.assertEqual(Effector.Status.RESERVED, e.status())

    def test_reserved_to(self):
        e = Effector(self.a)
        self.assertIsNone(e.reserved_to())

        xmr = XMR(self.a.memory)
        e.set_reserved_to(xmr)
        self.assertEqual(xmr, e.reserved_to())

    def test_type(self):
        e = Effector(self.a)
        self.assertIsNone(e.type())

        e.set_type("effector")
        self.assertEqual(self.a.memory.ontology.concept("effector"), e.type())