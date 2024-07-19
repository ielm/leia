from leia.ontosem.config import OntoSemConfig
from leia.ontosem.syntax.analyzer import Preprocessor, SyntacticAnalyzer
from unittest import TestCase
from unittest.mock import MagicMock, patch


class PreprocessorTestCase(TestCase):

    def test_analyze(self):
        text = "He can't do it."
        self.assertEqual("He can not do it.", Preprocessor(OntoSemConfig()).run(text))


class SyntacticAnalyzerTestCase(TestCase):

    @patch("leia.ontosem.syntax.analyzer.subprocess")
    @patch("leia.ontosem.syntax.analyzer.Syntax")
    def test_analyze(self, mock_syntax: MagicMock, mock_subprocess: MagicMock):
        mock_subprocess.Popen = MagicMock()
        mock_process = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_process.communicate.return_value = b"[1]>\n(some lisp string)", b""
        mock_syntax.from_lisp_string.return_value = "some output"

        config = OntoSemConfig()

        text = "Some text input."
        analyzer = SyntacticAnalyzer(config)
        result = analyzer.run(text)

        self.assertEqual("some output", result)

        host = config.corenlp_host
        port = config.corenlp_port
        type = "default"
        lexicon = config.ontosyn_lexicon
        mem_file = config.ontosyn_mem

        lisp_exe = '(run-syntax \'%s \"%s\" \"%s\" \"%s\" %d)' % (type, lexicon, text, host, port)

        mock_subprocess.Popen.assert_called_once_with('clisp -q --silent -M %s' % mem_file, shell=True, stdin=mock_subprocess.PIPE, stderr=mock_subprocess.PIPE, stdout=mock_subprocess.PIPE)
        mock_process.communicate.assert_called_once_with(str.encode(lisp_exe))
        mock_syntax.from_lisp_string.assert_called_once_with("(some lisp string)")