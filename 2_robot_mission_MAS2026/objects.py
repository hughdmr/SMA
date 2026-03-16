#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

from mesa import Agent

class wasteAgent(Agent):
    """Agent representing a piece of waste in the environment. The 'zone' attribute indicates in which zone the waste is located (0, 1, or 2)."""
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone
    
class radioactivityAgent(Agent):
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone

class wasteDisposalAgent(Agent):
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone

