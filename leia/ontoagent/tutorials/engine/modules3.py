"""
In this tutorial, we'll see how the agent tracks all of the modules that it has, allowing
for easy lookups.  We can also force all modules to heartbeat simultaneously from the agent.
"""

from leia.ontoagent.agent import Agent
from leia.ontoagent.engine.module import OntoAgentAttentionModule, OntoAgentReasoningModule

# First, we define the custom module for our agent.  We'll just give it a heartbeat for now - although in a real
# application, it probably should handle signaling as well.

class CustomReasoningModule(OntoAgentReasoningModule):

    # We'll clarify the heartbeat method to specify which module is active.
    def handle_heartbeat(self):
        print("Heartbeat pulsed for %s." % self.name)


if __name__ == "__main__":

    agent = Agent()

    # First, we'll make two instances of our module; we could alternatively make two different modules, with an
    # instance each, but here, we'll just reuse the same one.
    agent.modules.append(CustomReasoningModule(agent, "CRM1"))
    agent.modules.append(CustomReasoningModule(agent, "CRM2"))

    # Next, a sanity check that the agent knows about the modules.
    for m in agent.modules:
        print(m.name)

    # We can also filter modules from the agent by type; here, our modules are reasoning modules:
    for m in filter(lambda module: isinstance(module, OntoAgentReasoningModule), agent.modules):
        print(m.name)

    for m in filter(lambda module: isinstance(module, OntoAgentAttentionModule), agent.modules):
        print(m.name)  # Nothing will print, we have no attention modules

    # Finally, we can send a heartbeat to all of the modules.
    agent.heartbeat()