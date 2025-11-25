# ===========================================
# api/stream.py - Server-Sent Events streaming
# ===========================================
# Streams pathfinding events in real-time using SSE protocol.
# Allows frontend to visualize algorithm progress.

import json
import asyncio
from flask import Blueprint, request, Response
from services.jobs import get_queue

stream_bp = Blueprint('stream', __name__)


@stream_bp.route("/route/stream", methods=["GET"])
def stream_route():
    """
    Stream pathfinding events for a specific job.
    
    Query Parameters:
        id: Job ID returned from /route endpoint
    
    Returns:
        Server-Sent Events stream with algorithm progress
    """
    job_id = request.args.get('id')
    queue = get_queue(job_id)
    
    if queue is None:
        return json.dumps({"error": "Job not found"}), 404

    def event_generator():
        """Generate SSE stream from job queue."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            while True:
                # Wait for next event from pathfinding algorithm
                event = loop.run_until_complete(asyncio.wait_for(queue.get(), timeout=30.0))
                event_type = event['event']
                event_data = json.dumps(event['data'])
                
                # Format as SSE
                yield f"event: {event_type}\ndata: {event_data}\n\n"
                
        except asyncio.TimeoutError:
            pass  # Stream timeout, close gracefully
        except Exception as e:
            pass  # Handle errors gracefully
        finally:
            loop.close()

    response = Response(event_generator(), mimetype="text/event-stream")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
