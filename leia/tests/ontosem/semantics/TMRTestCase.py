from leia.ontomem.memory import Memory
from leia.ontosem.semantics.tmr import TMR
from unittest import TestCase


class TMRTestCase(TestCase):

    def setUp(self):
        self.m = Memory()

    def test_speaker(self):
        tmr = TMR(self.m)
        self.assertIsNone(tmr.speaker())

        speaker = self.m.episodic.new_instance("human")
        tmr.set_speaker(speaker)
        self.assertEqual(speaker, tmr.speaker())

    def test_listener(self):
        tmr = TMR(self.m)
        self.assertIsNone(tmr.listener())

        listener = self.m.episodic.new_instance("human")
        tmr.set_listener(listener)
        self.assertEqual(listener, tmr.listener())


class TMRInstanceTestCase(TestCase):

    pass
