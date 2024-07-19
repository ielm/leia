from ontosem.semantics.tmr import TMR, TMRFrame
from ontomem.episodic import Frame
from unittest import TestCase
from unittest.mock import MagicMock, patch


class TMRTestCase(TestCase):

    def test_next_frame_for_concept(self):
        tmr = TMR()

        f1 = tmr.next_frame_for_concept("HUMAN")
        f2 = tmr.next_frame_for_concept("HUMAN")
        f3 = tmr.next_frame_for_concept("ALL")

        self.assertEqual("@TMR.HUMAN.1", f1.frame_id())
        self.assertEqual("@TMR.HUMAN.2", f2.frame_id())
        self.assertEqual("@TMR.ALL.1", f3.frame_id())

        self.assertEqual(f1, tmr.frames[f1.frame_id()])
        self.assertEqual(f2, tmr.frames[f2.frame_id()])
        self.assertEqual(f3, tmr.frames[f3.frame_id()])

    def test_remove_frame(self):
        tmr = TMR()

        f1 = tmr.next_frame_for_concept("TEST")
        f2 = tmr.next_frame_for_concept("TEST")

        f1.add_filler("AGENT", f2.frame_id())

        tmr.remove_frame(f2)

        self.assertIn(f1.frame_id(), tmr.frames)
        self.assertNotIn(f2.frame_id(), tmr.frames)
        self.assertEqual([], f1.fillers("AGENT"))

    def test_root(self):
        # The root is considered the EVENT with the least incoming relations and most outgoing relations.  In the case
        # of a tie, the "first" is selected.
        # If no EVENTs exist, then OBJECTs, and finally PROPERTYs are chosen.
        # None is returned if no frames exist at all.
        # Relations to concepts (not instances) are ignored.

        tmr = TMR()
        self.assertIsNone(tmr.root())

        # Property is chosen as there is no other choice
        prop1 = tmr.next_frame_for_concept("PROPERTY")
        self.assertEqual(prop1, tmr.root())

        # Object is chosen over property
        object1 = tmr.next_frame_for_concept("OBJECT")
        self.assertEqual(object1, tmr.root())

        # Event is chosen over object
        event1 = tmr.next_frame_for_concept("EVENT")
        self.assertEqual(event1, tmr.root())

        # An event with more outgoing relations (tied for incoming) is chosen
        event2 = tmr.next_frame_for_concept("EVENT")
        event2.add_filler("THEME", object1.frame_id())
        self.assertEqual(event2, tmr.root())

        # The event with the least incoming is chosen when outgoing is tied
        event1.add_filler("THEME", event2.frame_id())
        self.assertEqual(event1, tmr.root())

        # The first event is chosen in the case of a complete tie
        prop1.add_filler("SCOPE", event1.frame_id())
        self.assertEqual(event1, tmr.root())

        # Relations to concepts are ignored.
        event2.add_filler("AGENT", "@HUMAN")
        self.assertEqual(event1, tmr.root())


class TMRFrameTestCase(TestCase):

    def test_add_filler(self):
        frame = TMRFrame("TEST", 1)

        self.assertEqual([], frame.fillers("AGENT"))

        frame.add_filler("AGENT", "a")

        self.assertEqual(["a"], frame.fillers("AGENT"))

        frame.add_filler("AGENT", "b")

        self.assertEqual(["a", "b"], frame.fillers("AGENT"))

        frame.add_filler("XYZ", "c")

        self.assertEqual(["a", "b"], frame.fillers("AGENT"))
        self.assertEqual(["c"], frame.fillers("XYZ"))

    def test_remove_filler(self):
        frame = TMRFrame("TEST", 1)

        frame.remove_filler("AGENT", "a")   # Nothing happens (no errors are thrown)

        frame.add_filler("AGENT", "a")
        frame.add_filler("AGENT", "b")
        frame.add_filler("XYZ", "c")

        self.assertEqual(["a", "b"], frame.fillers("AGENT"))
        self.assertEqual(["c"], frame.fillers("XYZ"))

        frame.remove_filler("AGENT", "a")

        self.assertEqual(["b"], frame.fillers("AGENT"))
        self.assertEqual(["c"], frame.fillers("XYZ"))

        frame.remove_filler("AGENT", "b")

        self.assertEqual([], frame.fillers("AGENT"))
        self.assertNotIn("AGENT", frame.properties.keys())
        self.assertEqual(["c"], frame.fillers("XYZ"))


