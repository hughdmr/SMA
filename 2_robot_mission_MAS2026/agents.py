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
            "current_position": self.pos,
            "target": None,
            "action_history": [],
            "percept_history": [],
            "waste_here": None,
            "on_disposal": False,
            "waste_on_board": None,
            "zone_start_x": self.zone * self.model.grid.width // self.model.number_zones - 1,
            "zone_end_x": (self.zone + 1) * self.model.grid.width // self.model.number_zones -1,
            "peer_same_color_with_waste_nearby": False,
            "peer_same_color_min_id": None,
        }
        self.action_list = ["move_up", "move_down", "move_left", "move_right", "pick_up"] #"transform", "drop"]

    def update(self, knowledge, percepts):
        if percepts is None:
            percepts = {}
        knowledge["current_position"] = self.pos

        # looking for waste on the current cell
        knowledge["waste_here"] = None  # réinitialiser avant de chercher
        current_cell = self.model.grid.get_cell_list_contents([self.pos])
        for obj in current_cell:
            if isinstance(obj, wasteAgent):
                knowledge["waste_here"] = obj
                break
        # knowledge["on_disposal"] = any(isinstance(obj, wasteDisposalAgent) for obj in current_cell)

        # definition d'une prochaine target parmi les cases voisines contenant des déchets
        neighbors_with_waste = []
        neighbors = []
        peer_same_color_min_id = None
        if isinstance(percepts, dict):
            for cell_pos, objects in percepts.items():
                # print(percepts)
                # print(f"Checking neighbor {cell_pos} with objects {objects}")
                if cell_pos[0] < 0 or cell_pos[0] > knowledge["zone_end_x"] or cell_pos[1] < 0 or cell_pos[1] >= self.model.grid.height:
                    continue  # ignore les cases en dehors de la zone de l'agent
                #on s'assure que les dechets sont de la bonne couleur
                if any(
                    isinstance(obj, wasteAgent) and obj.waste_type == self.color
                    for obj in objects
                ):
                    neighbors_with_waste.append(cell_pos)

                # Coordination locale: si deux robots de meme couleur portent un dechet,
                # le robot avec l'ID le plus grand deposera son dechet.
                for obj in objects:
                    if (
                        isinstance(obj, robotAgent)
                        and obj is not self
                        and obj.color == self.color
                        and obj.knowledge.get("waste_on_board") is not None
                    ):
                        if peer_same_color_min_id is None:
                            peer_same_color_min_id = obj.unique_id
                        else:
                            peer_same_color_min_id = min(peer_same_color_min_id, obj.unique_id)

                neighbors.append(cell_pos)  # on ajoute toutes les cases voisines à la liste des neighbors pour pouvoir choisir une target aléatoire parmi elles si aucune ne contient de déchet

        knowledge["peer_same_color_with_waste_nearby"] = peer_same_color_min_id is not None
        knowledge["peer_same_color_min_id"] = peer_same_color_min_id

        print(f"Agent {self.unique_id} percepts neighbors: {percepts}")
        print(f"neighbors_with_waste: of {self.pos}", neighbors_with_waste)

        if neighbors_with_waste:
            # print(f"Agent {self.unique_id} sees waste at: {neighbors_with_waste}")
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
        colors = ["green", "yellow", "red"]

        ## ROUGE : D'abord on implémente le comportement du robot rouge
        if self.color == "red":
            # Si il a déjà un déchet, on le dirige vers la zone de dépôt et on drop dès qu'on y est
            if knowledge["waste_on_board"]:
                # Recherche manuelle de la position du wasteDisposalAgent
                disposal_pos = None
                for cell_content, (x_cell, y_cell) in self.model.grid.coord_iter():
                    for obj in cell_content:
                        if isinstance(obj, wasteDisposalAgent) and getattr(obj, "radioactivity_level", None) == -1:
                            disposal_pos = (x_cell, y_cell)
                            break
                    if disposal_pos is not None:
                        break
                knowledge["target"] = disposal_pos
                print(f"Agent {self.unique_id} is red and has waste on board, setting target to waste disposal zone at {knowledge['target']}")
                if knowledge["target"] is not None:
                    if x < knowledge["target"][0]:
                        return "move_right"
                    if y < knowledge["target"][1]:
                        return "move_up"
                    else:
                        return "drop" # TO DO in model
            else: # si il n'a pas de déchet, soit il en pick up un
                if knowledge["waste_here"] and knowledge["waste_here"].waste_type == "red":
                    return "pick_up" # TO DO VIZ
            # dernière option, il se déplace pour explorer la zone (cf fin)
        ## VERT ET JAUNE : comportement similaire
        else:
            if knowledge["waste_on_board"]:
                if knowledge["waste_on_board"].waste_type == self.color : # Déchet pas encore transformé car de la même couleur
                    if knowledge["waste_here"] and knowledge["waste_here"].waste_type == self.color: # Déchet à transformer de la bonne couleur sur la case
                        return "transform" # transformation supposée immédiate
                    if (
                        knowledge.get("peer_same_color_with_waste_nearby")
                        and knowledge.get("peer_same_color_min_id") is not None
                        and self.unique_id > knowledge["peer_same_color_min_id"]
                    ):
                        return "drop"
                else : # Déchet déjà transformé donc à déposer dans la colonne de dépôt
                    knowledge["target"] = (knowledge["zone_end_x"], y)
                    if x < knowledge["target"][0]:
                        return "move_right"
                    else:
                        return "drop"
            else: 
                if knowledge["waste_here"] and knowledge["waste_here"].waste_type == self.color: # Déchet de la bonne couleur à ramasser
                    return "pick_up" # TO DO VIZ
                # dernière option, il se déplace pour explorer la zone (cf fin)
        
        # TO DO transform en 2 étapes (actuellement immédiat pour simplifier)
        # et donc TO DO drop (actuellement immédiat pour simplifier)
        # TO DO : clean le code (pick up)
        
        ## DERNIERE OPTION POUR TOUS LES ROBOTS : EXPLORER LA ZONE OU ALLER VERS LA COLONNE DE DEPOT DE LA ZONE PRECEDENTE
        # 1 fois sur 3 et pour 1 agent sur 2, je souhaite fixer comme target la colonne de dépôt de la zone précédente pour favoriser la circulation des déchets entre les zones, sinon je choisis une target aléatoire parmi les voisins (déjà fait dans update)
        if self.unique_id % 2 == 0 and self.color in ["yellow", "red"] and self.knowledge.get("waste_on_board") is None and random.random() < 0.33:
            print(f"Agent {self.unique_id} is {'yellow' if self.color == 'yellow' else 'red'} and has no waste on board, randomly deciding to target previous zone's disposal column at {knowledge['target']}")
            knowledge["target"] = (knowledge["zone_end_x"] - self.model.grid.width // self.model.number_zones, random.randint(0, self.model.grid.height - 1))
        if knowledge["target"] is None: # aucun target, on fait un mouvement aléatoire pour explorer la zone
            return self.random.choice(["move_up", "move_down", "move_left", "move_right"])
        tx, ty = knowledge["target"]
        # Définition des mouvements pour se rapprocher de la target
        if tx > x and x < knowledge["zone_end_x"]:
            return "move_right"
        if tx < x and x > knowledge["zone_start_x"]:
            return "move_left"
        if ty > y and y < self.model.grid.height - 1:
            return "move_up"
        if ty < y and y > 0:
            return "move_down"
        return "move_left" if x > knowledge["zone_start_x"] else "move_right"
    
    def step_agent(self, percepts=None):
        if percepts is None:
            percepts = self.model.build_percepts(self)

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
