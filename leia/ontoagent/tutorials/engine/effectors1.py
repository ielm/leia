"""
In this tutorial, we'll cover effectors and their use in rendering modules.

As a rule, it is not *required* to use effectors for your rendering module to be successful.  The contents of a
rendering module can fully specify how to enact the real-world (or simulation) effects.  Effectors are useful
for managing how the renderer's capabilities might vary or be limited in scope.  For example, a physical hand can
only be holding one object at a time; if the hand is busy, asking the module to hold a second object may or may
not work out well.

In the OntoAgent architecture, the effector represents the actual means of changing the environment.  The hand
is an effector.  The rendering module represents the means of controlling that effector and viewing it as a resource.
As a best practice, the actual robotic controls should be handled by the effector, but in certain situations they
could be handled by the module itself.

Let's build an example to better understand the differences.
"""

from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.effector import Effector
from leia.ontoagent.engine.module import OntoAgentRenderingModule
from leia.ontomem.episodic import Instance, XMR

# To start, let's build an effector.  This effector is going to represent a hand attached to an arm.
# It has a few basic commands - it can extend or retract a specified distance, and it can grasp or release.

class SimpleHandAndArmEffector(Effector):

    # First, we'll override the __init__ method; we want to specify that, ontologically, this effector
    # has a certain type.  We'll see the knowledge contents below.
    def __init__(self, agent: Agent):
        super().__init__(agent, "SIMPLE-HAND-AND-ARM-EFFECTOR")

    # If you intend to use the effector as the logical operation of its robotic counterpart, you must implement
    # the execute method.  You can take any arbitrary arguments you desire, and then execute the code as wanted.
    # The actual signature is execute(*args, **kwargs); override it for your operation.
    def execute(self, command: str, params: dict):
        # Recall, our effector has four known commands; we'll switch on them here.  An effector with only one
        # command could simply execute it here.
        if command == "extend":
            self.extend(params["distance"])
        elif command == "retract":
            self.retract(params["distance"])
        elif command == "grasp":
            self.grasp()
        elif command == "release":
            self.release()

    # And now we'll implement the details of each command; since this is a tutorial / simulation, there is no
    # actual robot, so we'll simple log the command.  In practice, here you would issue a command to your
    # robotic architecture.

    def extend(self, distance: float):
        print("Extending %s %f centimeters." % (self, distance))

    def retract(self, distance: float):
        print("Retracting %s %f centimeters." % (self, distance))

    def grasp(self):
        print("Grasping with %s." % self)

    def release(self):
        print("Releasing with %s." % self)

    # This is a physical effector, so we must track its location in space (we'll simplify by just tracking a single value)

    def set_location(self, location: float):
        self.location = location

    def __repr__(self):
        return self.__class__.__name__

# Next, we define a custom rendering module.
class CustomRenderingModule(OntoAgentRenderingModule):

    # To begin with, let's declare that an instance of this module necessarily has a corresponding effector.
    # To do this, we'll override the __init__ method, and add one in.
    def __init__(self, agent: Agent, name: str, effector: 'SimpleHandAndArmEffector'):
        super().__init__(agent, name)
        self.add_effector(effector)

    # Here, we only care to implement handling a signal; we don't need a heartbeat.
    # The signal receives is an XMR - it is a meaning representation.  We need to distill it down into effector
    # commands, so some reasoning that is specific to this module is required.
    def handle_signal(self, xmr: XMR):
        # The first step is to get our effector; while we know in this case that there is only one, a better
        # practice is to use the signal_preferred_effector(xmr) method.  This method looks into the signal for
        # any INSTRUMENT listed in the root, and tries to align it with effectors in this module.  If a specific
        # effector is requested, that will be returned; if an effector type is requested, effectors of that type
        # will be returned.  Default values in the case the XMR has no preference will also be used.
        effector: SimpleHandAndArmEffector = self.signal_preferred_effector(xmr)

        # Here the rendering module can now pick apart the XMR, and convert it into something appropriate for the
        # effector.  Remember that we could have used the @OntoAgentReasoningModule.check_allowed annotation from
        # tutorial 2 if we wanted to verify the form of the XMR prior to handling it.

        # Let's assume the xmr is in good form; we are looking for a single action (for this example), and we
        # expect it to be a MOVE event.

        event = xmr.root()
        if not event.concept.isa(self.agent.memory.ontology.concept("MOVE")):
            raise Exception

        theme = event.value("THEME")
        destination = event.value("DESTINATION")

        print("I am going to move %s to %s." % (theme, destination))

        # To render this intention in reality, we need a few more bits of detail.  Where exactly the THEME is,
        # where exactly the EFFECTOR is, and where exactly the DESTINATION is.  As this is a tutorial, and the
        # effector can only move in one dimension, we'll use a simple LOCATION value (a single number) to represent
        # distance from the agent.

        effector_location = effector.location
        theme_location = theme.value("LOCATION")
        destination_location = destination.value("LOCATION")

        # Now let's render; first, move the effector to the theme.
        distance = theme_location - effector_location
        if distance >= 0:
            effector.execute("extend", {"distance": distance})
        else:
            effector.execute("retract", {"distance": abs(distance)})

        # Now, grasp the object.
        effector.execute("grasp", {})

        # Now, move the object to the destination.
        distance = destination_location - theme_location
        if distance >= 0:
            effector.execute("extend", {"distance": distance})
        else:
            effector.execute("retract", {"distance": abs(distance)})

        # Finally, release the object.
        effector.execute("release", {})


# Now let's put it all together.

if __name__ == "__main__":
    agent = Agent()

    # First, let's add some definition to our knowledge.  We need to specify that our type of effector exists,
    # and how it is implemented.
    agent.memory.ontology.concept("MOVE").add_parent(agent.memory.ontology.concept("EVENT"))
    effector = agent.memory.ontology.concept("EFFECTOR")
    effector_type = agent.memory.ontology.concept("SIMPLE-HAND-AND-ARM-EFFECTOR").add_parent(effector)

    # Next, make an instance of our effector.
    effector = SimpleHandAndArmEffector(agent)

    # Now, we'll make a new instance of our module; and we'll give it an instance of our effector.
    m = CustomRenderingModule(agent, "CRM", effector)

    # Let's create the object and the destination.
    env = agent.memory.episodic.space("ENV")
    o = env.new_instance("OBJECT")
    p = env.new_instance("PLACE")

    # Now, give all of the relevant things a location; remember, we are using a simple location (distance from the
    # agent in one direction).

    effector.set_location(1)        # It is close by.
    o.add_filler("LOCATION", 5.5)   # It is farther away.
    p.add_filler("LOCATION", 3)     # It is between the effector and object.

    # Now, we create the signal.  It is an XMR; we only put the meaning into this.  The XMR just says "move the
    # object to the place", and nothing more.
    xmr = XMR(agent.memory)
    root = xmr.new_instance("MOVE")
    root.add_filler("AGENT", agent.instance)
    root.add_filler("THEME", o)
    root.add_filler("DESTINATION", p)

    # Now, we send the signal to the rendering module.  It should select its effector, and render the meaning
    # into specific commands that are executed.  You should see a printed log of the specifics.

    m.signal(xmr)