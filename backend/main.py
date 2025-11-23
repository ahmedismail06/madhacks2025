# ===========================================
# main.py — Flask bootstrap
# ===========================================

from flask import Flask, jsonify
from api.route import route_bp
from api.stream import stream_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(route_bp, url_prefix="/api")
app.register_blueprint(stream_bp, url_prefix="/api")


@app.route("/")
def root():
    return jsonify({"message": "Fiber Route API", "status": "running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, threaded=True)
