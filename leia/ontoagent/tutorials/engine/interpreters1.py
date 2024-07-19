"""
In this tutorial we'll explore best practices for developing an interpreter to produce meaningful interpretations
of an uninterpreted XMR.

An uninterpreted XMR is an XMR whose status is RAW, contains raw data, and does not contain any meaningful frames.
The job of the interpreter is to populate the XMR with meaningful frames by interpreting the contents of the raw
data.

Here we'll make a simple interpreter, and a raw signal; the result will be a meaningfully populated XMR once
the interpreter module has run.
"""

from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.module import OntoAgentInterpretationModule
from leia.ontomem.episodic import Instance, XMR

# First, we define the custom module for our agent.


class CustomInterpretationModule(OntoAgentInterpretationModule):

    # Here we are only interested in XMRs that are raw - any XMR that is sent that is not raw should not be
    # interpreted again.  (Note, this is not a hard rule - this is for the sake of example in this tutorial;
    # it is common practice not to reanalyze, but there are certainly situations where an XMR might want
    # to be analyzed by multiple interpreters, or where an interpreter might want to take a second pass after
    # new situational data is found.)
    def allow(self, xmr: XMR) -> bool:
        # We simply check to see that the XMR has RAW status.
        return xmr.status() == XMR.Status.RAW

    @OntoAgentInterpretationModule.check_allowed
    # For this interpretation module, we'll assume it will be signaled by perception directly,
    # so we won't implement a heartbeat.
    def handle_signal(self, xmr: XMR):
        # Here we'll do the interpretation of the contents.  First, let's pull out the raw data.
        raw = xmr.raw()

        # For simplification, we're going to generate one of two frames to populate the XMR, depending
        # on the raw data.  In practice, an interpreter of raw data will likely be very complex (see OntoSem
        # as an example).

        root = xmr.new_instance("EVENT")

        if raw >= 10:
            theme = xmr.new_instance("OBJECT")
            theme.add_filler("SIZE", "very big")
            root.add_filler("THEME", theme)
        else:
            theme = xmr.new_instance("OBJECT")
            theme.add_filler("SIZE", "super small")
            root.add_filler("THEME", theme)

        # The specifics above are a toy example; the point is that the XMR itself is directly modified; in this case
        # we make a new frame in the XMR's space, and we attach that frame to the XMR's root.

        # Now that the XMR is populated with meaningful data, we need to do one more thing - update its status.
        xmr.set_status(XMR.Status.INTERPRETED)


# Now to bring it all together.

if __name__ == "__main__":

    agent = Agent()

    # First, we'll make a new instance of our module.
    m = CustomInterpretationModule(agent, "CIM")

    # Now we'll make three different XMRs.  The first will not be a raw signal; the other two will be raw,
    # and with different raw values.

    xmr1 = XMR(agent.memory, status=XMR.Status.INTERPRETED)
    xmr2 = XMR(agent.memory, raw=5, status=XMR.Status.RAW)
    xmr3 = XMR(agent.memory, raw=15, status=XMR.Status.RAW)

    # Now we'll run each XMR through the module.  The first will be rejected, the other two will be interpreted.

    m.signal(xmr1)
    m.signal(xmr2)
    m.signal(xmr3)

    # To show the results, we'll inspect the signal's root - recall that the THEME is being assigned as part of the
    # interpretation.  Let's see what this looks like:

    if xmr1.root() is None:
        print("%s has no ROOT or THEME." % xmr1.name)

    print(
        "The SIZE of the THEME of %s is: %s."
        % (xmr2.name, xmr2.root().value("THEME").value("SIZE"))
    )
    print(
        "The SIZE of the THEME of %s is: %s."
        % (xmr3.name, xmr3.root().value("THEME").value("SIZE"))
    )