class TMRToOntoMemTestCase(TestCase):

    @patch("leia.ontosem.semantics.tmr.time")
    def test_tmr_to_memory(self, mock_time: MagicMock):

        # Saving a TMR to memory requires the following to happen:
        # 1) A TMR frame is created; it minimally requires the following:
        #    the RAW text
        #    a TIMESTAMP integer in nanoseconds
        #    a ROOT frame
        #    a SPACE name
        # 2) All frames inside it are converted to Frame objects, and properly mapped to each other
        #    their instance numbers may change
        #    they all need to be added to the SPACE
        #    grounded instances do not generate a new frame in memory
        # 3) The ROOT must be properly detected and/or created
        #    it must be a type of SPEECH-ACT
        #    find the apparent root of the tmr (the least incoming connected frame, choosing EVENT > OBJECT > PROPERTY)
        #    if the root is a SPEECH-ACT type, then assign it as the ROOT
        #    otherwise, make a SPEECH-ACT and set its theme to the root, then make it the ROOT
        #    the optional input "speaker" and "listener" can be assigned to the ROOT's AGENT and BENEFICIARY if empty

        tmr = TMR()
        frame1 = tmr.next_frame_for_concept("EVENT")
        frame2 = tmr.next_frame_for_concept("OBJECT")
        frame3 = tmr.grounded_frame("SOMETHING", 7)
        frame1.add_filler("THEME", frame2.frame_id())
        frame1.add_filler("AGENT", frame3.frame_id())

        tmr.root = MagicMock(return_value=frame1)
        mock_time.time_ns = MagicMock(return_value=12345)

        speaker = Frame("SPEAKER.?")
        listener = Frame("LISTENER.?")

        tmr_frame = tmr.to_memory("The man hit the building.", speaker=speaker.mframe.id, listener=listener.mframe.id)

        # First, check that the TMR frame is properly constructed
        self.assertEqual("The man hit the building.", tmr_frame["RAW"].singleton())
        self.assertEqual(12345, tmr_frame["TIMESTAMP"].singleton())
        self.assertIsNotNone(tmr_frame["SPACE"].singleton())
        self.assertIsNotNone(tmr_frame["ROOT"].singleton())
        self.assertEqual({Frame("TMR")}, tmr_frame.parents())

        # Next, verify the ROOT was properly constructed
        f1 = Frame("EVENT.1")       # This should be the generated id in this test
        f2 = Frame("OBJECT.1")
        f3 = Frame("SOMETHING.7")   # Grounded frame uses the specified instance number

        root_frame = tmr_frame["ROOT"].singleton()
        self.assertEqual({Frame("SPEECH-ACT")}, root_frame.parents())
        self.assertEqual(speaker, root_frame["AGENT"].singleton())
        self.assertEqual(listener, root_frame["BENEFICIARY"].singleton())
        self.assertEqual(f1, root_frame["THEME"].singleton())
        self.assertEqual({tmr_frame["SPACE"].singleton()}, root_frame.spaces())

        # Next, verify the SPACE contains the other frames, and they are properly connected
        self.assertEqual({tmr_frame["SPACE"].singleton()}, f1.spaces())
        self.assertEqual({tmr_frame["SPACE"].singleton()}, f2.spaces())
        self.assertEqual({tmr_frame["SPACE"].singleton()}, f3.spaces())
        self.assertEqual(f2, f1["THEME"].singleton())
        self.assertEqual(f3, f1["AGENT"].singleton())

    def test_tmr_to_memory_existing_speech_act(self):
        # Create a small ontology
        sa = Frame("SPEECH-ACT").add_to_space("ONT")
        ra = Frame("REQUEST-ACTION").add_parent(sa).add_to_space("ONT")

        tmr = TMR()
        frame = tmr.next_frame_for_concept("REQUEST-ACTION")

        tmr.root = MagicMock(return_value=frame)

        tmr_frame = tmr.to_memory("Test.")

        # Verify the ROOT was properly attached
        root_frame = tmr_frame["ROOT"].singleton()
        self.assertEqual({Frame("REQUEST-ACTION")}, root_frame.parents())

    def test_tmr_frame_to_memory(self):
        tmr_other = TMRFrame("OTHER", 1)

        # Verify the following:
        # 1) Multiple fillers for a single slot
        # 2) Relations are properly identified, and converted
        # 3) Unresolved relations are left as strings
        # 4) Resolutions are added to the $resolutions slot
        # 5) The frame's parent is assigned
        tmr_frame = TMRFrame("TEST", 1)
        tmr_frame.add_filler("AGENT", "a")
        tmr_frame.add_filler("AGENT", "b")
        tmr_frame.add_filler("XYZ", "@TMR.OTHER.1")
        tmr_frame.add_filler("DEF", "@TMR.OTHER.1?VALUE")
        tmr_frame.add_filler("GHI", "@HUMAN")

        tmr_frame.resolutions.add("3.VAR.1")
        tmr_frame.resolutions.add("2.HEAD")
        tmr_frame.resolutions.add("4.VAR.3.VALUE")

        other = Frame("OTHER.123")  # Specifically choosing an instance that does not match here
        frame = Frame("TEST.?")

        memory_map = {
            tmr_other.frame_id(): other.mframe.id,
            tmr_frame.frame_id(): frame.mframe.id,
        }

        tmr_frame.to_memory(memory_map)

        self.assertEqual(["a", "b"], frame["AGENT"].values())
        self.assertEqual(other, frame["XYZ"].singleton())
        self.assertEqual("@OTHER.123?VALUE", frame["DEF"].singleton())
        self.assertEqual(Frame("HUMAN"), frame["GHI"].singleton())
        self.assertEqual({"3.VAR.1", "2.HEAD", "4.VAR.3.VALUE"}, set(frame["$resolutions"].values()))
        self.assertEqual({Frame("TEST")}, frame.parents())
