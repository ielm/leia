from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.module import OntoAgentModule, OntoAgentModuleBlueprint
from leia.ontoagent.service.service import OntoAgentModuleService
from unittest import TestCase
from unittest.mock import MagicMock


class OntoAgentModuleServiceTestCase(TestCase):

    def setUp(self):
        self.a = Agent()

    def test_as_head(self):
        app = OntoAgentModuleService(self.a, "1.1.1.1", 1234)
        rules = [str(p) for p in app.url_map.iter_rules()]
        self.assertNotIn("/", rules)

        app = OntoAgentModuleService(self.a, "1.1.1.1", 1234, head=True)
        rules = [str(p) for p in app.url_map.iter_rules()]
        self.assertIn("/", rules)

    def test_register_assigns_host_and_port(self):
        m = OntoAgentModule(self.a, "test")
        app = OntoAgentModuleService(self.a, "1.1.1.1", 1234)

        with self.assertRaises(OntoAgentModule.NoServiceDefinedError):
            m.service()

        app.register(m)

        self.assertEqual("http://1.1.1.1:1234/%s" % m.name, m.service())

    def test_register_with_default_blueprint(self):
        m = OntoAgentModule(self.a, "test")
        app = OntoAgentModuleService(self.a, "1.1.1.1", 1234)
        app.register(m)

        rules = [str(p) for p in app.url_map.iter_rules()]
        self.assertIn("/%s/signal" % m.name, rules)
        self.assertIn("/%s/heartbeat/pulse" % m.name, rules)
        self.assertIn("/%s/heartbeat/start" % m.name, rules)
        self.assertIn("/%s/heartbeat/stop" % m.name, rules)

    def test_register_with_custom_blueprint(self):
        m = OntoAgentModule(self.a, "test")
        app = OntoAgentModuleService(self.a, "1.1.1.1", 1234)

        class TestBlueprint(OntoAgentModuleBlueprint):
            def __init__(self, m):
                super().__init__(m)
                self.add_url_rule("/test", endpoint=None, view_func=self.test, methods=["POST"])

            def test(self): pass

        m.blueprint = MagicMock(return_value=TestBlueprint(m))
        app.register(m)

        rules = [str(p) for p in app.url_map.iter_rules()]
        self.assertIn("/%s/signal" % m.name, rules)
        self.assertIn("/%s/heartbeat/pulse" % m.name, rules)
        self.assertIn("/%s/heartbeat/start" % m.name, rules)
        self.assertIn("/%s/heartbeat/stop" % m.name, rules)
        self.assertIn("/%s/test" % m.name, rules)

    def test_register_multiple_modules(self):
        m1 = OntoAgentModule(self.a, "test1")
        m2 = OntoAgentModule(self.a, "test2")

        app = OntoAgentModuleService(self.a, "1.1.1.1", 1234)
        app.register(m1)
        app.register(m2)

        rules = [str(p) for p in app.url_map.iter_rules()]
        self.assertIn("/%s/signal" % m1.name, rules)
        self.assertIn("/%s/signal" % m2.name, rules)

    def test_heartbeat_pulse(self):
        m1 = OntoAgentModule(self.a, "test1")
        m2 = OntoAgentModule(self.a, "test2")

        m1.heartbeat = MagicMock()
        m2.heartbeat = MagicMock()

        app = OntoAgentModuleService(self.a, "1.1.1.1", 1234)
        app.register(m1)
        app.register(m2)

        app.test_client().post("/heartbeat/pulse")

        m1.heartbeat.assert_called_once()
        m2.heartbeat.assert_called_once()

    def test_heartbeat_start_and_stop(self):
        m1 = OntoAgentModule(self.a, "test1")
        m2 = OntoAgentModule(self.a, "test2")

        m1.heartbeat = MagicMock()
        m2.heartbeat = MagicMock()

        app = OntoAgentModuleService(self.a, "1.1.1.1", 1234)
        app.register(m1)
        app.register(m2)

        import json
        data = {"time": 0.01}
        app.test_client().post("/heartbeat/start", data=json.dumps(data), content_type="application/json")

        import time
        time.sleep(0.015)
        app.test_client().post("/heartbeat/stop")

        time.sleep(0.05)

        self.assertEqual(2, m1.heartbeat.call_count)
        self.assertEqual(2, m2.heartbeat.call_count)