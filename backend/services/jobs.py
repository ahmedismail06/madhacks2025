# ===========================================
# services/jobs.py - Job management for pathfinding
# ===========================================
# Manages async job queues and event streaming for pathfinding algorithms.
# Each job has a unique ID and an event queue for communication.

import uuid
import asyncio

# Global storage for job queues and state
job_queues: dict[str, asyncio.Queue] = {}  # job_id -> event queue
job_buffers: dict[str, list] = {}  # job_id -> buffered events
last_job_id: str = None  # Track most recent job for easy access


def create_job():
    """
    Create a new pathfinding job with unique ID.
    
    Returns:
        str: Unique job ID (UUID)
    """
    global last_job_id
    job_id = str(uuid.uuid4())
    job_queues[job_id] = asyncio.Queue()
    job_buffers[job_id] = []
    last_job_id = job_id
    return job_id


def get_queue(job_id: str) -> asyncio.Queue:
    """
    Get event queue for a specific job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        asyncio.Queue or None if job doesn't exist
    """
    return job_queues.get(job_id)


def get_last_job_id() -> str:
    """
    Get ID of most recently created job.
    
    Returns:
        str: Last job ID or None if no jobs exist
    """
    return last_job_id


def make_event_sender(job_id: str):
    """
    Create event sender function for a specific job.
    
    Batches events for efficiency - sends in groups of 10 or when
    final event is reached.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Async function that sends events to job queue
    """
    queue = job_queues[job_id]
    buffer = job_buffers[job_id]
    
    async def send_event(event_type: str, payload: dict):
        """Send event to job queue, batching for efficiency."""
        # Buffer events
        buffer.append({"event": event_type, "data": payload})
        
        # Send batch when threshold reached or computation completes
        is_final = event_type in ["final-path", "no-path", "fail"]
        if len(buffer) >= 10 or is_final:
            await queue.put({"event": "batch", "data": buffer.copy()})
            buffer.clear()
    
    return send_event
