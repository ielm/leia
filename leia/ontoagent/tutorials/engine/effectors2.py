"""
In the previous tutorial we saw how to create an effector, attach it to a rendering module, and have its execute
method called when appropriate by the renderer.

Effectors are capable of a few other common pieces of functionality, all of which revolve around reserving
the effector to a certain task.  In our previous example, the effector was essentially a simulation; no practical
time was take to invoke the extend command; in reality, this will not be the case.

An effector can mark when it is currently in use, and then release that hold when it finishes its task.  A renderer
as well as any reasoner can use this information to try to schedule or prioritize actions.

In this tutorial we'll see a best practice for marking an effector's status, and see a few options for how best to
react to that status.
"""

from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.effector import Effector
from leia.ontoagent.engine.module import OntoAgentRenderingModule
from leia.ontomem.episodic import Instance, XMR

# Let's build our effector again; this one will be even simpler, as we aren't terribly concerned with its actual
# capabilities.


class SimpleEffector(Effector):

    def __init__(self, agent: Agent):
        super().__init__(agent, "SIMPLE-HAND-AND-ARM-EFFECTOR")

    def execute(self, *args, **kwargs):
        # Here we'll implement a best practice - the effector should reserve itself, perform its task, and then
        # release itself for future use.  All we are doing at this stage is marking the status - it is up to
        # the renderer to respect this, as we'll see.

        self.set_status(Effector.Status.RESERVED)

        print("Effector %s performing some task." % self)

        self.set_status(Effector.Status.AVAILABLE)

        # Note that if your effector needed to make a network call, or otherwise engage a robotic architecture element
        # that is remote, you may need to implement a callback or other, more complex design paradigm to properly
        # notify the effector that its resource should be marked as available.

    # Here we'll implement another basic function of Effector, interrupt.  Interrupt contains the code that
    # properly signals the robotic architecture to halt or stop in some recoverable and non-destructive way.
    # Interrupt is not called automatically by any part of the OntoAgent architecture, it is up to each
    # rendering module to consider when and if to do this.
    def interrupt(self, *args, **kwargs):
        print("Effector %s has safely interrupted." % self)

        # Presuming the interrupt method has been invoked without issue, the effector should be made available.
        self.set_status(Effector.Status.AVAILABLE)

    def __repr__(self):
        return self.__class__.__name__


# Next, we define a custom rendering module.
class CustomRenderingModule(OntoAgentRenderingModule):

    def __init__(self, agent: Agent, name: str, effector: "SimpleEffector"):
        super().__init__(agent, name)
        self.add_effector(effector)

    # In this rendering module, we'll want to handle the signal in a few ways; we're going to try to respect
    # both the status of the current effector, AND the priority wishes of sender of the signal.
    def handle_signal(self, xmr: XMR):
        # As before, we get our effector.
        effector = self.signal_preferred_effector(xmr)

        # Next, let's pull out the priority of the XMR.
        priority = xmr.priority()

        # Priority is one of three types: LOW, ASAP, and INTERRUPT.  The priority, by default, is considered ASAP.
        # The sender of the signal may opt to specify a priority - this is the wishes of the sender, but it is
        # entirely up to the rendering module to respect those wishes (or not).

        # In general, if the effector is available, it should be used.  If it is not, then the priority can
        # be an indicator of whether or not it should be interrupted.  Let's put some basic logic in.

        if effector.status() == Effector.Status.AVAILABLE:
            effector.execute()  # The effector is available, so we'll use it.
        else:
            if priority == XMR.Priority.INTERRUPT:
                # The sender has indicated that this is of the highest priority, so we'll interrupt what is
                # currently happening, and then execute
                effector.interrupt()
                effector.execute()
            else:
                # In all other cases, this module considers what it is currently doing to be higher priority.
                # Here it is up to the module to decide what to do - it can wait and try to reissue; or
                # it can queue the xmr and execute it as soon as it can.  It could also record an error, or even
                # signal the sender that nothing happened.  There are no generic implementations for these options,
                # it is up to the module to decide how best to handle this situation.
                print(
                    "Effector %s is currently busy, I will not interrupt it." % effector
                )


# Now let's put it all together.

if __name__ == "__main__":
    agent = Agent()

    # First, let's add some definition to our knowledge.  We need to specify that our type of effector exists,
    # and how it is implemented.
    effector = agent.memory.ontology.concept("EFFECTOR")
    effector_type = agent.memory.ontology.concept("SIMPLE-EFFECTOR").add_parent(
        effector
    )

    # Next, make an instance of our effector.
    effector = SimpleEffector(agent)

    # Now, we'll make a new instance of our module; and we'll give it an instance of our effector.
    m = CustomRenderingModule(agent, "CRM", effector)

    # We'll make an XMR (we'll keep reusing this one for convenience)
    xmr = XMR(agent.memory)

    # We should now be able to signal the module - we'll see the effector run at this point.
    m.signal(xmr)

    # If, however, we set the effector to be in use (suppose the previous signal took a long time to execute), we
    # will see different behavior.  (Note, we are manually setting the status here for demonstration; this should
    # only be done by the effector when it is run, in typical circumstances.)
    effector.set_status(Effector.Status.RESERVED)

    # Now we send the signal - but it will not execute; we will get the message about not interrupting.
    m.signal(xmr)

    # No worries - this signal is important!  Let's say so, and then resend it.  We'll see the effector is interrupted
    # and the signal is executed.
    xmr.set_priority(XMR.Priority.INTERRUPT)
    m.signal(xmr)
