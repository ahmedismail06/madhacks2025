# ===========================================
# services/jobs.py — manage A* tasks & SSE
# ===========================================

# Each route request gets a job_id.
# A background task runs A* and pushes events into an asyncio.Queue.
# SSE endpoint streams events from that queue.

import uuid
import asyncio

job_queues: dict[str, asyncio.Queue] = {}  # job_id -> Queue


def create_job():
    job_id = str(uuid.uuid4())
    job_queues[job_id] = asyncio.Queue()
    return job_id


def get_queue(job_id: str) -> asyncio.Queue:
    return job_queues[job_id]


# Wrapper passed into Dijkstra to send events
def make_event_sender(job_id: str):
    queue = job_queues[job_id]
    
    async def send_event(event_type: str, payload: dict):
        await queue.put({"event": event_type, "data": payload})
    
    return send_event
