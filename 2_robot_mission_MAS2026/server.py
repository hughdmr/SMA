#2 16/03/2026 Hugues d'Hardemare Louis Vauterin
from mesa import agent
from mesa.visualization import SolaraViz, make_space_component 
from model import RobotMission
from agents import robotAgent, greenAgent, yellowAgent, redAgent
from objects import wasteAgent, radioactivityAgent, wasteDisposalAgent
import matplotlib.patches as patches


DISPOSAL_POS = None
DISPOSAL_COUNT = 0

def draw_zones(ax):
    global DISPOSAL_POS, DISPOSAL_COUNT

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

    # Simple disposal counter displayed on top of the disposal square.
    if DISPOSAL_POS is not None:
        ax.text(
            DISPOSAL_POS[0],
            DISPOSAL_POS[1],
            str(DISPOSAL_COUNT),
            ha="center",
            va="center",
            fontsize=10,
            color="black",
            fontweight="bold",
            zorder=6,
        )

def agent_portrayal(agent):
    global DISPOSAL_POS, DISPOSAL_COUNT

    waste_colors = {"green": "darkgreen", "yellow": "darkgoldenrod", "red": "darkred"}
    marker = "o"
    if isinstance(agent, robotAgent):
        if agent.knowledge.get("waste_on_board") is not None:
            if agent.knowledge.get("waste_on_board").waste_type == agent.color:
                marker = "$⊙$"
            else:
                marker = "$⚇$"

        if isinstance(agent, greenAgent):
            return {"size": 400, "color": "green", "marker": marker}
        elif isinstance(agent, yellowAgent):
            return {"size": 400, "color": "orange", "marker": marker}
        elif isinstance(agent, redAgent):
            return {"size": 400, "color": "red", "marker": marker}
    elif isinstance(agent, wasteAgent):
        # Distinct waste colors by zone: dark green, dark goldenrod, and dark red
        return {"size": 200, "color": waste_colors.get(agent.waste_type, "black"), "marker": "s"}
    elif isinstance(agent, wasteDisposalAgent):
        DISPOSAL_POS = agent.pos
        DISPOSAL_COUNT = agent.model.count_collected_red_waste
        return {
            "size": 620,
            "color": "lightgray",
            "marker": "s",
            "alpha": 1.0,
            "zorder": 1,
        }
    elif isinstance(agent, radioactivityAgent):
        return {"size": 0, "alpha": 0.0, "color": "none"}
    
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

initial_model = RobotMission(N_agents=10, N_waste=10, z=10, height=10)

page = SolaraViz(
    initial_model,
    components=[make_space_component(agent_portrayal, post_process=draw_zones)],
    model_params=model_params,
    name="Robot Mission"
)
