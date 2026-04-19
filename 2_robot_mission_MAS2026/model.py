#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

import json
import os

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import MultiGrid
from agents import greenAgent, yellowAgent, redAgent
from communication.message.MessageService import MessageService
from objects import wasteAgent, radioactivityAgent, wasteDisposalAgent

class RobotMission(Model):

    def __init__(self, N_agents=10, want_no_waste_at_end=False, N_waste=10, z=10, height=10, communication_enabled=None, seed=None):
        super().__init__(seed=seed)

        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        config_data = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as config_file:
                config_data = json.load(config_file)

        if communication_enabled is None:
            communication_value = config_data.get("communication", False)
            if isinstance(communication_value, str):
                communication_enabled = communication_value.strip().lower() == "true"
            else:
                communication_enabled = bool(communication_value)
        self.communication_enabled = communication_enabled

        if MessageService.get_instance() is not None:
            MessageService._MessageService__instance = None
        MessageService(self, instant_delivery=True)

        # Si want_no_waste_at_end, arrondir aux multiples appropriés
        if want_no_waste_at_end:
            N_waste_green = (N_waste // 4) * 4
            N_waste_yellow = (N_waste // 2) * 2
            N_waste_red = N_waste - N_waste_green - N_waste_yellow
        else:
            N_waste_green = N_waste
            N_waste_yellow = N_waste
            N_waste_red = N_waste

        self.grid = MultiGrid(3*z, height, torus=False)
        self.number_zones = 3
        self.zone_radioactivity = {"1": (0,0.33), "2": (0.33,0.66), "3": (0.66,1)}
        self.count_collected_red_waste = 0
        self.waste_counts = {"green": N_waste_green, "yellow": N_waste_yellow, "red": N_waste_red}
        self.initial_waste_counts = {"green": N_waste_green, "yellow": N_waste_yellow, "red": N_waste_red}
        # Number of visits per cell by robots, indexed as [y][x].
        self.robot_visit_counts = [
            [0 for _ in range(self.grid.width)]
            for _ in range(self.grid.height)
        ]

        #place agents in their respective zones
        agent_classes = [greenAgent, yellowAgent, redAgent]
        for i in range(self.number_zones):
            for _ in range(N_agents):
                agent = agent_classes[i](self)
                x = self.random.randrange(i*z, (i+1)*z)
                y = self.random.randrange(self.grid.height)
                self.grid.place_agent(agent, (x, y))
                self.robot_visit_counts[y][x] += 1
                print(f"Placing {agent.__class__.__name__} with id {agent.unique_id} at ({x}, {y}) in zone {i+1}")
        
        #place radioactivity according to the zones
        for i in range(self.number_zones):
            for x in range(i*z, (i+1)*z):
                for y in range(self.grid.height):
                    radioactivity = radioactivityAgent(self, i)
                    self.grid.place_agent(radioactivity, (x, y))

        #place waste
        for i in range(self.number_zones):
            for _ in range(N_waste):
                x2 = self.random.randrange(i*z, (i+1)*z)
                y2 = self.random.randrange(self.grid.height)
                waste = wasteAgent(self, i)
                self.grid.place_agent(waste, (x2, y2))

        #place waste disposal zone in a cell in the easternmost part of the grid, randomly among the eastern cells
        x = 3*z - 1
        y = self.random.randrange(self.grid.height)
        waste_disposal = wasteDisposalAgent(self)
        waste_disposal.pos = (x, y)  # set the position attribute for visualization purposes
        # print(f"Placing waste disposal agent at ({x}, {y})")
        self.grid.place_agent(waste_disposal, (x, y))

        self.datacollector = DataCollector(
            model_reporters={
                "waste_green": lambda m: m.count_waste_by_type("green"),
                "waste_yellow": lambda m: m.count_waste_by_type("yellow"),
                "waste_red": lambda m: m.count_waste_by_type("red"),
                "waste_disposed": lambda m: m.count_collected_red_waste,
            }
        )
        self.datacollector.collect(self)

    def count_waste_by_type(self, waste_type):
        return self.waste_counts.get(waste_type, 0)
    
    def build_percepts(self, agent): # on veut le voisin du dessus, dessous, gauche, droite
        percepts = {}
        neighbors = self.grid.get_neighborhood(agent.pos, moore=False, include_center=False)
        # remove diagonals from neighbors
        neighbors = [n for n in neighbors if n[0] == agent.pos[0] or n[1] == agent.pos[1]]
        # print(f"Neighbors of {agent.unique_id} at {agent.pos}: {neighbors}")
        for neighbor in neighbors:
            percepts[neighbor] = self.grid.get_cell_list_contents([neighbor])
        return percepts
    
    def step(self):
        """Advance the model by one step."""
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)

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

        # if not hasattr(agent, "carried_waste"):
        #     agent.carried_waste = None

        if action == "wait":
            return self.build_percepts(agent)

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
                return {"error": "Move out of bounds", "percepts": self.build_percepts(agent)}

            self.grid.move_agent(agent, new_pos)
            self.robot_visit_counts[new_pos[1]][new_pos[0]] += 1
            return self.build_percepts(agent)

        if action == "pick_up":
            cell_objects = self.grid.get_cell_list_contents([agent.pos])
            wastes_of_color = [obj for obj in cell_objects if isinstance(obj, wasteAgent) and obj.waste_type == agent.color]
            if not wastes_of_color:
                # print(f"Agent {agent.unique_id} attempted to pick up waste at {agent.pos} but found none of the right color.")
                return {"error": "No waste to pick up", "percepts": self.build_percepts(agent)}
            waste_to_pick_up = wastes_of_color[0]
            # waste_to_pick_up.collect()
            self.grid.remove_agent(waste_to_pick_up) # TO DO ADD ICON VIZ FOR WASTE PICKUP
            agent.knowledge["waste_on_board"] = waste_to_pick_up
            return self.build_percepts(agent)

        if action == "transform":
            carried_waste = agent.knowledge.get("waste_on_board")
            if carried_waste is None or carried_waste.waste_type != agent.color:
                return {"error": "No carried waste to transform", "percepts": self.build_percepts(agent)}

            cell_objects = self.grid.get_cell_list_contents([agent.pos])
            wastes_of_color = [obj for obj in cell_objects if isinstance(obj, wasteAgent) and obj.waste_type == agent.color]
            if not wastes_of_color:
                # print(f"Agent {agent.unique_id} attempted to transform waste at {agent.pos} but found none of the right color.")
                # print(f"Cell objects: {cell_objects}")
                return {"error": "No waste to transform", "percepts": self.build_percepts(agent)}
            waste_to_transform = wastes_of_color[0]
            self.grid.remove_agent(waste_to_transform)
            # Crée un déchet de la couleur suivante (zone + 1)
            new_waste = wasteAgent(self, agent.zone + 1)
            agent.knowledge["waste_on_board"] = new_waste
            self.waste_counts[agent.color] -= 2
            self.waste_counts[new_waste.waste_type] += 1
            print(f"Agent {agent.unique_id} transformed waste to {new_waste.waste_type}")
            return self.build_percepts(agent)

        if action == "drop":
            waste = agent.knowledge.get("waste_on_board", None)
            if waste is None:
                return {"error": "No carried waste to drop", "percepts": self.build_percepts(agent)}
            if agent.color != "red":
                # Placer le déchet à la fin de la zone pour que le robot suivant puisse le ramasser
                drop_pos = (agent.pos[0], agent.pos[1])
                self.grid.place_agent(waste, drop_pos)
                # print(f"Agent {agent.unique_id} dropped waste at {drop_pos} for next zone")
            else:
                self.count_collected_red_waste += 1
                self.waste_counts["red"] -= 1
                print(f"Agent {agent.unique_id} disposed waste. Total disposed: {self.count_collected_red_waste}")
            agent.knowledge["waste_on_board"] = None
            agent.target = None
            return self.build_percepts(agent)

        return {"error": "Unknown action", "percepts": self.build_percepts(agent)}
    
