# ===========================================
# core/search.py — Dijkstra's algorithm with event callbacks
# ===========================================

import heapq
from core.graph import Graph


# send_event(event_name, payload) is a function passed from caller
async def dijkstra(graph: Graph, start: str, goal: str, weight_func, send_event):
    
    # use global city_name_to_id mapping to find IDs
    from services.loader import city_name_to_id
    start_id = city_name_to_id.get(start)
    goal_id = city_name_to_id.get(goal)
    
    print(f"[DIJKSTRA] Starting search from '{start}' (ID: {start_id}) to '{goal}' (ID: {goal_id})")
    
    if start_id is None:
        print(f"[DIJKSTRA ERROR] Start city '{start}' not found in city_name_to_id mapping")
        return None
    if goal_id is None:
        print(f"[DIJKSTRA ERROR] Goal city '{goal}' not found in city_name_to_id mapping")
        return None
    
    open_heap = [] # min-heap of (cost, node_id, signal_quality)
    heapq.heappush(open_heap, (0, start_id, 1.0)) 

    distances = {start_id: 0} # shortest known distance to each node
    signal_quality = {start_id: 1.0}  # track signal quality at each node
    came_from: dict[int, tuple[int, int]] = {}  # node_id -> (previous_node_id, edge_id)
    visited = set()
    
    print(f"[DIJKSTRA] Start node edges: {len(graph.nodes[start_id].edge_ids)}")
    print(f"[DIJKSTRA] Goal node edges: {len(graph.nodes[goal_id].edge_ids)}")

    await send_event("start", 
                     {"start": start_id, 
                      "goal": goal_id, 
                      "initialQuality": 1.0, 
                      "start_x": graph.nodes[start_id].x, 
                      "start_y": graph.nodes[start_id].y, 
                      "end_x": graph.nodes[goal_id].x, 
                      "end_y": graph.nodes[goal_id].y}) # send start event
    
    nodes_explored = 0

    while open_heap:
        nodes_explored += 1
        current_dist, current_id, current_quality = heapq.heappop(open_heap)
        
        # skip if already visited
        if current_id in visited:
            continue
        
        visited.add(current_id)
        current = graph.nodes[current_id]

        # send visited event with signal quality
        # if it's a city node, include the name, if not, just use type + id
        node_name = current.name if current.name else f"{current.type}{current.id}"
        
        # Debug: log when we visit different node types
        if current.type == "regen_spot":
            print(f"[DIJKSTRA] Visiting regen_spot node {current_id} with signal quality {current_quality}")
        
        await send_event("node", {
            "nodeName": node_name, 
            "status": "visited",
            "x": current.x,
            "y": current.y,
            "signalQuality": current_quality
        })

        # check if we reached the goal
        if current_id == goal_id:
            print(f"[DIJKSTRA SUCCESS] Found path! Explored {nodes_explored} nodes")
            # reconstruct path
            path = []
            edge_path = []
            node = current_id
            
            while node in came_from:
                prev_node, edge_id = came_from[node] # get previous node and edge
                path.append(node)
                edge_path.append(edge_id)
                node = prev_node # move to previous node
            
            path.append(start_id) # add start node
            path = path[::-1] # reverse path to start->goal
            edge_path = edge_path[::-1] # reverse edge path to start->goal
            
            await send_event("final-path", {
                "path": path,
                "edges": edge_path,
                "totalScore": distances[goal_id],
                "finalSignalQuality": current_quality,
                "regenerations": sum(1 for nid in path if graph.nodes[nid].type == "regen_spot")  # number of regeneration nodes in path
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
                print(f"[DIJKSTRA] Signal degraded below threshold at edge {edge_id} (quality: {new_quality:.4f})")
                await send_event("edge", {
                    "edgeId": edge_id,
                    "status": "failed",
                    "reason": "signal_degraded",
                    "signalQuality": new_quality
                })
                continue
            
            # If neighbor is a regen node, reset signal quality to 1.0
            if neighbor.type == "regen_spot":
                print(f"[DIJKSTRA] Signal regenerated at node {neighbor_id}")
                new_quality = 1.0
                await send_event("regeneration", {
                    "nodeId": neighbor_id,
                    "signalQuality": new_quality,
                    "x": neighbor.x,
                    "y": neighbor.y
                })
            
            tentative_dist = distances[current_id] + weight_func(edge)

            # If this is a better path to the neighbor
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
                await send_event("edge", 
                                 {"edgeId": edge_id, 
                                  "status": "failed", 
                                  "reason": "not_better"})

    print(f"[DIJKSTRA FAIL] No route found after exploring {nodes_explored} nodes")
    print(f"[DIJKSTRA FAIL] Visited {len(visited)} unique nodes")
    print(f"[DIJKSTRA FAIL] Final distances dict size: {len(distances)}")
    await send_event("fail", {"reason": "No route found"})
    return None