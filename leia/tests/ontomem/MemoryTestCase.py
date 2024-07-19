from leia.ontomem.lexicon import Sense
from leia.ontomem.memory import Memory, OntoMemEditBuffer, OntoMemTCPClient, OntoMemTCPRequest, OntoMemTCPServer
from leia.ontomem.memory import OntoMemTCPRequestGetInstance, OntoMemTCPRequestGetSense, OntoMemTCPRequestGetWord
from leia.tests.LEIATestCase import LEIATestCase
from unittest import TestCase

import json


class OntoMemEditBufferTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_note_edited(self):
        buffer = OntoMemEditBuffer(self.m)
        self.assertEqual(set(), buffer.edited())

        buffer.note_edited("OBJECT", "DEKADE")
        self.assertEqual({"OBJECT"}, buffer.edited())
        self.assertEqual({"OBJECT"}, buffer.edited("DEKADE"))
        self.assertEqual(set(), buffer.edited("OTHER"))

        buffer.note_edited("EVENT", "OTHER")
        self.assertEqual({"OBJECT", "EVENT"}, buffer.edited())
        self.assertEqual({"OBJECT"}, buffer.edited("DEKADE"))
        self.assertEqual({"EVENT"}, buffer.edited("OTHER"))
        self.assertEqual(set(), buffer.edited("XYZ"))

        buffer.clear(identifier="EVENT")
        self.assertEqual({"OBJECT"}, buffer.edited())
        self.assertEqual({"OBJECT"}, buffer.edited("DEKADE"))
        self.assertEqual(set(), buffer.edited("OTHER"))

        buffer.clear()
        self.assertEqual(set(), buffer.edited())


class OntoMemTCTPServerTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_server(self):
        server = OntoMemTCPServer.start(self.m, "", 6780)
        client = OntoMemTCPClient("", 6780)

        self.assertEqual("GOT ABC 123", client.message("PING ABC 123"))

        server.shutdown()

    def test_server_kill_message(self):
        server = OntoMemTCPServer.start(self.m, "", 6780)
        client = OntoMemTCPClient("", 6780)
        client.message("KILL %s" % server.kill_message)

        # The test passes because the server has turned off (nothing hangs).
        self.assertTrue(True)

    def test_server_custom_kill_message(self):
        server = OntoMemTCPServer.start(self.m, "", 6780, kill_message="NOW")
        client = OntoMemTCPClient("", 6780)
        client.message("KILL NOW")

        # The test passes because the server has turned off (nothing hangs).
        self.assertTrue(True)

    def test_server_custom_command(self):

        class TestOntoMemTCPRequest(OntoMemTCPRequest):

            def handle(self, details: str) -> str:
                return details + "DEF"

        server = OntoMemTCPServer.start(self.m, "", 6780)
        server.commands["TEST"] = TestOntoMemTCPRequest

        client = OntoMemTCPClient("", 6780)
        self.assertEqual("ABCDEF", client.message("TEST ABC"))

        server.shutdown()


class OntoMemTCPRequestGetSenseTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_handle_unknown_sense(self):
        self.assertEqual({
            "error": "unknown sense",
            "details": "TEST-X1"
        }, json.loads(OntoMemTCPRequestGetSense(self.m).handle("TEST-X1")))

    def test_handle(self):
        man_n1 = {
            "SENSE": "MAN-N1",
            "WORD": "MAN",
            "CAT": "N",
            "DEF": "",
            "EX": "",
            "COMMENTS": "",
            "SYNONYMS": ["X", "Y", "Z"],
            "HYPONYMS": ["A", "B", "C"],
            "SYN-STRUC": [
                {"type": "root"}
            ],
            "SEM-STRUC": {
                "HUMAN": {
                    "GENDER": "MALE"
                }
            },
            "TMR-HEAD": None,
            "MEANING-PROCEDURES": [],
            "OUTPUT-SYNTAX": [],
            "EXAMPLE-DEPS": [],
            "EXAMPLE-BINDINGS": [],
            "TYPES": [],
            "USE-WITH-TYPES": []
        }

        man = self.m.lexicon.word("MAN")
        man.add_sense(Sense(self.m, "MAN-N1", contents=man_n1))

        self.assertEqual(man_n1, json.loads(OntoMemTCPRequestGetSense(self.m).handle("MAN-N1")))


class OntoMemTCPRequestGetWordTestCase(LEIATestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_handle(self):
        # An unknown word can be requested
        self.assertEqual({
            "name": "MAN",
            "senses": []
        }, json.loads(OntoMemTCPRequestGetWord(self.m).handle("MAN")))

        # All senses will be returned
        man_n1 = self.mockSense("MAN-N1")
        man_n2 = self.mockSense("MAN-N2")

        man = self.m.lexicon.word("MAN")
        man.add_sense(Sense(self.m, "MAN-N1", contents=man_n1))
        man.add_sense(Sense(self.m, "MAN-N2", contents=man_n2))

        self.assertEqual({
            "name": "MAN",
            "senses": [man_n1, man_n2]
        }, json.loads(OntoMemTCPRequestGetWord(self.m).handle("MAN")))

        # Synonyms will also be returned
        other_n1 = self.mockSense("OTHER-N1", synonyms=["MAN"])

        other = self.m.lexicon.word("OTHER")
        other.add_sense(Sense(self.m, "OTHER-N1", contents=other_n1))

        self.assertEqual({
            "name": "MAN",
            "senses": [man_n1, man_n2, other_n1]
        }, json.loads(OntoMemTCPRequestGetWord(self.m).handle("MAN")))

        # Synonyms can be excluded
        self.assertEqual({
            "name": "MAN",
            "senses": [man_n1, man_n2]
        }, json.loads(OntoMemTCPRequestGetWord(self.m).handle("MAN synonyms=false")))


class OntoMemTCPRequestGetInstanceTestCase(TestCase):

    def setUp(self):
        self.m = Memory("", "", "")

    def test_handle_unknown_instance(self):
        self.assertEqual({
            "error": "unknown instance",
            "details": "#event.1"
        }, json.loads(OntoMemTCPRequestGetInstance(self.m).handle("event.1")))

    def test_handle(self):
        human = self.m.episodic.new_instance("human")

        # Verify all valid data types are exported
        instance = self.m.episodic.new_instance("event")
        instance.add_filler("instance", human)
        instance.add_filler("concept", self.m.ontology.concept("dog"))
        instance.add_filler("property", self.m.properties.get_property("color"))
        instance.add_filler("string", "abc")
        instance.add_filler("float", 123.4)
        instance.add_filler("int", 567)
        instance.add_filler("boolean", True)
        instance.add_filler("boolean", False)   # Multiple fillers will export as well

        self.assertEqual({
            "id": "#event.1",
            "concept": "@event",
            "properties": {
                "instance": ["#human.1"],
                "concept": ["@dog"],
                "property": ["$color"],
                "string": ["abc"],
                "float": [123.4],
                "int": [567],
                "boolean": [True, False]
            }
        }, json.loads(OntoMemTCPRequestGetInstance(self.m).handle("event.1")))