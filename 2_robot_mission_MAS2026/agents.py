#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

from mesa import Agent
from typing import Literal

class robotAgent(Agent):
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone
        self.carrying_waste = False
        """The attribute self.knowledge should represent the beliefs and knowledge of the
agent. The representation of these is entirely up to you! (as a bare minimum, you
might consider storing the percepts and actions at each time step)."""
        self.knowledge = {"current_position": None, "target": None, "action_history": [], "percept_history": []}
        self.action_list = Literal["move_up", "move_down", "move_left", "move_right", "pick_up", "transform", "drop"]

    def update(self, knowledge, percepts):
        pass

    def deliberate(self, knowledge):
        """the “deliberate” corresponds to the “reasoning” step of the agent. It takes as
input the “knowledge” (current position, the target, …) that has the agent at each
step and returns one or several actions (e.g. moving, collecting, etc.)

The function deliberate() is not allowed to access any variable outside its
argument. The variable action describes the action chosen by the agent, among a limited list,
such as move to an adjacent tile, pick up, transform, put down, … Its
implementation (e.g. as objects, strings, dictionaries, …) is left to you."""
        return "" 

    def step_agent(self, percepts):
        self.update(self.knowledge, percepts)
        action = self.deliberate(self.knowledge)
        percepts = self.model.do(self, action)

class greenAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=0)

class yellowAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=1)

class redAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=2) 