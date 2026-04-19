#2 16/03/2026 Hugues d'Hardemare Louis Vauterin
from mesa import agent
from mesa.visualization import SolaraViz, make_space_component 
from mesa.visualization.utils import update_counter
from model import RobotMission
from agents import robotAgent, greenAgent, yellowAgent, redAgent
from objects import wasteAgent, radioactivityAgent, wasteDisposalAgent
import matplotlib.patches as patches
from matplotlib.figure import Figure
import solara


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

def custom_component(model):
    # This wraps the grid in a container that takes up 100% of the available width
    with solara.Div(style={
        "min-height": "800px", 
        "height": "80vh", 
        "width": "100%",
        "display": "flex",
        "align-items": "center",
        "justify-content": "center"
    }):
        make_space_component(agent_portrayal, post_process=draw_zones)(model)


@solara.component
def waste_bar_chart_component(model):
    update_counter.get()

    fig = Figure(figsize=(6, 3.2))
    ax = fig.subplots()

    df = model.datacollector.get_model_vars_dataframe()
    if df.empty:
        counts = {
            "Vert": 0,
            "Jaune": 0,
            "Rouge": 0,
            "Depose": 0,
        }
    else:
        last_row = df.iloc[-1]
        counts = {
            "Vert": int(last_row["waste_green"]),
            "Jaune": int(last_row["waste_yellow"]),
            "Rouge": int(last_row["waste_red"]),
            "Depose": int(last_row["waste_disposed"]),
            
        }
        

    labels = list(counts.keys())
    values = list(counts.values())
    colors = ["darkgreen", "goldenrod", "darkred", "dimgray"]

    bars = ax.bar(labels, values, color=colors)
    ax.set_title("Etat des dechets")
    n_waste = model_params["N_waste"]["value"]
    ax.set_xlabel(
        f"Verif : Deposes = (Vi-Vf)/2 + (Ji-Jf)/2 + (Ri-Rf),\n"
        f"on a bien {counts['Depose']} = ({n_waste}-{counts['Vert']})/2 + "
        f"({n_waste}-{counts['Jaune']})/2 + ({n_waste}-{counts['Rouge']})"
    )
    ax.set_ylabel("Nombre")
    ax.set_ylim(0, max(values + [1]) + 1)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.05,
            str(value),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    solara.FigureMatplotlib(fig, format="png", bbox_inches="tight")


@solara.component
def robot_movement_heatmap_component(model):
    update_counter.get()

    fig = Figure(figsize=(8, 3.2))
    ax = fig.subplots()

    heatmap = model.robot_visit_counts
    max_count = max((max(row) for row in heatmap), default=0)

    im = ax.imshow(
        heatmap,
        origin="lower",
        cmap="YlOrRd",
        vmin=0,
        vmax=max(max_count, 1),
        interpolation="nearest",
        aspect="auto",
    )

    ax.set_title("Heatmap des mouvements des robots")
    ax.set_xlabel("Position X")
    ax.set_ylabel("Position Y")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Passages")

    solara.FigureMatplotlib(fig, format="png", bbox_inches="tight")


@solara.component
def communication_metrics_component(model):
    update_counter.get()

    metrics = getattr(model, "communication_metrics", {})
    communication_enabled = getattr(model, "communication_enabled", False)
    advanced_enabled = getattr(model, "advanced_communication_enabled", False)

    with solara.Card("Communication Metrics", style={"width": "100%"}):
        solara.Markdown(f"- communication: **{communication_enabled}**")
        solara.Markdown(f"- advanced_communication: **{advanced_enabled}**")

        rows = [
            ["have_waste_sent", str(metrics.get("have_waste_sent", 0))],
            ["have_waste_received", str(metrics.get("have_waste_received", 0))],
            ["need_handoff_sent", str(metrics.get("need_handoff_sent", 0))],
            ["need_handoff_received", str(metrics.get("need_handoff_received", 0))],
            ["claim_handoff_sent", str(metrics.get("claim_handoff_sent", 0))],
            ["claim_handoff_received", str(metrics.get("claim_handoff_received", 0))],
            ["commit_handoff_sent", str(metrics.get("commit_handoff_sent", 0))],
            ["commit_handoff_received", str(metrics.get("commit_handoff_received", 0))],
            ["assist_drops", str(metrics.get("assist_drops", 0))],
            ["assist_pickups", str(metrics.get("assist_pickups", 0))],
        ]
        lines = ["| Metric | Count |", "|---|---:|"]
        for name, value in rows:
            lines.append(f"| {name} | {value} |")
        solara.Markdown("\n".join(lines))

page = SolaraViz(
    initial_model,
    components=[
        custom_component,
        waste_bar_chart_component,
        robot_movement_heatmap_component,
        communication_metrics_component,
    ],
    model_params=model_params,
    name="Robot Mission"
)