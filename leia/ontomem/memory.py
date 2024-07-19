from multiprocessing import Process
from threading import Thread

import functools
import json
import random
import socket
import socketserver
import string


class Memory(object):

    def __init__(self, props_path: str, ont_path: str, lex_path: str):
        from leia.ontomem.episodic import EpisodicMemory
        from leia.ontomem.lexicon import Lexicon
        from leia.ontomem.ontology import Ontology
        from leia.ontomem.properties import PropertyInventory

        self.episodic = EpisodicMemory(self)
        self.lexicon = Lexicon(self, lex_path, load_now=False)
        self.properties = PropertyInventory(self, props_path, load_now=False)
        self.ontology = Ontology(self, ont_path, load_now=False)

        self._server: OntoMemTCPServer = None

    def start_tcp_server(self, host: str="", port: int=5999):
        if self._server is not None:
            self.stop_tcp_server()

        self._server = OntoMemTCPServer.start(self, host, port)

    def stop_tcp_server(self):
        if self._server is not None:
            self._server.shutdown()
            self._server = None


class OntoMemTCPServer(socketserver.TCPServer):

    allow_reuse_address = True

    @classmethod
    def start(cls, memory: Memory, host: str, port: int, kill_message: str=None, process: bool=False) -> 'OntoMemTCPServer':

        def _start(s):

            with s as server:

                server.server_bind()
                server.server_activate()

                while server.keep_running():
                    server.handle_request()

                server.server_close()
                server.socket.close()

        s = OntoMemTCPServer(memory, host, port, kill_message)

        if process:
            process = Process(target=_start, args=(s,))
            process.start()
        else:
            thread = Thread(target=_start, args=(s,))
            thread.start()

        return s

    def __init__(self, memory: Memory, host: str, port: int, kill_message: str=None):
        super().__init__((host, port), OntoMemTCPHandler, bind_and_activate=False)
        self.memory = memory
        self.host = host
        self.port = port
        self.kill_signaled = False

        if not kill_message:
            kill_message = self.generate_kill_message()
        self.kill_message = kill_message

        self.commands = {
            "PING": OntoMemTCPRequestPing,
            "GET SENSE": OntoMemTCPRequestGetSense,
            "GET WORD": OntoMemTCPRequestGetWord,
            "GET INSTANCE": OntoMemTCPRequestGetInstance
        }

    def keep_running(self) -> bool:
        return not self.kill_signaled

    def message(self, message: str) -> str:
        return OntoMemTCPClient(self.host, self.port).message(message)

    def shutdown(self):
        self.message("KILL %s" % self.kill_message)

    def generate_kill_message(self) -> str:
        return functools.reduce(lambda x, y: x + y, map(lambda i: random.choice(string.ascii_letters), range(64)))


class OntoMemTCPHandler(socketserver.BaseRequestHandler):

    EOM_FLAG = b'##EOM'

    @classmethod
    def recvall(cls, socket) -> str:
        BUFF_SIZE = 1024
        data = b''
        while True:
            part = socket.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE or data.endswith(OntoMemTCPHandler.EOM_FLAG):
                break

        if data.endswith(OntoMemTCPHandler.EOM_FLAG):
            data = data[0:-len(OntoMemTCPHandler.EOM_FLAG)]

        return str(data.strip(), "utf-8")

    def handle(self):
        data = OntoMemTCPHandler.recvall(self.request)
        parts = data.split(" ")

        command = parts[0]
        details = " ".join(parts[1:])

        if command in self.server.commands:
            response = self.server.commands[command](self.server.memory).handle(details)
            response = bytes(response, "utf-8")
            response += OntoMemTCPHandler.EOM_FLAG
            self.request.sendall(response)
        elif command == "KILL" and details == self.server.kill_message:
            response = "Killing server."
            response = bytes(response, "utf-8")
            response += OntoMemTCPHandler.EOM_FLAG
            self.request.sendall(response)

            self.server.kill_signaled = True
        else:
            response = "Unknown command %s." % command
            response = bytes(response, "utf-8")
            response += OntoMemTCPHandler.EOM_FLAG
            self.request.sendall(response)


class OntoMemTCPClient(object):

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def message(self, message: str) -> str:
        message += str(OntoMemTCPHandler.EOM_FLAG, "utf-8")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, self.port))
            sock.sendall(bytes(message, "utf-8"))

            received = OntoMemTCPHandler.recvall(sock)

            return received


class OntoMemTCPRequest(object):

    def __init__(self, memory: Memory):
        self.memory = memory

    def handle(self, details: str) -> str:
        raise NotImplementedError


class OntoMemTCPRequestPing(OntoMemTCPRequest):

    def handle(self, details: str) -> str:
        return "GOT %s" % details


class OntoMemTCPRequestGetSense(OntoMemTCPRequest):

    def handle(self, details: str) -> str:
        try:
            sense = self.memory.lexicon.sense(details)
            return json.dumps(sense.contents)
        except:
            return json.dumps({
                "error": "unknown sense",
                "details": details
            })

class OntoMemTCPRequestGetWord(OntoMemTCPRequest):

    def handle(self, details: str) -> str:
        name = details
        include_synonyms = True
        if "synonyms=" in details:
            parts = details.split("synonyms=")
            name = parts[0].strip()
            include_synonyms = parts[1].strip().lower() == "true"

        word = self.memory.lexicon.word(name)
        return json.dumps({
            "name": word.name,
            "senses": list(map(lambda s: s.contents, word.senses(include_synonyms=include_synonyms)))
        })


class OntoMemTCPRequestGetInstance(OntoMemTCPRequest):

    def handle(self, details: str) -> str:
        instance = self.memory.episodic.instance(details)
        if instance is None:
            return json.dumps({
                "error": "unknown instance",
                "details": "#%s" % details
            })

        return json.dumps({
            "id": str(instance),
            "concept": str(instance.concept),
            "properties": dict(map(lambda kv: (kv[0], self.cast(kv[1])), instance.properties.items()))
        })

    def cast(self, fillers):
        values = []
        for f in fillers:
            value = f.value
            if isinstance(value, int) or isinstance(value, float) or isinstance(value, bool):
                values.append(value)
            else:
                values.append(str(value))
        return values