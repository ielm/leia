"""
An implementation of OntoAgent is comprised of a collection of modules - these modules form the underlying capabilities
of the agent: perception, interpretation, attention, reasoning, and rendering.  Some agents may have multiple of the
same type of module, some may have none.

In this tutorial we'll create a simple reasoning module.  We'll see how this module can be called into action in the
agent architecture.
"""

from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.module import OntoAgentReasoningModule
from leia.ontomem.episodic import XMR

# First, we define the custom module for our agent.

class CustomReasoningModule(OntoAgentReasoningModule):

    # There are two methods that we should override - handle_signal and handle_heartbeat.

    # This method specifies how the module reacts to receiving a signal.  A module only receives a signal if another
    # module explicitly calls it.  This must be directed by something elsewhere in the agent architecture.  We'll
    # go over signals a bit later; for now assume the signal will contain some relevant content for this module.
    def handle_signal(self, xmr: XMR):
        # Here, we'll do something with the signal; in this trivial example, we'll just print its name.
        print("Received signal %s." % xmr.name)

    # This method specifies what the module does at each "pulse" of the agent.  The agent's heartbeat can be controlled
    # in a variety of ways, which we'll see later.  Some modules may be on a timer, some may use a global timer that
    # is shared with others.  Some modules may not have their heartbeat called at all, and rely only on signals.
    def handle_heartbeat(self):
        # Here, we'll do something when the heartbeat is pulsed.
        print("Heartbeat pulsed.")


if __name__ == "__main__":

    agent = Agent()

    # First, we'll make a new instance of our module.
    m = CustomReasoningModule(agent, "CRM")

    # Next, we'll create a signal - don't worry about the details here for now.
    xmr = XMR(agent.memory)

    # Now, we'll send the signal to our module - note that we do not call m.handle_signal(xmr).  Instead, always
    # call m.signal(xmr); this will ensure that the signal is properly dispatched to the module, even if it is
    # running on a separate service (more on this later).
    m.signal(xmr)

    # We can also pulse the module's heartbeat.  Again, we don't call m.handle_heartbeat(), but use the wrapper
    # m.heartbeat() to ensure the call is properly dispatched.
    m.heartbeat()

    # Both the signal and heartbeat methods should have printed their respective outputs.