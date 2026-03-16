#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

from mesa import Agent
from model import RobotMission

class wasteAgent(Agent):
    """Agent representing a piece of waste in the environment. The 'zone' attribute indicates in which zone the waste is located (0, 1, or 2)."""
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone
    
class radioactivityAgent(Agent):
    """This agent will have no behavior but two attributes: the
zone to which it belongs and its level of radioactivity (low, medium and high). The
level of radioactivity is calculated randomly according to the zone in which this
radioactivated agent will be placed (between 0 and 0.33 for z1, between 0.33 and
0.66 for z2 and between 0.66 and 1 for z3). This radioactivity attribute will be used
by Robot agents to know in which zone they are!"""
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone
        self.radioactivity_range = model.zone_radioactivity[str(zone+1)]
        self.radioactivity_level = model.random.uniform(self.radioactivity_range[0], self.radioactivity_range[1])

class wasteDisposalAgent(Agent):
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone

