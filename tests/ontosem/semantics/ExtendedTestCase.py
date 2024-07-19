from ontomem.memory import Memory
from ontosem.analysis import Analysis
from ontosem.config import OntoSemConfig
from ontosem.semantics.extended import BasicSemanticsMPProcessor
from ontosem.semantics.tmr import TMR, TMRInstance
from unittest import TestCase
from unittest.mock import MagicMock, patch

import json


class BasicSemanticsMPProcessorTestCase(TestCase):

    @patch("ontosem.semantics.extended.subprocess")
    def test_analyze(self, mock_subprocess: MagicMock):
        mock_subprocess.Popen = MagicMock()
        mock_process = MagicMock()
        mock_subprocess.Popen.return_value = mock_process
        mock_process.communicate.return_value = b"[1]>\n(some lisp string)", b""

        config = OntoSemConfig()

        tmr = TMR(config.memory())

        analysis = Analysis(config)
        analyzer = BasicSemanticsMPProcessor(config)
        analyzer._parse_lisp_tmrs = MagicMock(return_value={"abc": tmr})
        analyzer._assign_extended_tmrs_to_candidates = MagicMock()

        result = analyzer.run(analysis)

        self.assertEqual(analysis, result)

        mem_file = config.semantics_mp_mem

        lisp_exe = '(post-basic-semantic-MPs "%s")' % json.dumps(analysis.to_dict()).replace("\"", "\\\"")

        mock_subprocess.Popen.assert_called_once_with("clisp -q --silent -M %s" % mem_file, shell=True, stdin=mock_subprocess.PIPE, stderr=mock_subprocess.PIPE, stdout=mock_subprocess.PIPE)
        mock_process.communicate.assert_called_once_with(str.encode(lisp_exe))
        analyzer._parse_lisp_tmrs.assert_called_once_with("(some lisp string)")
        analyzer._assign_extended_tmrs_to_candidates.assert_called_once_with(analysis, {"abc": tmr})

    def test_parse_lisp_to_frame(self):
        lisp = "((ID @TMR.HUMAN.1) (CONCEPT HUMAN) (INSTANCE 1) (PROPERTIES ((GENDER (MALE)))) (RESOLUTIONS (1.HEAD 0.VAR.1 1.VAR.0 2.VAR.1)))"
        lisp = [["ID", "@TMR.HUMAN.1"], ["CONCEPT", "HUMAN"], ["INSTANCE", 1], ["PROPERTIES", [["GENDER", ["MALE"]]]], ["RESOLUTIONS", ["1.HEAD", "0.VAR.1", "1.VAR.0", "2.VAR.1"]]]

        config = OntoSemConfig()

        tmr = TMR(config.memory())

        analyzer = BasicSemanticsMPProcessor(config)

        analyzer._lisp_to_frame(tmr, lisp)

        instance: TMRInstance = tmr.instances["@TMR.HUMAN.1"]
        self.assertEqual(config.memory().ontology.concept("HUMAN"), instance.concept)
        self.assertEqual(1, instance.index)
        self.assertEqual(["MALE"], instance.values("GENDER"))
        self.assertEqual({"1.HEAD", "0.VAR.1", "1.VAR.0", "2.VAR.1"}, instance.resolutions)