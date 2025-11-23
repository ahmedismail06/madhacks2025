# =====================================
# in your Flask app file
# =====================================

from flask import Response, app
from  plot_route  import plot_route_svg  
import requests  # or however you access /route/result internally


@app.route("/plot_route.svg")
def plot_route_svg_route():

    # Get final route result (you may call the internal function instead)
    route_json = requests.get("http://localhost:8000/route/result").json()

    if route_json.get("event") != "final-path":
        return Response("No path to plot", status=400)

    path_points = route_json["path"]

    svg_data = plot_route_svg(path_points)

    return Response(svg_data, headers={"Content-Type": "image/svg+xml"})
