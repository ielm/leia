from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.effector import Effector
from leia.ontoagent.engine.module import OntoAgentModule, OntoAgentModuleBlueprint, OntoAgentRenderingModule
from leia.ontomem.episodic import XMR
from unittest import TestCase
from unittest.mock import call, MagicMock, patch


class OntoAgentModuleTestCase(TestCase):

    def setUp(self):
        self.a = Agent()

    def test_process_id(self):
        m = OntoAgentModule(self.a, "test")
        m.set_process_id(1234)
        self.assertEqual(1234, m.process_id())

    def test_service_host(self):
        m = OntoAgentModule(self.a, "test")
        m.set_service_host("localhost")
        self.assertEqual("localhost", m.service_host())

    def test_service_port(self):
        m = OntoAgentModule(self.a, "test")
        m.set_service_port(1234)
        self.assertEqual(1234, m.service_port())

    def test_service(self):
        m = OntoAgentModule(self.a, "test")

        with self.assertRaises(OntoAgentModule.NoServiceDefinedError):
            m.service()

        m.set_service_host("localhost")

        with self.assertRaises(OntoAgentModule.NoServiceDefinedError):
            m.service()

        m.set_service_port(1234)

        self.assertEqual("http://localhost:1234/%s" % m.name, m.service())

    def test_signal_calls_local_if_process_ids_are_shared(self):
        m = OntoAgentModule(self.a, "test")
        m.local_signal = MagicMock()
        m.remote_signal = MagicMock()

        m.set_process_id(-1)

        xmr = XMR(self.a.memory)
        m.signal(xmr)

        m.local_signal.assert_not_called()

        import os
        m.set_process_id(os.getpid())
        m.signal(xmr)

        m.local_signal.assert_called_once_with(xmr)

    def test_signal_raises_error_if_not_defined(self):
        m = OntoAgentModule(self.a, "test")
        m.set_process_id(-1)

        xmr = XMR(self.a.memory)

        with self.assertRaises(OntoAgentModule.NoServiceDefinedError):
            m.signal(xmr)

    def test_signal_calls_remote_if_service_is_defined(self):
        m = OntoAgentModule(self.a, "test")
        m.set_process_id(-1)
        m.set_service_host("localhost")
        m.set_service_port(1234)

        m.remote_signal = MagicMock()

        xmr = XMR(self.a.memory)
        m.signal(xmr)

        m.remote_signal.assert_called_once_with(xmr)

    def test_local_signal_calls_handle(self):
        m = OntoAgentModule(self.a, "test")
        xmr = XMR(self.a.memory)

        m.handle_signal = MagicMock()

        m.local_signal(xmr)
        m.handle_signal.assert_called_once_with(xmr)

    @patch("leia.ontoagent.engine.module.urlopen")
    def test_remote_signal_calls_request(self, mock_url_open: MagicMock):
        m = OntoAgentModule(self.a, "test")
        m.set_service_host("localhost")
        m.set_service_port(1234)

        xmr = XMR(self.a.memory)

        m.remote_signal(xmr)

        mock_url_open.assert_called_once()
        args = mock_url_open.call_args
        called_request = args[0][0]

        import json
        from urllib.request import Request

        expected_request = Request("http://localhost:1234/%s/signal" % m.name, data={"signal": xmr.name}, headers={"content-type": "application/json"})

        self.assertEqual(expected_request.full_url, called_request.full_url)
        self.assertEqual(expected_request.data, json.loads(called_request.data))
        self.assertEqual(expected_request.headers, called_request.headers)

    def test_pulse_calls_local_if_process_ids_are_shared(self):
        m = OntoAgentModule(self.a, "test")
        m.local_heartbeat = MagicMock()
        m.remote_heartbeat = MagicMock()

        m.set_process_id(-1)

        m.heartbeat()

        m.local_heartbeat.assert_not_called()

        import os
        m.set_process_id(os.getpid())
        m.heartbeat()

        m.local_heartbeat.assert_called_once()

    def test_pulse_raises_error_if_not_defined(self):
        m = OntoAgentModule(self.a, "test")
        m.set_process_id(-1)

        with self.assertRaises(OntoAgentModule.NoServiceDefinedError):
            m.heartbeat()

    def test_pulse_calls_remote_if_service_is_defined(self):
        m = OntoAgentModule(self.a, "test")
        m.set_process_id(-1)
        m.set_service_host("localhost")
        m.set_service_port(1234)

        m.remote_heartbeat = MagicMock()

        m.heartbeat()

        m.remote_heartbeat.assert_called_once()

    def test_local_pulse_calls_heartbeat(self):
        m = OntoAgentModule(self.a, "test")

        m.handle_heartbeat = MagicMock()

        m.local_heartbeat()
        m.handle_heartbeat.assert_called_once()

    @patch("leia.ontoagent.engine.module.urlopen")
    def test_remote_pulse_calls_request(self, mock_url_open: MagicMock):
        m = OntoAgentModule(self.a, "test")
        m.set_service_host("localhost")
        m.set_service_port(1234)

        m.remote_heartbeat()

        mock_url_open.assert_called_once()
        args = mock_url_open.call_args
        called_request = args[0][0]

        from urllib.request import Request

        expected_request = Request("http://localhost:1234/%s/heartbeat/pulse" % m.name)

        self.assertEqual(expected_request.full_url, called_request.full_url)


