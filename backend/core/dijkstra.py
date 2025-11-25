# ===========================================
# core/dijkstra.py - Dijkstra's pathfinding algorithm
# ===========================================
# Implements Dijkstra's shortest path algorithm with signal quality tracking.
# Explores nodes in order of total cost, guaranteeing optimal path.

import heapq
from core.graph import Graph


async def dijkstra(graph: Graph, start: str, goal: str, weight_func, send_event):
    """
    Find optimal fiber optic path using Dijkstra's algorithm.
    Explores uniformly in all directions without goal knowledge.
    
    Args:
        graph: Fiber network graph
        start: Starting city name  
        goal: Destination city name
        weight_func: Edge cost calculation function
        send_event: Async callback for visualization events
    
    Returns:
        List of nodes [{x, y, type}] or None if no path found
    """
    # Look up city node IDs from names
    from services.loader import city_name_to_id
    start_id = city_name_to_id.get(start)
    goal_id = city_name_to_id.get(goal)
    
    # Validate city names exist
    if start_id is None or goal_id is None:
        await send_event("no-path", {"reason": "Invalid city name"})
        return None
    
    # Initialize Dijkstra's data structures
    open_heap = []  # Priority queue: (cost, node_id, signal_quality)
    heapq.heappush(open_heap, (0, start_id, 1.0))
    distances = {start_id: 0}  # Best known cost to each node
    signal_quality = {start_id: 1.0}  # Signal quality at each node  
    came_from: dict[int, tuple[int, int]] = {}  # Backtracking map
    visited = set()  # Processed nodes

    # Send initial event
    await send_event("start", {
        "start": start_id,
        "goal": goal_id,
        "initialQuality": 1.0,
        "start_x": graph.nodes[start_id].x,
        "start_y": graph.nodes[start_id].y,
        "end_x": graph.nodes[goal_id].x,
        "end_y": graph.nodes[goal_id].y
    })

    # Main Dijkstra loop - process nodes by increasing cost
    while open_heap:
        current_dist, current_id, current_quality = heapq.heappop(open_heap)
        
        # Skip if already visited
        if current_id in visited:
            continue
        
        visited.add(current_id)
        current = graph.nodes[current_id]

        # Send node visit event
        node_name = current.name if current.name else f"{current.type}{current.id}"
        await send_event("node", {
            "nodeName": node_name,
            "status": "visited",
            "x": current.x,
            "y": current.y,
            "signalQuality": current_quality
        })

        # Goal reached - reconstruct path
        if current_id == goal_id:
            path_nodes = []
            node = current_id
            
            # Backtrack from goal to start
            while node in came_from:
                node_obj = graph.nodes[node]
                path_nodes.append({
                    "x": node_obj.x,
                    "y": node_obj.y,
                    "type": node_obj.type
                })
                prev_node, edge_id = came_from[node]
                node = prev_node
            
            # Add start node
            start_node = graph.nodes[start_id]
            path_nodes.append({
                "x": start_node.x,
                "y": start_node.y,
                "type": start_node.type
            })
            path_nodes = path_nodes[::-1]  # Reverse to start->goal order
            
            # Send final path event
            await send_event("final-path", {
                "path": path_nodes,
                "totalScore": distances[goal_id],
                "finalSignalQuality": current_quality,
                "regenerations": sum(1 for n in path_nodes if n["type"] == "regen_spot")
            })
            return path_nodes

        # Explore neighbors
        for edge_id in current.edge_ids:
            edge = graph.edges[edge_id]
            neighbor_id = edge.get_other_node(current_id)
            neighbor = graph.nodes[neighbor_id]
            
            # Skip already-visited nodes
            if neighbor_id in visited:
                continue
            
            # Calculate signal quality degradation
            # Fiber optic attenuation: decay_factor = 10^(-attenuation_dB/10)
            # Scaled by 10x to allow longer viable paths
            total_attenuation_db = (edge.degrade_rate * edge.distance) / 10
            decay_factor = 10 ** (-total_attenuation_db / 10)
            new_quality = current_quality * decay_factor
            
            # Reject if signal drops below 10% threshold
            if new_quality < 0.1:
                await send_event("edge", {
                    "edgeId": edge_id,
                    "status": "failed",
                    "reason": "signal_degraded",
                    "signalQuality": new_quality
                })
                continue
            
            # Regeneration spots reset signal to 100%
            if neighbor.type == "regen_spot":
                new_quality = 1.0
                await send_event("regeneration", {
                    "nodeId": neighbor_id,
                    "signalQuality": new_quality,
                    "x": neighbor.x,
                    "y": neighbor.y
                })
            
            # Calculate total cost via this path
            tentative_dist = distances[current_id] + weight_func(edge)

            # Update if better path found
            if neighbor_id not in distances or tentative_dist < distances[neighbor_id]:
                distances[neighbor_id] = tentative_dist
                signal_quality[neighbor_id] = new_quality
                came_from[neighbor_id] = (current_id, edge_id)
                heapq.heappush(open_heap, (tentative_dist, neighbor_id, new_quality))
                
                await send_event("edge", {
                    "edgeId": edge_id,
                    "status": "succeeded",
                    "from": current_id,
                    "to": neighbor_id,
                    "newCost": tentative_dist,
                    "signalQuality": new_quality,
                    "degradation": edge.degrade_rate
                })
            else:
                await send_event("edge", {
                    "edgeId": edge_id,
                    "status": "failed",
                    "reason": "not_better"
                })

    # No path found after exploring all reachable nodes
    await send_event("no-path", {"reason": "No route found"})
    return None