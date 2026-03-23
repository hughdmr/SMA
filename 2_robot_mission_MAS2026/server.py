#2 16/03/2026 Hugues d'Hardemare Louis Vauterin
from mesa import agent
from mesa.visualization import SolaraViz, make_space_component 
from model import RobotMission
from agents import greenAgent, yellowAgent, redAgent
from objects import wasteAgent, radioactivityAgent, wasteDisposalAgent
import matplotlib.patches as patches

def draw_zones(ax):
    # This post-process function draws uniform continuous background zones 
    # over the entire grid
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    width = x_max - x_min
    z = width / 3
    
    # Add colored rectangle patches with lower zorder so they sit behind agents
    rect_green = patches.Rectangle((x_min, y_min), z, y_max - y_min, facecolor='green', alpha=0.2, zorder=-1)
    rect_yellow = patches.Rectangle((x_min + z, y_min), z, y_max - y_min, facecolor='yellow', alpha=0.2, zorder=-1)
    rect_red = patches.Rectangle((x_min + 2 * z, y_min), z, y_max - y_min, facecolor='red', alpha=0.2, zorder=-1)
    
    ax.add_patch(rect_green)
    ax.add_patch(rect_yellow)
    ax.add_patch(rect_red)
    
    # Hide the axes ticks and labels for a cleaner, game-like visualization
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    
    # Make the aspect ratio equal so cells are squares
    ax.set_aspect('equal')
    
    # Scale the figure dynamically so it properly wraps the grid without huge whitespace margins.
    # This ensures the browser displays the cells nicely and as large as the screen allows.
    height_grid = y_max - y_min
    ax.figure.set_size_inches(width * 0.5, height_grid * 0.5)
    
    # Put a title on it to make it look nicer
    ax.set_title("Robot Waste Cleanup", fontsize=14, pad=10)

def agent_portrayal(agent):
    if isinstance(agent, greenAgent):
        return {"size": 400, "color": "green", "marker": "o"}
    elif isinstance(agent, yellowAgent):
        return {"size": 400, "color": "orange", "marker": "o"}
    elif isinstance(agent, redAgent):
        return {"size": 400, "color": "red", "marker": "o"}
    elif isinstance(agent, wasteAgent):
        waste_colors = {"green": "darkgreen", "yellow": "darkgoldenrod", "red": "darkred"}
        return {"size": 200, "color": waste_colors.get(agent.waste_type, "black"), "marker": "s"}
    elif isinstance(agent, wasteDisposalAgent):
        return {"size": 1200, "color": "black", "marker": "x", "alpha": 0.3, "linewidths": 1}
    elif isinstance(agent, radioactivityAgent):
        return {"size": 0, "alpha": 0.0, "color": "none"}
    
    # TO DO highlight last column of each zone 
    
    return {"size": 0, "alpha": 0}

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

initial_model = RobotMission(N_agents=2, N_waste=1, z=10, height=10)

page = SolaraViz(
    initial_model,
    components=[make_space_component(agent_portrayal, post_process=draw_zones)],
    model_params=model_params,
    name="Robot Mission"
)

