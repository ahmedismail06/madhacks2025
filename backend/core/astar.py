# ===========================================
# core/astar.py — A* algorithm with event callbacks
# ===========================================

import heapq
import math
from core.graph import Graph


def heuristic(graph: Graph, node_id: int, goal_id: int) -> float:
    """
    Euclidean distance heuristic based on node coordinates.
    This is admissible since it never overestimates the actual distance.
    """
    node = graph.nodes[node_id]
    goal = graph.nodes[goal_id]
    dx = node.x - goal.x
    dy = node.y - goal.y
    return math.sqrt(dx * dx + dy * dy)


async def astar(graph: Graph, start: str, goal: str, weight_func, send_event):
    
    # use global city_name_to_id mapping to find IDs
    from services.loader import city_name_to_id
    start_id = city_name_to_id.get(start)
    goal_id = city_name_to_id.get(goal)
    
    open_heap = [] # min-heap of (f_score, node_id, signal_quality)
    g_score = {start_id: 0}  # cost from start to node
    f_score = {start_id: heuristic(graph, start_id, goal_id)}  # g_score + heuristic
    heapq.heappush(open_heap, (f_score[start_id], start_id, 1.0))

    signal_quality = {start_id: 1.0}  # track signal quality at each node
    came_from: dict[int, tuple[int, int]] = {}  # node_id -> (previous_node_id, edge_id)
    visited = set()

    await send_event("start", {
        "start": start_id, 
        "goal": goal_id, 
        "initialQuality": 1.0, 
        "start_x": graph.nodes[start_id].x, 
        "start_y": graph.nodes[start_id].y, 
        "end_x": graph.nodes[goal_id].x, 
        "end_y": graph.nodes[goal_id].y
    })

    while open_heap:
        current_f, current_id, current_quality = heapq.heappop(open_heap)
        
        # skip if already visited
        if current_id in visited:
            continue
        
        visited.add(current_id)
        current = graph.nodes[current_id]

        # send visited event with signal quality
        # if it's a city node, include the name, if not, just use type + id
        node_name = current.name if current.name else f"{current.type}{current.id}"
        await send_event("node", {
            "nodeName": node_name, 
            "status": "visited",
            "x": current.x,
            "y": current.y,
            "signalQuality": current_quality
        })

        # check if we reached the goal
        if current_id == goal_id:
            # reconstruct path
            path = []
            edge_path = []
            node = current_id
            
            while node in came_from:
                prev_node, edge_id = came_from[node]
                path.append(node)
                edge_path.append(edge_id)
                node = prev_node
            
            path.append(start_id)
            path = path[::-1]
            edge_path = edge_path[::-1]
            
            await send_event("final-path", {
                "path": path,
                "edges": edge_path,
                "totalScore": g_score[goal_id],
                "finalSignalQuality": current_quality,
                "regenerations": sum(1 for nid in path if graph.nodes[nid].type == "regen")
            })
            return path

        # explore neighbors through edges
        for edge_id in current.edge_ids:
            edge = graph.edges[edge_id]
            neighbor_id = edge.get_other_node(current_id)
            neighbor = graph.nodes[neighbor_id]
            
            # skip if neighbor already visited
            if neighbor_id in visited:
                continue
            
            # Calculate signal quality after traversing this edge
            # Use realistic fiber optic attenuation model:
            # attenuation_db_per_km = degrade_rate (treat as dB/km)
            # power_ratio_per_km = 10^(-attenuation/10)
            # decay_factor = (power_ratio_per_km)^distance
            power_ratio_per_km = 10 ** (-edge.degrade_rate / 10)
            decay_factor = power_ratio_per_km ** edge.distance
            new_quality = current_quality * decay_factor
            
            # Check if signal drops below threshold (0.1 = 10%)
            if new_quality < 0.1:
                await send_event("edge", {
                    "edgeId": edge_id,
                    "status": "failed",
                    "reason": "signal_degraded",
                    "signalQuality": new_quality
                })
                continue
            
            # If neighbor is a regen node, reset signal quality to 1.0
            if neighbor.type == "regen":
                new_quality = 1.0
                await send_event("regeneration", {
                    "nodeId": neighbor_id,
                    "signalQuality": new_quality,
                    "x": neighbor.x,
                    "y": neighbor.y
                })
            
            tentative_g_score = g_score[current_id] + weight_func(edge)

            # If this is a better path to the neighbor
            if neighbor_id not in g_score or tentative_g_score < g_score[neighbor_id]:
                g_score[neighbor_id] = tentative_g_score
                f_score[neighbor_id] = tentative_g_score + heuristic(graph, neighbor_id, goal_id)
                signal_quality[neighbor_id] = new_quality
                came_from[neighbor_id] = (current_id, edge_id)
                heapq.heappush(open_heap, (f_score[neighbor_id], neighbor_id, new_quality))
                
                await send_event("edge", {
                    "edgeId": edge_id,
                    "status": "succeeded",
                    "from": current_id,
                    "to": neighbor_id,
                    "newCost": tentative_g_score,
                    "signalQuality": new_quality,
                    "degradation": edge.degrade_rate
                })
            else:
                await send_event("edge", {"edgeId": edge_id, "status": "failed", "reason": "not_better"})

    await send_event("fail", {"reason": "No route found"})
    return None
