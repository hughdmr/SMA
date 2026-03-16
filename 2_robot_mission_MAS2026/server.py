#2 16/03/2026 Hugues d'Hardemare Louis Vauterin
from mesa import agent
from mesa.visualization import SolaraViz, make_space_component 
from model import RobotMission
from agents import greenAgent, yellowAgent, redAgent
from objects import wasteAgent, radioactivityAgent, wasteDisposalAgent

def agent_portrayal(agent):
    if isinstance(agent, greenAgent):
        return {"size": 50, "color": "green", "marker": "o"}
    elif isinstance(agent, yellowAgent):
        return {"size": 50, "color": "orange", "marker": "o"} # orange is easier to see than yellow on light backgrounds
    elif isinstance(agent, redAgent):
        return {"size": 50, "color": "red", "marker": "o"}
    elif isinstance(agent, wasteAgent):
        return {"size": 20, "color": "black", "marker": "s"}
    elif isinstance(agent, wasteDisposalAgent):
        return {"size": 60, "color": "blue", "marker": "s"}
    elif isinstance(agent, radioactivityAgent):
        # Background radioactivity, distinct light colors and smaller markers
        color_map = {0: "#ccffcc", 1: "#ffffcc", 2: "#ffcccc"}
        return {"size": 15, "color": color_map.get(agent.zone, "grey"), "marker": "x"}
    
    return {"size": 10, "color": "grey"}

model_params = {
    "N_agents": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of agents",
        "min": 1,
        "max": 50,
        "step": 1,
    },
    "N_waste": {
        "type": "SliderInt",
        "value": 10,
        "label": "Amount of waste per zone",
        "min": 1,
        "max": 50,
        "step": 1,
    },
    "z": {
        "type": "SliderInt",
        "value": 10,
        "label": "Zone width",
        "min": 5,
        "max": 20,
        "step": 1,
    },
    "height": {
        "type": "SliderInt",
        "value": 10,
        "label": "Grid height",
        "min": 5,
        "max": 20,
        "step": 1,
    },
}

initial_model = RobotMission(N_agents=10, N_waste=10, z=10, height=10)

page = SolaraViz(
    initial_model,
    components=[make_space_component(agent_portrayal)],
    model_params=model_params,
    name="Robot Mission"
)

