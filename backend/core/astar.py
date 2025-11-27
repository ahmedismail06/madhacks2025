# ===========================================
# core/astar.py - A* pathfinding algorithm
# ===========================================
# Implements A* algorithm with signal quality tracking.
# Uses heuristic to efficiently search toward goal.

import heapq
import math
from core.graph import Graph


def heuristic(graph: Graph, node_id: int, goal_id: int) -> float:
    """
    Calculate straight-line distance between two nodes.
    
    Uses Euclidean distance as an admissible heuristic (never overestimates
    actual path cost), ensuring A* finds optimal paths.
    
    Args:
        graph: The network graph
        node_id: Current node ID
        goal_id: Goal node ID
        
    Returns:
        Straight-line distance between nodes
    """
    node = graph.nodes[node_id]
    goal = graph.nodes[goal_id]
    dx = node.x - goal.x
    dy = node.y - goal.y
    return math.sqrt(dx * dx + dy * dy)


def astar(graph: Graph, start: str, goal: str, weight_func):
    """
    Find optimal fiber optic path using A* algorithm.
    Prioritizes nodes closer to goal for faster search.
    
    Args:
        graph: Fiber network graph
        start: Starting city name
        goal: Destination city name
        weight_func: Edge cost calculation function
    
    Returns:
        tuple: (path_nodes, tried_edges)
            - path_nodes: List of nodes [{x, y, type}] or None if no path found
            - tried_edges: List of all edges explored [{start_x, start_y, end_x, end_y}]
    """
    # Look up city node IDs from names
    from services.loader import city_name_to_id
    start_id = city_name_to_id.get(start)
    goal_id = city_name_to_id.get(goal)
    
    # Validate city names exist
    if start_id is None or goal_id is None:
        return None, []
    
    # Track all edges tried during pathfinding
    tried_edges = []
    
    # Initialize A* data structures
    open_heap = []  # Priority queue: (f_score, node_id, signal_quality)
    g_score = {start_id: 0}  # Actual cost from start
    f_score = {start_id: heuristic(graph, start_id, goal_id)}  # g + heuristic
    heapq.heappush(open_heap, (f_score[start_id], start_id, 1.0))
    signal_quality = {start_id: 1.0}  # Signal quality at each node
    came_from: dict[int, tuple[int, int]] = {}  # Backtracking map
    visited = set()  # Processed nodes

    # Main A* loop - process nodes by f_score (cost + heuristic)
    while open_heap:
        current_f, current_id, current_quality = heapq.heappop(open_heap)
        
        # Skip if already visited
        if current_id in visited:
            continue
        
        visited.add(current_id)
        current = graph.nodes[current_id]

        # Goal reached - reconstruct path
        if current_id == goal_id:
            # reconstruct path with node details
            path_nodes = []
            node = current_id
            
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
            path_nodes = path_nodes[::-1] # reverse path to start->goal
            
            return path_nodes, tried_edges

        # Explore neighbors
        for edge_id in current.edge_ids:
            edge = graph.edges[edge_id]
            neighbor_id = edge.get_other_node(current_id)
            neighbor = graph.nodes[neighbor_id]
            
            # Track this edge as tried
            tried_edges.append({
                "start_x": edge.start_x,
                "start_y": edge.start_y,
                "end_x": edge.end_x,
                "end_y": edge.end_y
            })
            
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
                continue
            
            # Regeneration spots reset signal to 100%
            if neighbor.type == "regen_spot":
                new_quality = 1.0
            
            # Calculate tentative g_score
            tentative_g_score = g_score[current_id] + weight_func(edge)

            # Update if better path found
            if neighbor_id not in g_score or tentative_g_score < g_score[neighbor_id]:
                g_score[neighbor_id] = tentative_g_score
                f_score[neighbor_id] = tentative_g_score + heuristic(graph, neighbor_id, goal_id)
                signal_quality[neighbor_id] = new_quality
                came_from[neighbor_id] = (current_id, edge_id)
                heapq.heappush(open_heap, (f_score[neighbor_id], neighbor_id, new_quality))

    # No path found after exploring all reachable nodes
    return None, tried_edges
