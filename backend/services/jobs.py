# ===========================================
# services/jobs.py - Job management for pathfinding
# ===========================================
# Manages job storage for pathfinding algorithms.
# Each job stores the final result (path and tried edges).

import uuid

# Global storage for job results
job_results: dict[str, dict] = {}  # job_id -> {path, tried_edges, status}
last_job_id: str = None  # Track most recent job for easy access


def create_job():
    """
    Create a new pathfinding job with unique ID.
    
    Returns:
        str: Unique job ID (UUID)
    """
    global last_job_id
    job_id = str(uuid.uuid4())
    job_results[job_id] = {"status": "running", "path": None, "tried_edges": []}
    last_job_id = job_id
    return job_id


def store_result(job_id: str, path, tried_edges):
    """
    Store pathfinding result for a job.
    
    Args:
        job_id: Job identifier
        path: List of path nodes or None if no path found
        tried_edges: List of all edges explored during pathfinding
    """
    if job_id in job_results:
        job_results[job_id] = {
            "status": "completed",
            "path": path,
            "tried_edges": tried_edges
        }


def get_result(job_id: str) -> dict:
    """
    Get result for a specific job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        dict with status, path, and tried_edges, or None if job doesn't exist
    """
    return job_results.get(job_id)


def get_last_job_id() -> str:
    """
    Get ID of most recently created job.
    
    Returns:
        str: Last job ID or None if no jobs exist
    """
    return last_job_id
