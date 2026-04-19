#2 16/03/2026 Hugues d'Hardemare Louis Vauterin

import random
from communication.agent.CommunicatingAgent import CommunicatingAgent
from communication.message.Message import Message
from communication.message.MessagePerformative import MessagePerformative

from objects import wasteAgent, wasteDisposalAgent

class robotAgent(CommunicatingAgent):
    def __init__(self, model, zone):
        super().__init__(model, name=f"robot-{zone}-pending")
        self._CommunicatingAgent__name = f"robot-{self.unique_id}"
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
            "adjacent_carrier_id": None,
            "adjacent_carrier_pos": None,
            "rendezvous_target_id": None,
            "rendezvous_target_pos": None,
        }
        self.action_list = ["move_up", "move_down", "move_left", "move_right", "pick_up"] #"transform", "drop"]

    def communication_name(self):
        return self.get_name()

    def process_communication(self):
        if not getattr(self.model, "communication_enabled", False):
            self.knowledge["rendezvous_target_id"] = None
            self.knowledge["rendezvous_target_pos"] = None
            return

        # Broadcast only if the robot is carrying a waste of its own color.
        carried = self.knowledge.get("waste_on_board")
        if carried is not None and carried.waste_type == self.color:
            content = {
                "type": "have_waste",
                "color": self.color,
                "position": self.pos,
                "agent_id": self.unique_id,
            }
            for other in self.model.agents:
                if (
                    isinstance(other, robotAgent)
                    and other is not self
                    and other.color == self.color
                ):
                    self.send_message(
                        Message(
                            self.communication_name(),
                            other.communication_name(),
                            MessagePerformative.INFORM_REF,
                            content,
                        )
                    )

        messages = self.get_new_messages()
        candidates = []
        for msg in messages:
            if msg.get_performative() != MessagePerformative.INFORM_REF:
                continue
            payload = msg.get_content()
            if not isinstance(payload, dict):
                continue
            if payload.get("type") != "have_waste":
                continue
            if payload.get("color") != self.color:
                continue

            sender_id = payload.get("agent_id")
            sender_pos = payload.get("position")
            if sender_id is None or sender_pos is None:
                continue
            candidates.append((sender_id, sender_pos))

        if not candidates:
            self.knowledge["rendezvous_target_id"] = None
            self.knowledge["rendezvous_target_pos"] = None
            return

        target_id, target_pos = min(candidates, key=lambda item: item[0])
        self.knowledge["rendezvous_target_id"] = target_id
        self.knowledge["rendezvous_target_pos"] = target_pos

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
        adjacent_carrier_id = None
        adjacent_carrier_pos = None
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
                        if obj.knowledge["waste_on_board"].waste_type == self.color:
                            if adjacent_carrier_id is None or obj.unique_id < adjacent_carrier_id:
                                adjacent_carrier_id = obj.unique_id
                                adjacent_carrier_pos = cell_pos
                        if peer_same_color_min_id is None:
                            peer_same_color_min_id = obj.unique_id
                        else:
                            peer_same_color_min_id = min(peer_same_color_min_id, obj.unique_id)

                neighbors.append(cell_pos)  # on ajoute toutes les cases voisines à la liste des neighbors pour pouvoir choisir une target aléatoire parmi elles si aucune ne contient de déchet

        knowledge["peer_same_color_with_waste_nearby"] = peer_same_color_min_id is not None
        knowledge["peer_same_color_min_id"] = peer_same_color_min_id
        knowledge["adjacent_carrier_id"] = adjacent_carrier_id
        knowledge["adjacent_carrier_pos"] = adjacent_carrier_pos

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

        # Fast local exchange: if two same-color carriers are adjacent,
        # force immediate coordination instead of exploration.
        if (
            knowledge.get("waste_on_board") is not None
            and knowledge["waste_on_board"].waste_type == self.color
            and knowledge.get("adjacent_carrier_id") is not None
            and knowledge.get("adjacent_carrier_pos") is not None
        ):
            neighbor_id = knowledge["adjacent_carrier_id"]
            nx, ny = knowledge["adjacent_carrier_pos"]
            if self.unique_id > neighbor_id:
                return "drop"
            if nx > x:
                return "move_right"
            if nx < x:
                return "move_left"
            if ny > y:
                return "move_up"
            if ny < y:
                return "move_down"
            if knowledge.get("waste_here") and knowledge["waste_here"].waste_type == self.color:
                return "transform"
            return "wait"

        # If communication is enabled and two same-color robots carry waste,
        # we force a rendezvous: smallest ID waits, others move to it.
        if (
            self.model.communication_enabled
            and knowledge.get("waste_on_board") is not None
            and knowledge["waste_on_board"].waste_type == self.color
            and knowledge.get("rendezvous_target_id") is not None
            and knowledge.get("rendezvous_target_pos") is not None
        ):
            target_id = knowledge["rendezvous_target_id"]
            tx, ty = knowledge["rendezvous_target_pos"]
            # At rendezvous, one robot drops and the other transforms,
            # so agents do not get stuck waiting while carrying waste.
            if x == tx and y == ty:
                if self.unique_id > target_id:
                    return "drop"
                if knowledge.get("waste_here") and knowledge["waste_here"].waste_type == self.color:
                    return "transform"
                return "wait"
            if tx > x and x < knowledge["zone_end_x"]:
                return "move_right"
            if tx < x and x > knowledge["zone_start_x"]:
                return "move_left"
            if ty > y and y < self.model.grid.height - 1:
                return "move_up"
            if ty < y and y > 0:
                return "move_down"
            return "wait"

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

        self.process_communication()
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
