#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

from mesa import Agent

class robotAgent(Agent):
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone
        self.carrying_waste = False

    def step(self):
        # Implement the logic for the robot's behavior here
        pass

class greenAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=0)

class yellowAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=1)

class redAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=2) 