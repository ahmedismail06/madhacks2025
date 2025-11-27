# ===========================================
# core/dijkstra.py - Dijkstra's pathfinding algorithm
# ===========================================
# Implements Dijkstra's shortest path algorithm with signal quality tracking.
# Explores nodes in order of total cost, guaranteeing optimal path.

import heapq
from core.graph import Graph


def dijkstra(graph: Graph, start: str, goal: str, weight_func):
    """
    Find optimal fiber optic path using Dijkstra's algorithm.
    Explores uniformly in all directions without goal knowledge.
    
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
    
    # Initialize Dijkstra's data structures
    open_heap = []  # Priority queue: (cost, node_id, signal_quality)
    heapq.heappush(open_heap, (0, start_id, 1.0))
    distances = {start_id: 0}  # Best known cost to each node
    signal_quality = {start_id: 1.0}  # Signal quality at each node  
    came_from: dict[int, tuple[int, int]] = {}  # Backtracking map
    visited = set()  # Processed nodes

    # Main Dijkstra loop - process nodes by increasing cost
    while open_heap:
        current_dist, current_id, current_quality = heapq.heappop(open_heap)
        
        # Skip if already visited
        if current_id in visited:
            continue
        
        visited.add(current_id)
        current = graph.nodes[current_id]

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
            
            # Calculate total cost via this path
            tentative_dist = distances[current_id] + weight_func(edge)

            # Update if better path found
            if neighbor_id not in distances or tentative_dist < distances[neighbor_id]:
                distances[neighbor_id] = tentative_dist
                signal_quality[neighbor_id] = new_quality
                came_from[neighbor_id] = (current_id, edge_id)
                heapq.heappush(open_heap, (tentative_dist, neighbor_id, new_quality))

    # No path found after exploring all reachable nodes
    return None, tried_edges