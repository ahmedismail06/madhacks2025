# ===========================================
# main.py — Flask application entry point
# ===========================================
# Initializes the Flask web server and registers all API blueprints.
# Provides health check endpoint and starts the development server.

from flask import Flask, jsonify
from api.route import route_bp
from api.edges import edges_bp
from api.result import result_bp

app = Flask(__name__)

# Register API blueprints for pathfinding endpoints
# - route_bp: Initiates pathfinding jobs (POST /api/route)
# - edges_bp: Returns all tried edges in JSON format (GET /api/route/edges)
# - result_bp: Returns final path results in JSON format (GET /api/route/result)
app.register_blueprint(route_bp, url_prefix="/api")
app.register_blueprint(edges_bp, url_prefix="/api")
app.register_blueprint(result_bp, url_prefix="/api")


@app.route("/")
def root():
    """Health check endpoint to verify API is running."""
    response = jsonify({"message": "Fiber Route API", "status": "running"})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


if __name__ == "__main__":
    # Start Flask development server
    # - host="0.0.0.0": Accept connections from any network interface
    # - port=8000: Listen on port 8000
    # - debug=True: Enable auto-reload and detailed error pages
    # - threaded=True: Handle concurrent requests in separate threads
    app.run(host="0.0.0.0", port=8000, debug=True, threaded=True)
