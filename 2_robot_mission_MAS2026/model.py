#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

from mesa import Model
from mesa.space import MultiGrid
from agents import greenAgent, yellowAgent, redAgent
from objects import wasteAgent, radioactivityAgent, wasteDisposalAgent

class RobotMission(Model):

    def __init__(self, N_agents=10, N_waste=10, z=10, height=10, seed=None):
        super().__init__(seed=seed)
        self.grid = MultiGrid(3*z, height, torus=False)
        self.number_zones = 3
        self.zone_radioactivity = {"1": (0,0.33), "2": (0.33,0.66), "3": (0.66,1)}

        #place agents in their respective zones
        agent_classes = [greenAgent, yellowAgent, redAgent]
        for i in range(self.number_zones):
            for _ in range(N_agents):
                agent = agent_classes[i](self)
                x = self.random.randrange(i*z, (i+1)*z)
                y = self.random.randrange(self.grid.height)
                self.grid.place_agent(agent, (x, y))

        #place radioactivity according to the zones
        for i in range(self.number_zones):
            for x in range(i*z, (i+1)*z):
                for y in range(self.grid.height):
                    radioactivity = radioactivityAgent(self, i)
                    self.grid.place_agent(radioactivity, (x, y))

        #place waste
        for i in range(self.number_zones):
            for _ in range(N_waste):
                x = self.random.randrange(i*z, (i+1)*z)
                y = self.random.randrange(self.grid.height)
                waste = wasteAgent(self, i)
                self.grid.place_agent(waste, (x, y))
        
        #place waste disposal zones as last column of each zone
        for i in range(self.number_zones):
            for y in range(self.grid.height):
                waste_disposal = wasteDisposalAgent(self, i)
                self.grid.place_agent(waste_disposal, ((i+1)*z-1, y))
    
    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step_agent")

    def _build_percepts(self, pos):
        percepts = {}
        for neighbor in self.grid.get_neighborhood(pos, moore=True, include_center=False):
            percepts[neighbor] = self.grid.get_cell_list_contents([neighbor])
        return percepts

    def do(self, agent, action):
        """the “do” allows the agent to inform the environment of its actions (the results of
the deliberation process) and, thus, the environment to apply the consequences
of these actions. For instance, when an agent collects waste, the latter must no
longer exist in the grid. Removing the waste is the responsibility of the
environment.

The variable percepts, returned by the method Model.do, should contain information 
        about the adjacent tiles and their content – use a dictionary!
        
        Moreover, the model is in charge of the execution of actions, with a method called do.
This method should have as arguments the agent performing the action and the description of the action. It should check whether the action is feasible (each action has
requirements, and even if the agent believes its action is feasible, it might be mistaken),
then perform the changes entailed by the action."""

        if not hasattr(agent, "carried_waste"):
            agent.carried_waste = None

        if action in ["move_up", "move_down", "move_left", "move_right"]:
            x, y = agent.pos
            if action == "move_up":
                new_pos = (x, y + 1)
            elif action == "move_down":
                new_pos = (x, y - 1)
            elif action == "move_left":
                new_pos = (x - 1, y)
            else:  # move_right
                new_pos = (x + 1, y)

            if self.grid.out_of_bounds(new_pos):
                return {"error": "Move out of bounds", "percepts": self._build_percepts(agent.pos)}

            self.grid.move_agent(agent, new_pos)
            return self._build_percepts(agent.pos)

        if action == "pick_up":
            if getattr(agent, "carrying_waste", False):
                return {"error": "Agent already carrying waste", "percepts": self._build_percepts(agent.pos)}

            cell_objects = self.grid.get_cell_list_contents([agent.pos])
            wastes = [obj for obj in cell_objects if isinstance(obj, wasteAgent)]
            if not wastes:
                return {"error": "No waste to pick up", "percepts": self._build_percepts(agent.pos)}

            waste = wastes[0]
            waste.collect()
            self.grid.remove_agent(waste)
            agent.carrying_waste = True
            agent.carried_waste = waste
            return self._build_percepts(agent.pos)

        if action == "transform":
            waste = getattr(agent, "carried_waste", None)
            if not getattr(agent, "carrying_waste", False) or waste is None:
                return {"error": "No carried waste to transform", "percepts": self._build_percepts(agent.pos)}

            waste.transform()
            return self._build_percepts(agent.pos)

        if action == "drop":
            waste = getattr(agent, "carried_waste", None)
            if not getattr(agent, "carrying_waste", False) or waste is None:
                return {"error": "No carried waste to drop", "percepts": self._build_percepts(agent.pos)}

            cell_objects = self.grid.get_cell_list_contents([agent.pos])
            disposals = [obj for obj in cell_objects if isinstance(obj, wasteDisposalAgent)]
            if not disposals:
                return {"error": "Not on a disposal cell", "percepts": self._build_percepts(agent.pos)}

            disposal = disposals[0]
            if not disposal.accepts(waste):
                return {"error": "Waste must be transformed before drop", "percepts": self._build_percepts(agent.pos)}

            agent.carrying_waste = False
            agent.carried_waste = None
            return self._build_percepts(agent.pos)

        return {"error": "Unknown action", "percepts": self._build_percepts(agent.pos)}
    