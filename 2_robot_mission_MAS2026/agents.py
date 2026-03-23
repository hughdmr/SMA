#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

import random
from mesa import Agent

from objects import wasteAgent, wasteDisposalAgent

class robotAgent(Agent):
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone
        self.last_percepts = None
        """The attribute self.knowledge should represent the beliefs and knowledge of the
agent. The representation of these is entirely up to you! (as a bare minimum, you
might consider storing the percepts and actions at each time step)."""
        self.knowledge = {
            "current_position": None,
            "target": None,
            "action_history": [],
            "percept_history": [],
            "waste_here": False,
            "on_disposal": False,
            "waste_on_board": None,
            # "waste_transformed": False,
            "zone_start_x": 0,
            "zone_end_x": 0,
            "grid_height": 0,
        }
        self.action_list = ["move_up", "move_down", "move_left", "move_right", "pick_up"] #"transform", "drop"]

    def update(self, knowledge, percepts):
        if percepts is None:
            percepts = {}

        zone_width = self.model.grid.width // self.model.number_zones
        zone_end_x = (self.zone + 1) * zone_width - 1

        knowledge["current_position"] = self.pos
        knowledge["zone_start_x"] = 0
        knowledge["zone_end_x"] = zone_end_x
        knowledge["grid_height"] = self.model.grid.height

        current_cell = self.model.grid.get_cell_list_contents([self.pos])
        knowledge["waste_here"] = any(isinstance(obj, wasteAgent) for obj in current_cell)
        # knowledge["on_disposal"] = any(isinstance(obj, wasteDisposalAgent) for obj in current_cell)

        # definition d'une prochaine target parmi les cases voisines contenant des déchets
        neighbors_with_waste = []
        neighbors = []
        if isinstance(percepts, dict):
            for cell_pos, objects in percepts.items():
                print(percepts)
                print(f"Checking neighbor {cell_pos} with objects {objects}")
                if cell_pos[0] < 0 or cell_pos[0] > zone_end_x or cell_pos[1] < 0 or cell_pos[1] >= self.model.grid.height:
                    continue  # ignore les cases en dehors de la zone de l'agent
                if any(isinstance(obj, wasteAgent) for obj in objects):
                    neighbors_with_waste.append(cell_pos)
                neighbors.append(cell_pos)  # on ajoute toutes les cases voisines à la liste des neighbors pour pouvoir choisir une target aléatoire parmi elles si aucune ne contient de déchet

        print(f"Agent {self.unique_id} percepts neighbors: {percepts}")
        print(f"neighbors_with_waste: of {self.pos}", neighbors_with_waste)

        if neighbors_with_waste:
            print(f"Agent {self.unique_id} sees waste at: {neighbors_with_waste}")
            knowledge["target"] = random.choice(neighbors_with_waste)  # target la première case avec du déchet trouvée
        else:
            knowledge["target"] = random.choice(neighbors)
        
        # else: # sinon, on se fixe comme target la zone de dépot
        #     knowledge["target"] = (zone_end_x, self.pos[1])
        knowledge["percept_history"].append(percepts)

    def deliberate(self, knowledge):
        """the “deliberate” corresponds to the “reasoning” step of the agent. It takes as
input the “knowledge” (current position, the target, …) that has the agent at each
step and returns one or several actions (e.g. moving, collecting, etc.)

The function deliberate() is not allowed to access any variable outside its
argument. The variable action describes the action chosen by the agent, among a limited list,
such as move to an adjacent tile, pick up, transform, put down, … Its
implementation (e.g. as objects, strings, dictionaries, …) is left to you."""
        x, y = knowledge["current_position"]

        if self.color == "green":
            if knowledge["waste_on_board"]:
                if knowledge["waste_on_board"].waste_type == "green" : # Déchet porté de la bonne couleur --> cher
                    if knowledge["waste_here"]:
                        return "transform"
                else : # Déchet déjà transformé
                    knowledge["target"] = (knowledge["zone_end_x"], y)
                    if x < knowledge["zone_end_x"]:
                        return "move_right"
            else :
                if knowledge["waste_here"]:
                    return "pick_up" # TO DO VIZ
        
        # TO DO yellow and red

        # TO DO transform
            
        target = knowledge["target"]
        if target is None:
            # aucun target, on fait un mouvement aléatoire pour explorer la zone
            return self.random.choice(["move_up", "move_down", "move_left", "move_right"])
        tx, ty = target

        # Définition des mouvements pour se rapprocher de la target
        if tx > x and x < knowledge["zone_end_x"]:
            return "move_right"
        if tx < x and x > knowledge["zone_start_x"]:
            return "move_left"
        if ty > y and y < knowledge["grid_height"] - 1:
            return "move_up"
        if ty < y and y > 0:
            return "move_down"

        return "move_left" if x > knowledge["zone_start_x"] else "move_right"
    
    def step_agent(self, percepts=None):
        if percepts is None:
            percepts = self.model.build_percepts(self.pos)

        self.update(self.knowledge, percepts)
        print(f"Agent {self.unique_id} at {self.pos} with target {self.knowledge['target']}")
        action = self.deliberate(self.knowledge)
        print(f"Agent {self.unique_id} decided to: {action}")
        self.knowledge["action_history"].append(action)
        self.last_percepts = self.model.do(self, action)

    def step(self):
        self.step_agent(self.last_percepts)

class greenAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=0)
        self.color = "green"

class yellowAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=1)
        self.color = "yellow"

class redAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=2) 
        self.color = "red"