class OntoAgentModuleBlueprintTestCase(TestCase):

    def setUp(self):
        self.a = Agent()

    def test_default_blueprint(self):
        m = OntoAgentModule(self.a, "test")
        bp = m.blueprint()

        self.assertEqual(m.name, bp.name)

        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(bp)

        rules = [str(p) for p in app.url_map.iter_rules()]
        self.assertIn("/signal", rules)
        self.assertIn("/heartbeat/pulse", rules)
        self.assertIn("/heartbeat/start", rules)
        self.assertIn("/heartbeat/stop", rules)

    def test_kwargs_passed_through_blueprint(self):
        bp = OntoAgentModuleBlueprint(OntoAgentModule(self.a, "test"), template_folder="/test/template/folder")
        self.assertEqual("/test/template/folder", bp.template_folder)

    def test_signal(self):
        m = OntoAgentModule(self.a, "test")
        bp = m.blueprint()
        xmr = XMR(self.a.memory)

        m.signal = MagicMock()

        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(bp)

        import json
        data = {"signal": xmr.name}
        app.test_client().post("/signal", data=json.dumps(data), content_type="application/json")

        m.signal.assert_called_once_with(xmr)

    def test_heartbeat_pulse(self):
        m = OntoAgentModule(self.a, "test")
        bp = m.blueprint()

        m.heartbeat = MagicMock()

        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(bp)

        app.test_client().post("/heartbeat/pulse")

        m.heartbeat.assert_called_once()

    def test_heartbeat_start_and_stop(self):
        m = OntoAgentModule(self.a, "test")
        bp = m.blueprint()

        m.heartbeat = MagicMock()

        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(bp)

        import json
        data = {"time": 0.01}
        app.test_client().post("/heartbeat/start", data=json.dumps(data), content_type="application/json")

        import time
        time.sleep(0.015)
        app.test_client().post("/heartbeat/stop")

        time.sleep(0.05)

        self.assertEqual(2, m.heartbeat.call_count)


class OntoAgentRenderingModuleTestCase(TestCase):

    def setUp(self):
        self.a = Agent()

    def test_effectors(self):
        m = OntoAgentRenderingModule(self.a, "test")

        e1 = Effector(self.a)
        e2 = Effector(self.a)

        self.assertEqual([], m.effectors())

        m.add_effector(e1)

        self.assertEqual([e1], m.effectors())

        m.add_effector(e2)

        self.assertEqual([e1, e2], m.effectors())

    def test_signal_instrument(self):
        m = OntoAgentRenderingModule(self.a, "test")

        xmr = XMR(self.a.memory)

        self.assertIsNone(m.signal_instrument(xmr))

        root = xmr.new_instance("event")
        instrument = xmr.new_instance("instrument")
        root.add_filler("INSTRUMENT", instrument)

        xmr.root = MagicMock(return_value=root)

        self.assertEqual(instrument, m.signal_instrument(xmr))

    def test_signal_preferred_effector_simple_match(self):
        m = OntoAgentRenderingModule(self.a, "test")
        e = Effector(self.a)
        xmr = XMR(self.a.memory)

        root = xmr.new_instance("event")
        xmr.root = MagicMock(return_value=root)

        # No preferred effector, as neither the module nor the xmr specifies
        self.assertIsNone(m.signal_preferred_effector(xmr))

        # No preferred effector, as the module has no effector
        xmr.root().add_filler("INSTRUMENT", e)
        self.assertIsNone(m.signal_preferred_effector(xmr))

        # Preferred effector as even though the instrument in the XMR is unspecified, the module has only one effector
        xmr.root().remove_filler("INSTRUMENT", e)
        m.add_effector(e)
        self.assertEqual(e, m.signal_preferred_effector(xmr))

        # Preferred effector matched as both signal and module specify
        xmr.root().add_filler("INSTRUMENT", e)
        self.assertEqual(e, m.signal_preferred_effector(xmr))

        # Preferred effectors are all effectors if the instrument is unspecified
        xmr.root().remove_filler("INSTRUMENT", e)
        m.add_effector(e) # a second effector
        self.assertEqual([e, e], m.signal_preferred_effector(xmr))

    def test_signal_preferred_effector_from_type(self):
        effector = self.a.memory.ontology.concept("effector")
        effector_child_a = self.a.memory.ontology.concept("effector-a")
        effector_child_b = self.a.memory.ontology.concept("effector-b")

        effector_child_a.add_parent(effector)
        effector_child_b.add_parent(effector)

        m = OntoAgentRenderingModule(self.a, "test")
        e1 = Effector(self.a, type=effector_child_a)
        e2 = Effector(self.a, type=effector_child_b)
        m.add_effector(e1)
        m.add_effector(e2)

        xmr = XMR(self.a.memory)
        root = xmr.new_instance("event")
        xmr.root = MagicMock(return_value=root)

        xmr.root().set_filler("INSTRUMENT", effector_child_a)
        self.assertEqual(e1, m.signal_preferred_effector(xmr))

        xmr.root().set_filler("INSTRUMENT", effector_child_b)
        self.assertEqual(e2, m.signal_preferred_effector(xmr))

        xmr.root().set_filler("INSTRUMENT", effector)
        self.assertEqual([e1, e2], m.signal_preferred_effector(xmr))