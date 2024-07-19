"""
In this tutorial, we'll expand our custom reasoning module to only allow certain signals to be handled.  It may be
that another module in the architecture is overzealous when it comes to sending signals - a module may want to reject
the signal entirely, rather than handling it at all.

To accomplish this, we'll use the module's built-in allow method, and annotate the module's handle_signal method
to use it.

The heartbeat method is unaffected by this allowance filtering.
"""

from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.module import OntoAgentReasoningModule
from leia.ontomem.episodic import Instance, XMR

# First, we define the custom module for our agent.  This will have the same handle methods, but we'll add some new
# elements as well.


class CustomReasoningModule(OntoAgentReasoningModule):

    # To force the module to check for valid signals, we must override the allow method.  This method should return
    # a boolean: true means the signal is allowed by the module (it can be handled) and false means it should not
    # be handled.
    def allow(self, xmr: XMR) -> bool:
        # Here we'll make a simple check; if the XMR's root type is an object, we'll allow it.
        return xmr.root().isa(self.agent.memory.ontology.concept("OBJECT"))

    # Defining the allow function isn't quite enough - we need to also tell the module to use it prior to handling
    # a signal; to do this, we use an annotation.  The handle_signal method is otherwise unchanged from tutorial 1.

    @OntoAgentReasoningModule.check_allowed
    def handle_signal(self, xmr: XMR):
        print("Received signal %s." % xmr.name)

    # The handle_heartbeat method is the same as in tutorial 1.
    def handle_heartbeat(self):
        print("Heartbeat pulsed.")


if __name__ == "__main__":

    agent = Agent()

    # First, we'll make a new instance of our module.
    m = CustomReasoningModule(agent, "CRM")

    # Next, we'll create two signals; one is rooted in an object, and the other, in an event.
    xmr1 = XMR(agent.memory)
    xmr1.new_instance("OBJECT")

    xmr2 = XMR(agent.memory)
    xmr2.new_instance("EVENT")

    # Now, we'll send each signal to the module.  Only the first one will cause the handle function to run.
    m.signal(xmr1)
    m.signal(xmr2)
