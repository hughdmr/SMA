#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

from mesa import Model
from mesa.space import MultiGrid
from agents import greenAgent, yellowAgent, redAgent
from objects import wasteAgent, radioactivityAgent, wasteDisposalAgent

class RobotMission(Model):

    def __init__(self, N_agents=10, N_waste=10, z=10, height=10, seed=None):
        super().__init__(seed=seed)
        self.grid = MultiGrid(3*z, height, torus=False)

        #place agents in their respective zones
        agents = [greenAgent(self), yellowAgent(self), redAgent(self)]
        for i in range(3):
            for _ in range(N_agents):
                agent = agents[i]
                x = self.random.randrange(i*z, (i+1)*z)
                y = self.random.randrange(self.grid.height)
                self.grid.place_agent(agent, (x, y))

        #place radioactivity according to the zones
        for i in range(3):
            for x in range(i*z, (i+1)*z):
                for y in range(self.grid.height):
                    radioactivity = radioactivityAgent(self, i)
                    self.grid.place_agent(radioactivity, (x, y))

        #place waste
        for i in range(3):
            for _ in range(N_waste):
                x = self.random.randrange(i*z, (i+1)*z)
                y = self.random.randrange(self.grid.height)
                waste = wasteAgent(self, i)
                self.grid.place_agent(waste, (x, y))
        
        #place waste disposal zones as last column of each zone
        for i in range(3):
            for y in range(self.grid.height):
                waste_disposal = wasteDisposalAgent(self, i)
                self.grid.place_agent(waste_disposal, ((i+1)*z-1, y))
        

    
    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
    