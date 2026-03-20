#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

from mesa import Agent

from objects import wasteAgent, wasteDisposalAgent

class robotAgent(Agent):
    def __init__(self, model, zone):
        super().__init__(model)
        self.zone = zone
        self.carrying_waste = False
        self.carried_waste = None
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
            "carrying_waste": False,
            "waste_transformed": False,
            "zone_start_x": 0,
            "zone_end_x": 0,
            "grid_height": 0,
        }
        self.action_list = ["move_up", "move_down", "move_left", "move_right", "pick_up", "transform", "drop"]

    def update(self, knowledge, percepts):
        if percepts is None:
            percepts = {}

        zone_width = self.model.grid.width // self.model.number_zones
        zone_start_x = self.zone * zone_width
        zone_end_x = (self.zone + 1) * zone_width - 1

        knowledge["current_position"] = self.pos
        knowledge["zone_start_x"] = zone_start_x
        knowledge["zone_end_x"] = zone_end_x
        knowledge["grid_height"] = self.model.grid.height
        knowledge["carrying_waste"] = self.carrying_waste
        knowledge["waste_transformed"] = bool(self.carried_waste and self.carried_waste.is_transformed)

        current_cell = self.model.grid.get_cell_list_contents([self.pos])
        knowledge["waste_here"] = any(isinstance(obj, wasteAgent) for obj in current_cell)
        knowledge["on_disposal"] = any(isinstance(obj, wasteDisposalAgent) for obj in current_cell)

        # definition d'une prochaine target parmi les cases voisines contenant des déchets, ou None si aucune n'en contient
        neighbors_with_waste = []
        if isinstance(percepts, dict):
            for cell_pos, objects in percepts.items():
                if any(isinstance(obj, wasteAgent) for obj in objects):
                    neighbors_with_waste.append(cell_pos)

        if neighbors_with_waste:
            cx, cy = self.pos
            knowledge["target"] = min(
                neighbors_with_waste,
                key=lambda p: abs(p[0] - cx) + abs(p[1] - cy),
            )
        elif knowledge["target"] is not None and knowledge["target"] == self.pos:
            knowledge["target"] = None

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

        if knowledge["carrying_waste"]: # Déchet porté --> transformation ou dépôt
            if not knowledge["waste_transformed"]:
                return "transform"
            if knowledge["on_disposal"]:
                return "drop"
            target = (knowledge["zone_end_x"], y)
        else: # Pas de déchet porté --> collecte ou déplacement vers un déchet
            if knowledge["waste_here"]:
                return "pick_up"
            target = knowledge["target"]

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

    def build_percepts(self, pos):
        percepts = {}
        for neighbor in self.model.grid.get_neighborhood(pos, moore=True, include_center=False):
            percepts[neighbor] = self.model.grid.get_cell_list_contents([neighbor])
        return percepts
    
    def step_agent(self, percepts=None):
        if percepts is None:
            percepts = self._build_percepts(self.pos)

        self.update(self.knowledge, percepts)
        action = self.deliberate(self.knowledge)
        self.knowledge["action_history"].append(action)
        self.last_percepts = self.model.do(self, action)

    def step(self):
        self.step_agent(self.last_percepts)

class greenAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=0)

class yellowAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=1)

class redAgent(robotAgent):
    def __init__(self, model):
        super().__init__(model, zone=2) 