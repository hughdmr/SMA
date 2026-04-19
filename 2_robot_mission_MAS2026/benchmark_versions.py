import argparse
import contextlib
import io
import os
from statistics import mean

import matplotlib.pyplot as plt

from model import RobotMission


SCENARIOS = [
    ("no_communication", False, False),
    ("basic_communication", True, False),
    ("advanced_communication", True, True),
]


def run_single_scenario(name, communication_enabled, advanced_enabled, runs, max_steps, n_agents, n_waste, z, height):
    completion_steps = []
    failures = 0

    for seed in range(runs):
        # Silence verbose agent logs to keep benchmark output readable.
        with contextlib.redirect_stdout(io.StringIO()):
            model = RobotMission(
                N_agents=n_agents,
                N_waste=n_waste,
                z=z,
                height=height,
                want_no_waste_at_end=True,
                communication_enabled=communication_enabled,
                advanced_communication_enabled=advanced_enabled,
                seed=seed,
            )
            steps = model.run_until_complete(max_steps=max_steps)

        if steps is None:
            failures += 1
        else:
            completion_steps.append(steps)

    success_count = len(completion_steps)
    success_rate = success_count / runs if runs else 0.0
    avg_steps = mean(completion_steps) if completion_steps else None

    return {
        "name": name,
        "success_count": success_count,
        "failure_count": failures,
        "success_rate": success_rate,
        "avg_steps": avg_steps,
        "steps": completion_steps,
    }


def format_result(result):
    avg = "N/A" if result["avg_steps"] is None else f"{result['avg_steps']:.2f}"
    success_pct = f"{result['success_rate'] * 100:.1f}%"
    return (
        f"- {result['name']}: avg_steps={avg}, "
        f"success={result['success_count']}/{result['success_count'] + result['failure_count']} ({success_pct})"
    )


def generate_plots(results, output_dir, runs, max_steps):
    os.makedirs(output_dir, exist_ok=True)

    scenario_names = [r["name"] for r in results]
    avg_values = [r["avg_steps"] if r["avg_steps"] is not None else 0 for r in results]
    has_avg = [r["avg_steps"] is not None for r in results]
    success_rates = [r["success_rate"] * 100 for r in results]

    # Bar chart: average completion time.
    fig1, ax1 = plt.subplots(figsize=(8, 4.5))
    bars = ax1.bar(scenario_names, avg_values, color=["#7f8c8d", "#3498db", "#2ecc71"])
    for idx, bar in enumerate(bars):
        label = "N/A" if not has_avg[idx] else f"{avg_values[idx]:.1f}"
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(1, max(avg_values + [1]) * 0.01),
            label,
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax1.set_title(f"Average Steps to Complete (runs={runs}, max_steps={max_steps})")
    ax1.set_ylabel("Average steps (lower is better)")
    ax1.set_ylim(0, max(avg_values + [1]) * 1.2)
    fig1.tight_layout()
    fig1.savefig(os.path.join(output_dir, "benchmark_avg_steps.png"), dpi=160)
    plt.close(fig1)

    # Bar chart: success rates.
    fig2, ax2 = plt.subplots(figsize=(8, 4.5))
    bars2 = ax2.bar(scenario_names, success_rates, color=["#95a5a6", "#5dade2", "#58d68d"])
    for idx, bar in enumerate(bars2):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{success_rates[idx]:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax2.set_title("Completion Success Rate")
    ax2.set_ylabel("Success rate (%)")
    ax2.set_ylim(0, 110)
    fig2.tight_layout()
    fig2.savefig(os.path.join(output_dir, "benchmark_success_rate.png"), dpi=160)
    plt.close(fig2)

    # Box plot: distribution of completion steps for successful runs.
    successful_data = [r["steps"] if r["steps"] else [max_steps] for r in results]
    fig3, ax3 = plt.subplots(figsize=(8, 4.5))
    ax3.boxplot(successful_data, tick_labels=scenario_names, showmeans=True)
    ax3.set_title("Distribution of Completion Steps")
    ax3.set_ylabel("Steps")
    fig3.tight_layout()
    fig3.savefig(os.path.join(output_dir, "benchmark_steps_distribution.png"), dpi=160)
    plt.close(fig3)


def main():
    parser = argparse.ArgumentParser(description="Compare average disposal completion times across communication versions.")
    parser.add_argument("--runs", type=int, default=20, help="Number of seeds per scenario.")
    parser.add_argument("--max-steps", type=int, default=2000, help="Maximum steps allowed for one run.")
    parser.add_argument("--agents", type=int, default=10, help="Number of agents per color.")
    parser.add_argument("--waste", type=int, default=30, help="Base waste amount per zone before optional rounding.")
    parser.add_argument("--zone-width", type=int, default=15, help="Width of one zone.")
    parser.add_argument("--height", type=int, default=15, help="Grid height.")
    parser.add_argument("--output-dir", type=str, default="benchmark_outputs", help="Directory where benchmark plots are saved.")
    parser.add_argument("--no-plots", action="store_true", help="Disable plot generation.")
    args = parser.parse_args()

    results = []
    for name, comm, adv in SCENARIOS:
        results.append(
            run_single_scenario(
                name=name,
                communication_enabled=comm,
                advanced_enabled=adv,
                runs=args.runs,
                max_steps=args.max_steps,
                n_agents=args.agents,
                n_waste=args.waste,
                z=args.zone_width,
                height=args.height,
            )
        )

    print("Benchmark results (lower avg_steps is better):")
    for result in results:
        print(format_result(result))

    if not args.no_plots:
        generate_plots(results, args.output_dir, args.runs, args.max_steps)
        print(f"Plots saved in: {args.output_dir}")


if __name__ == "__main__":
    main()
