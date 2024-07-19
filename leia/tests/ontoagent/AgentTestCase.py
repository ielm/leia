from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.effector import Effector
from leia.ontoagent.engine.module import OntoAgentModule, OntoAgentRenderingModule
from unittest import TestCase
from unittest.mock import call, MagicMock, patch


class AgentTestCase(TestCase):

    def test_heartbeat(self):
        agent = Agent()

        m1 = OntoAgentModule(agent, "m1")
        m2 = OntoAgentModule(agent, "m2")

        m1.heartbeat = MagicMock()
        m2.heartbeat = MagicMock()

        agent.modules.append(m1)
        agent.modules.append(m2)

        agent.heartbeat()

        m1.heartbeat.assert_has_calls(calls=[call()])
        m2.heartbeat.assert_has_calls(calls=[call()])

    def test_renderer_with_effector(self):
        agent = Agent()

        m1 = OntoAgentRenderingModule(agent, "test1")
        m2 = OntoAgentRenderingModule(agent, "test2")

        agent.modules.append(m1)
        agent.modules.append(m2)

        e1 = Effector(agent)
        e2 = Effector(agent)

        self.assertIsNone(agent.renderer_with_effector(e1))

        m1.add_effector(e1)
        m2.add_effector(e2)

        self.assertEqual(m1, agent.renderer_with_effector(e1))
        self.assertEqual(m2, agent.renderer_with_effector(e2))
