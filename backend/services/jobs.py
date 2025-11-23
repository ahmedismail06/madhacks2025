# ===========================================
# services/jobs.py — manage A* tasks & SSE
# ===========================================

# Each route request gets a job_id.
# A background task runs A* and pushes events into an asyncio.Queue.
# SSE endpoint streams events from that queue.

import uuid
import asyncio

job_queues: dict[str, asyncio.Queue] = {}  # job_id -> Queue
job_buffers: dict[str, list] = {}  # job_id -> list of buffered events


def create_job():
    job_id = str(uuid.uuid4())
    job_queues[job_id] = asyncio.Queue()
    job_buffers[job_id] = []
    return job_id


def get_queue(job_id: str) -> asyncio.Queue:
    return job_queues[job_id]


# Wrapper passed into Dijkstra to send events in batches
def make_event_sender(job_id: str):
    queue = job_queues[job_id]
    buffer = job_buffers[job_id]
    
    async def send_event(event_type: str, payload: dict):
        # Add event to buffer
        buffer.append({"event": event_type, "data": payload})
        
        # Send batch when we have 10 events, or if it's a final event
        if len(buffer) >= 10 or event_type in ["final-path", "no-path"]:
            await queue.put({"event": "batch", "data": buffer.copy()})
            buffer.clear()
    
    return send_event
