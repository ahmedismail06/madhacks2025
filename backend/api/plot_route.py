# ===========================================
# plot_route.py — create an SVG plot in memory
# ===========================================

import io
import matplotlib.pyplot as plt

def plot_route_svg(path_points):
    """
    path_points: list of dicts like:
        { "x": float, "y": float, "type": "normal"|"final"|"start"|... }

    Returns: SVG string
    """
    if not path_points:
        return None

    # Extract coordinate arrays
    xs = [p["x"] for p in path_points]
    ys = [p["y"] for p in path_points]

    fig, ax = plt.subplots(figsize=(4, 4))

    # Draw path line
    ax.plot(xs, ys, "-o", markersize=3, linewidth=1.2)

    # Optional: color special points
    for p in path_points:
        if p["type"] == "start":
            ax.scatter(p["x"], p["y"], color="green", s=40, label="start")
        elif p["type"] == "end":
            ax.scatter(p["x"], p["y"], color="red", s=40, label="end")

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Computed Route Path")
    ax.grid(True, linestyle="--", linewidth=0.4)

    # Tight layout
    plt.tight_layout()

    # Save as SVG in memory
    svg_buffer = io.StringIO()
    fig.savefig(svg_buffer, format="svg")
    plt.close(fig)

    return svg_buffer.getvalue()
