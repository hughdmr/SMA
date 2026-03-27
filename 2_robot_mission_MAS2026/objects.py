#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

from mesa import Agent

class wasteAgent(Agent):
    """This agent will represent the object waste, and will have an
attribute allowing to distinguish between green, yellow and red waste."""
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone
        self.waste_type = ["green", "yellow", "red"][zone]
        self.is_collected = False
        self.is_transformed = False

    def collect(self):
        self.is_collected = True

    def transform(self):
        if self.is_collected:
            if self.waste_type == "green":
                self.waste_type = "yellow"
            elif self.waste_type == "yellow":
                self.waste_type = "red"
            self.is_transformed = True
    
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
    """this zone corresponds to a cell of the grid located
as far to the east as possible. This cell can be chosen randomly among the eastern
cells. The implementation of this zone can be done either by programming a new
object agent (without behavior) or by using a radioactivated agent with a
particular radioactivity value (this value will allow the robot agents to identify this
cell as being the waste disposal zone)."""
    def __init__(self, model):
        super().__init__(model)
        self.radioactivity_level = -1  # A distinct value to identify waste disposal zones
