from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.module import OntoAgentModule
from leia.ontoagent.service.blueprint import OntoAgentBlueprint
from unittest import skip, TestCase


class OntoAgentBlueprintTestCase(TestCase):

    def setUp(self):
        self.a = Agent()

    def test_build_payload_agent(self):
        payload = OntoAgentBlueprint(self.a, "test", __name__).build_payload()

        self.assertEqual(repr(self.a.instance), payload["agent"])
        self.assertEqual(repr(self.a.instance), payload["name"])

    def test_build_payload_modules(self):
        m1 = OntoAgentModule(self.a, "m1")
        m2 = OntoAgentModule(self.a, "m2")

        self.a.modules.append(m1)
        self.a.modules.append(m2)

        m2.set_service_host("localhost")
        m2.set_service_port(1234)

        payload = OntoAgentBlueprint(self.a, "test", __name__).build_payload()

        self.assertEqual([{
            "id": m1.name,
            "service": None
        }, {
            "id": m2.name,
            "service": "http://localhost:1234/%s" % m2.name
        }], payload["modules"])

    @skip("Requires scripts implementation; which may be discarded.")
    def test_build_payload_scripts(self):
        s1 = OntoAgentScript("test1", 5)
        s2 = OntoAgentScript("test2", OntoAgentScript.DURATION_INFINITE)

        payload = OntoAgentBlueprint("test", __name__).build_payload()

        self.assertEqual({
            "available": ["test1", "test2"],
            "current": None
        }, payload["scripts"])

        OntoAgentScript.current_script = s2
        s2.time = 3

        payload = OntoAgentBlueprint("test", __name__).build_payload()

        self.assertEqual({
            "available": ["test1", "test2"],
            "current": {
                "name": "test2",
                "time": 3,
                "duration": OntoAgentScript.DURATION_INFINITE
            }
        }, payload["scripts"])

    def test_output_instance_basics(self):
        i = self.a.memory.episodic.new_instance("frame")

        self.assertEqual({
            "id": i.id(),
            "fillers": [],
            "instance-of": "@frame"
        }, OntoAgentBlueprint(self.a, "test", __name__).output_instance(i))

        self.assertEqual({
            "id": i.id(),
            "fillers": [],
            "instance-of": "@frame"
        }, OntoAgentBlueprint(self.a, "test", __name__).output_instance(i))

    def test_output_filler_types(self):
        i = self.a.memory.episodic.new_instance("frame")

        i.set_filler("X", 1)
        self.assertEqual([{
            "slot": "X",
            "filler": 1,
            "type": "attribute/number"
        }], OntoAgentBlueprint(self.a, "test", __name__).output_instance(i)["fillers"])

        i.set_filler("X", 1.5)
        self.assertEqual([{
            "slot": "X",
            "filler": 1.5,
            "type": "attribute/number"
        }], OntoAgentBlueprint(self.a, "test", __name__).output_instance(i)["fillers"])

        i.set_filler("X", True)
        self.assertEqual([{
            "slot": "X",
            "filler": True,
            "type": "attribute/boolean"
        }], OntoAgentBlueprint(self.a, "test", __name__).output_instance(i)["fillers"])

        i.set_filler("X", "a")
        self.assertEqual([{
            "slot": "X",
            "filler": "a",
            "type": "attribute/text"
        }], OntoAgentBlueprint(self.a, "test", __name__).output_instance(i)["fillers"])

        i.set_filler("X", i)
        self.assertEqual([{
            "slot": "X",
            "filler": repr(i),
            "type": "relation/instance"
        }], OntoAgentBlueprint(self.a, "test", __name__).output_instance(i)["fillers"])

        i.set_filler("X", self.a.memory.ontology.concept("test"))
        self.assertEqual([{
            "slot": "X",
            "filler": repr(self.a.memory.ontology.concept("test")),
            "type": "relation/concept"
        }], OntoAgentBlueprint(self.a, "test", __name__).output_instance(i)["fillers"])

        i.set_filler("X", self.a.memory.properties.get_property("agent"))
        self.assertEqual([{
            "slot": "X",
            "filler": repr(self.a.memory.properties.get_property("agent")),
            "type": "relation/property"
        }], OntoAgentBlueprint(self.a, "test", __name__).output_instance(i)["fillers"])